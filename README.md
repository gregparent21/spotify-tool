# Spotify Terminal CLI (Python)

Control your Spotify playback from the terminal: play/pause, next/prev, volume, shuffle, repeat, manage devices, add to queue, and even search + play.

> **Requires Spotify Premium** for playback controls via the Web API.

## Features
- List & switch **devices**
- **Play / pause / resume** & **skip** tracks
- **Add to queue**
- Toggle **shuffle** and set **repeat**
- Set **volume**
- Show a nice **now playing** status line
- **Search & play** (top result) by query

## Quick Start (macOS/Linux/Windows)

1) **Create a Spotify Developer App**
   - Go to <https://developer.spotify.com/dashboard>
   - Create an app (any name), then add a Redirect URI: `http://localhost:8080/callback`
   - Copy the **Client ID** and **Client Secret**

2) **Clone or download this folder**

3) **Create a virtualenv (recommended) and install deps**
```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

4) **Set environment variables**
- Option A: export in your shell
```bash
export SPOTIPY_CLIENT_ID="YOUR_CLIENT_ID"
export SPOTIPY_CLIENT_SECRET="YOUR_CLIENT_SECRET"
export SPOTIPY_REDIRECT_URI="http://localhost:8080/callback"
```
- Option B: copy `.env.example` to `.env` and fill values, then run with `python -m dotenv -f .env run -- python spotify_cli.py ...`

5) **Authorize once (opens browser)**
```bash
python spotify_cli.py devices
```
This will open a browser to log in and grant access; token is cached at `~/.config/spotify-cli/.cache`.

## Examples
```bash
# Show devices and the active one
python spotify_cli.py devices

# Transfer playback to a device (by name or id)
python spotify_cli.py device set "Greg’s MacBook Pro"

# Resume or start playback
python spotify_cli.py play

# Play a specific track/album/playlist URI or URL
python spotify_cli.py play --uri spotify:track:1v3lG…
python spotify_cli.py play --uri https://open.spotify.com/track/1v3lG…

# Pause, next, previous
python spotify_cli.py pause
python spotify_cli.py next
python spotify_cli.py prev

# Add to queue
python spotify_cli.py queue add spotify:track:…

# Shuffle / Repeat
python spotify_cli.py shuffle on
python spotify_cli.py repeat context     # off | context | track

# Volume (0–100)
python spotify_cli.py volume 35

# Now playing
python spotify_cli.py status

# Search & play first matching track
python spotify_cli.py search "mr brightside"
python spotify_cli.py search "taylor swift cruel summer" --type track --play

# Optionally specify a device for commands that start playback
python spotify_cli.py play --device "Living Room"
python spotify_cli.py search "random access memories" --type album --play --device "MacBook"
```

## Scopes requested
- `user-read-playback-state`
- `user-modify-playback-state`
- `user-read-currently-playing`

## Notes
- For **playback control**, Spotify requires **Premium**.
- Make sure the Spotify app is open on at least one device when transferring playback.
- On first run, a browser will open to authorize and cache your token locally.
- To re-auth, delete the cache file at `~/.config/spotify-cli/.cache`.

## Uninstall / Cleanup
- Deactivate and remove the virtual environment
- Delete `~/.config/spotify-cli/.cache` to clear tokens
