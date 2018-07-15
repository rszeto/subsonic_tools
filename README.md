# Subsonic Tools: Playlist Sorter

The included script sorts all playlists on a Subsonic server in alphabetical order. It runs on Python 2.7.

## Installation

```
virtualenv .env
source .env/bin/activate
pip install -r requirements.txt
```

## Set up environment

```
cp config.json.example config.json
```

Then edit `config.json` in your favorite text editor.

## Usage

Example usage:

```
python subsonic_tools.py sort_playlists
```

Example usage with verbose messages:

```
python subsonic_tools.py --verbose sort_playlists
```
