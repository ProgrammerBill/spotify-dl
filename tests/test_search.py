from unittest import mock

from spotify_dl import search


SPOTIFY_TRACK = {
    "name": "Bohemian Rhapsody",
    "id": "3z8h0TU7ReDPLIbEnYhWZb",
    "track_number": 11,
    "artists": [{"name": "Queen"}],
    "album": {
        "name": "A Night At The Opera",
        "release_date": "1975-11-21",
        "total_tracks": 12,
        "images": [{"url": "https://img/cover.jpg"}],
    },
}

YOUTUBE_RESULT = {
    "title": "Bohemian Rhapsody",
    "videoId": "fJ9rUzIMcZQ",
    "artists": [{"name": "Queen"}],
    "album": {"name": "A Night At The Opera"},
    "thumbnails": [{"url": "https://img/small.jpg"}, {"url": "https://img/large.jpg"}],
}


def test_build_song_dict_from_spotify():
    song = search.build_song_dict_from_spotify(SPOTIFY_TRACK)
    assert song == {
        "name": "Bohemian Rhapsody",
        "artist": "Queen",
        "album": "A Night At The Opera",
        "year": "1975",
        "num_tracks": 12,
        "num": 11,
        "playlist_num": 1,
        "cover": "https://img/cover.jpg",
        "genre": "",
        "spotify_id": "3z8h0TU7ReDPLIbEnYhWZb",
        "track_url": None,
        "tempo": None,
    }


def test_build_song_dict_from_spotify_handles_missing_album_art():
    track = dict(SPOTIFY_TRACK, album=dict(SPOTIFY_TRACK["album"], images=[]))
    song = search.build_song_dict_from_spotify(track)
    assert song["cover"] is None


def test_build_song_dict_from_youtube():
    song = search.build_song_dict_from_youtube(YOUTUBE_RESULT)
    assert song["name"] == "Bohemian Rhapsody"
    assert song["artist"] == "Queen"
    assert song["album"] == "A Night At The Opera"
    assert song["cover"] == "https://img/large.jpg"
    assert song["spotify_id"] is None
    assert song["tempo"] is None
    assert song["playlist_num"] == 1


def test_format_spotify_candidate():
    assert (
        search.format_spotify_candidate(SPOTIFY_TRACK)
        == "Bohemian Rhapsody — Queen — A Night At The Opera (1975)"
    )


def test_format_youtube_candidate():
    assert (
        search.format_youtube_candidate(YOUTUBE_RESULT)
        == "Bohemian Rhapsody — Queen — A Night At The Opera"
    )


def test_prompt_user_selection_picks_number():
    with mock.patch("builtins.input", return_value="2"):
        assert search.prompt_user_selection(["a", "b", "c"], "q") == 1


def test_prompt_user_selection_enter_defaults_to_first():
    with mock.patch("builtins.input", return_value=""):
        assert search.prompt_user_selection(["a", "b"], "q") == 0


def test_prompt_user_selection_skip_returns_none():
    with mock.patch("builtins.input", return_value="s"):
        assert search.prompt_user_selection(["a", "b"], "q") is None


def test_prompt_user_selection_retries_on_invalid():
    with mock.patch("builtins.input", side_effect=["9", "0", "x", "1"]):
        assert search.prompt_user_selection(["a", "b"], "q") == 0


def test_resolve_songs_spotify_backend():
    sp = mock.Mock()
    with mock.patch.object(
        search, "search_spotify_tracks", return_value=[SPOTIFY_TRACK]
    ) as mock_search, mock.patch("builtins.input", return_value="1"):
        songs = search.resolve_songs(["Bohemian Rhapsody Queen"], sp=sp)
    mock_search.assert_called_once_with(sp, "Bohemian Rhapsody Queen", 5)
    assert len(songs) == 1
    assert songs[0]["name"] == "Bohemian Rhapsody"
    assert songs[0]["spotify_id"] == "3z8h0TU7ReDPLIbEnYhWZb"


def test_resolve_songs_youtube_backend_when_no_client():
    with mock.patch.object(
        search, "search_youtube_tracks", return_value=[YOUTUBE_RESULT]
    ) as mock_search, mock.patch("builtins.input", return_value="1"):
        songs = search.resolve_songs(["Bohemian Rhapsody"], sp=None)
    mock_search.assert_called_once_with("Bohemian Rhapsody", 5)
    assert len(songs) == 1
    assert songs[0]["name"] == "Bohemian Rhapsody"
    assert songs[0]["spotify_id"] is None


def test_resolve_songs_falls_back_to_youtube_on_spotify_error():
    with mock.patch.object(
        search, "search_spotify_tracks", side_effect=Exception("403 Forbidden")
    ), mock.patch.object(
        search, "search_youtube_tracks", return_value=[YOUTUBE_RESULT]
    ) as mock_yt, mock.patch("builtins.input", return_value="1"):
        songs = search.resolve_songs(["说谎"], sp=mock.Mock())
    mock_yt.assert_called_once_with("说谎", 5)
    assert len(songs) == 1
    assert songs[0]["spotify_id"] is None


def test_resolve_songs_skips_query_with_no_results():
    with mock.patch.object(search, "search_spotify_tracks", return_value=[]):
        songs = search.resolve_songs(["nonexistent"], sp=mock.Mock())
    assert songs == []


def test_resolve_songs_skips_when_user_skips():
    with mock.patch.object(
        search, "search_spotify_tracks", return_value=[SPOTIFY_TRACK]
    ), mock.patch("builtins.input", return_value="s"):
        songs = search.resolve_songs(["Bohemian Rhapsody"], sp=mock.Mock())
    assert songs == []


SPOTIFY_ALBUM = {
    "name": "A Night At The Opera",
    "id": "1GbtB4zTqAsyfZEsm1RZfx",
    "release_date": "1975-11-21",
    "total_tracks": 12,
    "artists": [{"name": "Queen"}],
}

YOUTUBE_ALBUM = {
    "title": "A Night At The Opera",
    "browseId": "MPREb_album",
    "artists": [{"name": "Queen"}],
    "year": "1975",
}

YOUTUBE_ALBUM_DETAIL = {
    "title": "A Night At The Opera",
    "year": "1975",
    "thumbnails": [{"url": "https://img/album.jpg"}],
    "tracks": [
        {"title": "Death on Two Legs", "videoId": "v1", "artists": [{"name": "Queen"}]},
        {"title": "Bohemian Rhapsody", "videoId": "v2", "artists": [{"name": "Queen"}]},
    ],
}


def _youtube_context(detail):
    ym = mock.MagicMock()
    ym.get_album.return_value = detail
    ctx = mock.MagicMock()
    ctx.__enter__.return_value = ym
    return ctx


def test_format_spotify_album():
    assert (
        search.format_spotify_album(SPOTIFY_ALBUM)
        == "A Night At The Opera — Queen — 1975 — 12 tracks"
    )


def test_format_youtube_album():
    assert (
        search.format_youtube_album(YOUTUBE_ALBUM)
        == "A Night At The Opera — Queen — 1975"
    )


def test_resolve_albums_spotify_backend(tmp_path):
    album_songs = [{"name": "Bohemian Rhapsody"}, {"name": "Death on Two Legs"}]
    with mock.patch.object(
        search, "search_spotify_albums", return_value=[SPOTIFY_ALBUM]
    ) as mock_search, mock.patch.object(
        search, "fetch_tracks", return_value=album_songs
    ) as mock_fetch, mock.patch("builtins.input", return_value="1"):
        units = search.resolve_albums(
            ["A Night At The Opera Queen"], str(tmp_path), sp=mock.Mock()
        )
    mock_search.assert_called_once()
    mock_fetch.assert_called_once()
    assert len(units) == 1
    assert units[0]["songs"] == album_songs
    assert units[0]["save_path"].name == "A Night At The Opera"
    assert units[0]["save_path"].is_dir()


def test_resolve_albums_youtube_backend(tmp_path):
    with mock.patch.object(
        search, "search_youtube_albums", return_value=[YOUTUBE_ALBUM]
    ), mock.patch.object(
        search.ytmusicapi, "YTMusic", return_value=_youtube_context(YOUTUBE_ALBUM_DETAIL)
    ), mock.patch("builtins.input", return_value="1"):
        units = search.resolve_albums(["A Night At The Opera"], str(tmp_path), sp=None)
    assert len(units) == 1
    songs = units[0]["songs"]
    assert len(songs) == 2
    assert [s["name"] for s in songs] == ["Death on Two Legs", "Bohemian Rhapsody"]
    assert all(s["album"] == "A Night At The Opera" for s in songs)
    assert all(s["num_tracks"] == 2 for s in songs)
    assert all(s["year"] == "1975" for s in songs)
    assert songs[0]["num"] == 1 and songs[1]["num"] == 2
    assert all(s["cover"] == "https://img/album.jpg" for s in songs)


def test_resolve_albums_falls_back_to_youtube_on_spotify_error(tmp_path):
    with mock.patch.object(
        search, "search_spotify_albums", side_effect=Exception("403 Forbidden")
    ), mock.patch.object(
        search, "search_youtube_albums", return_value=[YOUTUBE_ALBUM]
    ) as mock_yt, mock.patch.object(
        search.ytmusicapi, "YTMusic", return_value=_youtube_context(YOUTUBE_ALBUM_DETAIL)
    ), mock.patch("builtins.input", return_value="1"):
        units = search.resolve_albums(["A Night At The Opera"], str(tmp_path), sp=mock.Mock())
    mock_yt.assert_called_once()
    assert len(units) == 1
    assert len(units[0]["songs"]) == 2


def test_resolve_albums_skips_query_with_no_results(tmp_path):
    with mock.patch.object(search, "search_spotify_albums", return_value=[]):
        units = search.resolve_albums(["nonexistent"], str(tmp_path), sp=mock.Mock())
    assert units == []
