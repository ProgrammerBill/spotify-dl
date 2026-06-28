"""Resolve free-text song queries into downloadable song dicts.

Two backends are supported and chosen automatically by the caller:

* Spotify search (when Spotify API credentials are available) - yields full
  metadata (album, cover, year) by reusing the same song dict shape produced by
  ``spotify_dl.spotify.fetch_tracks``.
* YouTube Music search (fallback when no credentials) - yields a leaner song
  dict built straight from the YouTube Music search results.

Both backends funnel through :func:`resolve_songs`, which presents the
candidates and lets the user pick one interactively.
"""

from pathlib import Path

import ytmusicapi

from spotify_dl.scaffold import log, console
from spotify_dl.spotify import fetch_tracks
from spotify_dl.utils import sanitize


def search_spotify_tracks(sp, query, limit=5):
    """
    Search Spotify for tracks matching the query.
    :param sp: Spotify client
    :param query: free text query, e.g. "Bohemian Rhapsody Queen"
    :param limit: maximum number of candidates to return
    :return list of raw Spotify track objects
    """
    results = sp.search(q=query, type="track", limit=limit)
    return results.get("tracks", {}).get("items", [])


def search_youtube_tracks(query, limit=5):
    """
    Search YouTube Music for songs matching the query, falling back to the
    broader "videos" filter when no songs are found.
    :param query: free text query
    :param limit: maximum number of candidates to return
    :return list of YouTube Music search result dicts
    """
    with ytmusicapi.YTMusic() as ym:
        results = ym.search(query, filter="songs")
        if not results:
            log.warning("No song results for '%s', trying videos.", query)
            results = ym.search(query, filter="videos")
    return results[:limit]


def format_spotify_candidate(track):
    """Build a human-readable one-line description of a Spotify track."""
    artists = ", ".join(a["name"] for a in track.get("artists", []))
    album = track.get("album", {})
    album_name = album.get("name", "")
    release_date = album.get("release_date", "") or ""
    year = release_date[:4]
    suffix = f" ({year})" if year else ""
    return f"{track.get('name')} — {artists} — {album_name}{suffix}"


def format_youtube_candidate(result):
    """Build a human-readable one-line description of a YouTube Music result."""
    artists = ", ".join(
        a["name"] for a in result.get("artists", []) if a.get("name")
    )
    album = result.get("album")
    album_name = album.get("name") if isinstance(album, dict) else (album or "")
    parts = [result.get("title"), artists]
    if album_name:
        parts.append(album_name)
    return " — ".join(p for p in parts if p)


def build_song_dict_from_spotify(track):
    """Convert a Spotify track object into the download pipeline's song dict."""
    album = track.get("album", {})
    artists = ", ".join(a["name"] for a in track.get("artists", []))
    images = album.get("images", [])
    cover = images[0]["url"] if images else None
    release_date = album.get("release_date", "") or ""
    return {
        "name": track.get("name"),
        "artist": artists,
        "album": album.get("name", ""),
        "year": release_date[:4],
        "num_tracks": album.get("total_tracks", 1),
        "num": track.get("track_number", 1),
        "playlist_num": 1,
        "cover": cover,
        "genre": "",
        "spotify_id": track.get("id"),
        "track_url": None,
        "tempo": None,
    }


def build_song_dict_from_youtube(result):
    """Convert a YouTube Music search result into the song dict."""
    artists = ", ".join(
        a["name"] for a in result.get("artists", []) if a.get("name")
    )
    album = result.get("album")
    album_name = album.get("name") if isinstance(album, dict) else (album or "")
    thumbnails = result.get("thumbnails", [])
    cover = thumbnails[-1]["url"] if thumbnails else None
    return {
        "name": result.get("title"),
        "artist": artists,
        "album": album_name,
        "year": "",
        "num_tracks": 1,
        "num": 1,
        "playlist_num": 1,
        "cover": cover,
        "genre": "",
        "spotify_id": None,
        "track_url": None,
        "tempo": None,
    }


def prompt_user_selection(displays, query):
    """
    Show the numbered candidates and ask the user to pick one.
    :param displays: list of human-readable candidate strings
    :param query: the original query (for display)
    :return zero-based index of the chosen candidate, or None to skip
    """
    console.print(f"\nResults for [bold]{query}[/bold]:")
    for idx, item in enumerate(displays, start=1):
        console.print(f"  [cyan]{idx}[/cyan]. {item}")

    while True:
        choice = input(f"Select 1-{len(displays)} (Enter for 1, 's' to skip): ").strip().lower()
        if choice == "":
            return 0
        if choice == "s":
            return None
        if choice.isdigit():
            number = int(choice)
            if 1 <= number <= len(displays):
                return number - 1
        console.print("[red]Invalid selection, try again.[/red]")


def resolve_songs(queries, sp=None, limit=5):
    """
    Resolve free-text queries into song dicts via interactive selection.

    Uses Spotify search when ``sp`` is provided, otherwise falls back to
    YouTube Music search.
    :param queries: list of free text queries
    :param sp: Spotify client, or None to use the YouTube Music backend
    :param limit: maximum number of candidates shown per query
    :return list of song dicts ready for the download pipeline
    """
    songs = []
    # Once Spotify search errors out (e.g. a 403 from an app whose owner lacks
    # the required subscription), stop trying it and use YouTube Music for the
    # rest of the queries too.
    spotify_failed = False
    for query in queries:
        candidates, displays, builder = [], [], None
        if sp is not None and not spotify_failed:
            try:
                candidates = search_spotify_tracks(sp, query, limit)
                displays = [format_spotify_candidate(c) for c in candidates]
                builder = build_song_dict_from_spotify
            except Exception as exc:  # skipcq: PYL-W0703
                log.warning(
                    "Spotify search failed (%s); falling back to YouTube Music.",
                    exc,
                )
                spotify_failed = True
                candidates = []

        if builder is None:
            candidates = search_youtube_tracks(query, limit)
            displays = [format_youtube_candidate(c) for c in candidates]
            builder = build_song_dict_from_youtube

        if not candidates:
            log.error("No results found for '%s', skipping.", query)
            continue

        index = prompt_user_selection(displays, query)
        if index is None:
            log.info("Skipped '%s'.", query)
            continue
        songs.append(builder(candidates[index]))
    return songs


def search_spotify_albums(sp, query, limit=5):
    """
    Search Spotify for albums matching the query.
    :return list of raw Spotify album objects
    """
    results = sp.search(q=query, type="album", limit=limit)
    return results.get("albums", {}).get("items", [])


def search_youtube_albums(query, limit=5):
    """
    Search YouTube Music for albums matching the query.
    :return list of YouTube Music album search result dicts
    """
    with ytmusicapi.YTMusic() as ym:
        results = ym.search(query, filter="albums")
    return results[:limit]


def format_spotify_album(album):
    """Build a human-readable one-line description of a Spotify album."""
    artists = ", ".join(a["name"] for a in album.get("artists", []))
    release_date = album.get("release_date", "") or ""
    year = release_date[:4]
    total = album.get("total_tracks", "?")
    suffix = f" — {year}" if year else ""
    return f"{album.get('name')} — {artists}{suffix} — {total} tracks"


def format_youtube_album(album):
    """Build a human-readable one-line description of a YouTube Music album."""
    artists = ", ".join(
        a["name"] for a in album.get("artists", []) if a.get("name")
    )
    year = album.get("year") or ""
    suffix = f" — {year}" if year else ""
    return f"{album.get('title')} — {artists}{suffix}"


def _resolve_one_spotify_album(sp, query, output_dir, limit):
    """Search, select and expand a single album via Spotify.
    :return a download unit ({save_path, songs}) or None to skip
    """
    albums = search_spotify_albums(sp, query, limit)
    if not albums:
        log.error("No album results found for '%s', skipping.", query)
        return None
    displays = [format_spotify_album(a) for a in albums]
    index = prompt_user_selection(displays, query)
    if index is None:
        log.info("Skipped '%s'.", query)
        return None
    album = albums[index]
    name = sanitize(album.get("name", "album"))
    songs = fetch_tracks(sp, "album", album.get("id"))
    save_path = Path(output_dir) / name
    save_path.mkdir(parents=True, exist_ok=True)
    return {"save_path": save_path, "songs": songs}


def _resolve_one_youtube_album(query, output_dir, limit):
    """Search, select and expand a single album via YouTube Music.
    :return a download unit ({save_path, songs}) or None to skip
    """
    albums = search_youtube_albums(query, limit)
    if not albums:
        log.error("No album results found for '%s', skipping.", query)
        return None
    displays = [format_youtube_album(a) for a in albums]
    index = prompt_user_selection(displays, query)
    if index is None:
        log.info("Skipped '%s'.", query)
        return None
    album = albums[index]
    with ytmusicapi.YTMusic() as ym:
        detail = ym.get_album(album.get("browseId"))

    album_name = detail.get("title", album.get("title", "album"))
    year = (detail.get("year") or "")[:4]
    thumbnails = detail.get("thumbnails", [])
    album_cover = thumbnails[-1]["url"] if thumbnails else None
    tracks = detail.get("tracks", [])
    total = len(tracks)

    songs = []
    for position, track in enumerate(tracks, start=1):
        song = build_song_dict_from_youtube(track)
        song["album"] = album_name
        song["year"] = year
        song["num"] = position
        song["num_tracks"] = total
        song["playlist_num"] = position
        if song.get("cover") is None:
            song["cover"] = album_cover
        songs.append(song)

    save_path = Path(output_dir) / sanitize(album_name)
    save_path.mkdir(parents=True, exist_ok=True)
    return {"save_path": save_path, "songs": songs}


def resolve_albums(queries, output_dir, sp=None, limit=5):
    """
    Resolve album-name queries into download units via interactive selection.

    Uses Spotify search when ``sp`` is provided, otherwise (or when a Spotify
    request errors out) falls back to YouTube Music.
    :param queries: list of free text album queries
    :param output_dir: base directory; each album gets its own sub-folder
    :param sp: Spotify client, or None to use the YouTube Music backend
    :param limit: maximum number of candidates shown per query
    :return list of download units, each a dict with save_path and songs
    """
    units = []
    spotify_failed = False
    for query in queries:
        unit = None
        if sp is not None and not spotify_failed:
            try:
                unit = _resolve_one_spotify_album(sp, query, output_dir, limit)
            except Exception as exc:  # skipcq: PYL-W0703
                log.warning(
                    "Spotify album search failed (%s); falling back to "
                    "YouTube Music.",
                    exc,
                )
                spotify_failed = True

        if sp is None or spotify_failed:
            unit = _resolve_one_youtube_album(query, output_dir, limit)

        if unit is not None:
            units.append(unit)
    return units
