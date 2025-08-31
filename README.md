# Spotify Terminal CLI (Python)

Control your Spotify playback straight from your terminal with an interactive menu.  
Pick commands by number (play/pause, skip, volume, shuffle, search, etc.) — no need to re-run Python with arguments each time.

> ⚠️ **Spotify Premium is required** for playback control via the Web API.

---

## Features
- Always-on **menu interface**  
- Show **now playing** status (track, artist, device, progress)  
- **Play / pause / resume**  
- **Next / previous** track  
- **Add to queue**  
- **Shuffle** on/off/toggle  
- **Repeat** off/context/track  
- **Set volume** (0–100)  
- List & **switch devices**  
- Play by **Spotify URI/URL**  
- **Search** for tracks, albums, artists, or playlists and play by selection  

---

## Setup

### 1. Create a Spotify Developer App
1. Go to <https://developer.spotify.com/dashboard>
2. Create a new app (any name is fine).
3. Add a **Redirect URI**:  
   ```
   http://127.0.0.1:8080/callback
   ```
   (Spotify no longer accepts `localhost`; you must use `127.0.0.1`)

4. Copy your **Client ID** and **Client Secret**.

---

### 2. Clone or download this repo

```bash
git clone https://github.com/yourname/spotify-terminal-cli.git
cd spotify-terminal-cli
```

---

### 3. Create a virtual environment & install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

### 4. Configure environment variables

Copy `.env.example` → `.env` and fill in your credentials:

```env
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://127.0.0.1:8080/callback
```

> The value of `SPOTIPY_REDIRECT_URI` must **exactly match** what you registered on the Spotify Developer Dashboard.

---

### 5. First run

```bash
python spotify_menu.py
```

On first run, your browser will open to authorize the app. A token will be cached at:
```
~/.config/spotify-cli/.cache
```

---

## Usage

When you run `spotify_menu.py`, you’ll see a menu like:

```
=== Spotify Terminal Controller ===
 1) Status (now playing)
 2) Play / Resume
 3) Pause
 4) Next track
 5) Previous track
 6) Add to queue
 7) Volume 0–100
 8) Shuffle on/off/toggle
 9) Repeat off/context/track
10) Devices (list)
11) Switch device
12) Play a specific URI/URL
13) Search & (optionally) play
14) Refresh
15) Quit
```

Just type the number, hit Enter, and follow any prompts. Example:
- `13` → enter `"taylor swift cruel summer"` → choose from results.
- `7` → enter `40` → sets volume to 40%.  
- `11` → lists devices → pick the number to transfer playback.

Press **Ctrl+C** or choose `15) Quit` to exit.

---

## Notes
- **Playback control requires Spotify Premium.**
- The Spotify app must be open on at least one device (phone, desktop, web).
- To re-authenticate, delete the cache file:  
  ```
  rm ~/.config/spotify-cli/.cache
  ```
