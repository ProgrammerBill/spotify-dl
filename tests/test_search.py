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
