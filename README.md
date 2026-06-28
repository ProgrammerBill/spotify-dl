## spotify_dl

Downloads songs from any Spotify playlist, album or track.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](http://makeapullrequest.com)
[![PyPI download month](https://img.shields.io/pypi/dm/spotify_dl.svg)](https://pypi.python.org/pypi/spotify_dl/)
[![PyPI license](https://img.shields.io/pypi/l/spotify_dl.svg)](https://pypi.python.org/pypi/spotify_dl/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/spotify_dl.svg)](https://pypi.python.org/pypi/spotify_dl/)
[![GitHub release](https://img.shields.io/github/release/SathyaBhat/spotify-dl.svg)](https://GitHub.com/SathyaBhat/spotify-dl/releases/)
[![GitHub stars](https://img.shields.io/github/stars/SathyaBhat/spotify-dl.svg?style=social&label=Star&maxAge=2592000)](https://GitHub.com/SathyaBhat/spotify-dl/stargazers/)
[![GitHub contributors](https://img.shields.io/github/contributors/SathyaBhat/spotify-dl.svg)](https://GitHub.com/SathyaBhat/spotify-dl/graphs/contributors/)

[![Awesome Badges](https://img.shields.io/badge/badges-awesome-green.svg)](https://github.com/Naereen/badges)

### Tell me more!

I wanted an easy way to grab the songs present in my library so I can download it & use it offline. I no longer use this, but continue to maintain this. spotify-dl doesn't download anything from Spotify. It picks up the metadata from Spotify API and then uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to download the song.

### How do I get this thing running?

Install using pip

    pip3 install spotify_dl

Run the program

    spotify_dl -l spotify_playlist_link_1 spotify_playlist_link_2

#### Download a song by name

You can search for and download a song by name (optionally with the artist) using `-q`/`--song`, without needing a Spotify link:

    spotify_dl -q "Bohemian Rhapsody Queen"

spotify-dl shows the top matches and asks you to pick one:

    Results for Bohemian Rhapsody Queen:
      1. Bohemian Rhapsody — Queen — A Night At The Opera (1975)
      2. Bohemian Rhapsody — Queen — Bohemian Rhapsody (The Original Soundtrack)
      3. Bohemian Rhapsody - Live Aid — Queen — Bohemian Rhapsody
    Select 1-5 (Enter for 1, 's' to skip):

Type the number of the match you want, press `Enter` to take the first one, or `s` to skip. Pass multiple songs at once to be prompted for each in turn:

    spotify_dl -q "Bohemian Rhapsody Queen" "Hotel California Eagles"

#### Download a whole album by name

Use `-a`/`--album` to search for an album by name (optionally with the artist) and download **all** of its tracks into a folder named after the album:

    spotify_dl -a "A Night At The Opera Queen"

You pick the album from the top matches, then every track on it is downloaded automatically:

    Results for A Night At The Opera Queen:
      1. A Night At The Opera — Queen — 1975 — 12 tracks
      2. A Night At The Opera (Deluxe Remastered) — Queen — 2011 — 24 tracks
    Select 1-5 (Enter for 1, 's' to skip): 1

Multiple albums can be queued in one command:

    spotify_dl -a "A Night At The Opera Queen" "Hotel California Eagles"

#### How the search backend is chosen

Both `-q` and `-a` pick a backend automatically:

* When Spotify API credentials are set, the search runs through Spotify (giving full metadata such as album, cover art and year).
* When no credentials are found — or a Spotify request fails (for example a `403` because the app owner lacks the required subscription) — spotify-dl falls back to searching YouTube Music directly.

So you can use `-q`/`-a` with no Spotify credentials at all. If your network blocks YouTube, pass a proxy with `-p`, e.g. `-p "http://127.0.0.1:7890"`.

If you want to make use of parallel download, pass `-mc <number>`, where `<number>` refers to number of cores. If this is too high, spotify-dl will set it to one lesser than max number of cores that you have.

    spotify_dl -mc 4 -l spotify_playlist_link_1 spotify_playlist_link_2

Spotify-dl can make use of SponsorBlock and skip non-music sections when downloading from YouTube. This is disabled by default and can be enabled using:

        spotify_dl -l spotify_playlist_link_1 -s y

For running in verbose mode, append `-V`

    spotify_dl -V -l spotify_playlist_link -o download_directory

For more details and other arguments, issue `-h`

    spotify_dl -h

See [the getting started guide](https://github.com/SathyaBhat/spotify-dl/blob/master/GETTING_STARTED.md) for more details.

### Demo

[![asciicast](https://asciinema.org/a/488558.svg)](https://asciinema.org/a/488558)

### Contributing and Local development

Pull requests and any contributions are always welcome. Please open an issue with your proposal before you start with something.

#### Running tests

Tests are setup and run with pytest, run

    make tests

to run the tests with [Make](https://www.gnu.org/software/make/)

### Thanks and Credits

Take a look at [CONTRIBUTORS](https://github.com/SathyaBhat/spotify-dl/graphs/contributors) for a list of all people who have helped and contributed to the project.

### Issues, Feedback, Contact details

Feel free to raise any bugs/issues under Github issues. Pull requests are also more than welcome.
