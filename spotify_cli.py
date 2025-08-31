#!/usr/bin/env python3
import argparse
import os
import sys
import time
from datetime import timedelta
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

# -------- Auth --------

SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
]
SCOPE_STR = " ".join(SCOPES)

def make_spotify_client() -> spotipy.Spotify:
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8080/callback")

    if not client_id or not client_secret:
        print("[!] Missing credentials. Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET.", file=sys.stderr)
        print("    You can use a .env file or export shell variables.", file=sys.stderr)
        sys.exit(1)

    cache_path = os.path.expanduser("~/.config/spotify-cli/.cache")
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE_STR,
        cache_handler=CacheFileHandler(cache_path),
        open_browser=True,
        show_dialog=False,
    )
    return spotipy.Spotify(auth_manager=auth_manager)

# -------- Helpers --------

def ms_to_mmss(ms: int) -> str:
    if ms is None:
        return "--:--"
    s = int(ms // 1000)
    return f"{s // 60:02d}:{s % 60:02d}"

def get_devices(sp: spotipy.Spotify):
    d = sp.devices()
    return d.get("devices", [])

def find_device(sp: spotipy.Spotify, query: str) -> Optional[str]:
    """Return device_id matching id or (case-insensitive) substring of the device name."""
    for dev in get_devices(sp):
        if dev["id"] == query:
            return dev["id"]
        if query.lower() in dev["name"].lower():
            return dev["id"]
    return None

def ensure_device(sp: spotipy.Spotify, device: Optional[str], force_play: bool=False) -> Optional[str]:
    """Return a device_id. If 'device' is given, try to transfer playback there."""
    if device:
        target = find_device(sp, device)
        if not target:
            print(f"[!] No device matching '{device}' found. Use `devices` to list.", file=sys.stderr)
            sys.exit(1)
        try:
            sp.transfer_playback(device_id=target, force_play=force_play)
        except spotipy.SpotifyException as e:
            handle_spotify_exception(e, "transfer playback")
        return target

    # If no device specified, prefer the currently active one if any
    devices = get_devices(sp)
    for dev in devices:
        if dev.get("is_active"):
            return dev["id"]
    # Otherwise return the first available device (but don't transfer unless needed)
    if devices:
        return devices[0]["id"]
    return None

def handle_spotify_exception(e: spotipy.SpotifyException, action: str):
    status = getattr(e, "http_status", None)
    msg = getattr(e, "msg", str(e))
    if status == 403:
        print(f"[!] Spotify API rejected the request (403) while trying to {action}.", file=sys.stderr)
        print("    Playback control via Web API requires Spotify Premium.", file=sys.stderr)
    elif status == 404:
        print(f"[!] Resource not found while trying to {action}.", file=sys.stderr)
    elif status == 401:
        print(f"[!] Unauthorized (401). Your token may be expired. Try deleting the cache and re-auth.", file=sys.stderr)
    else:
        print(f"[!] Spotify API error during {action}: {msg}", file=sys.stderr)
    sys.exit(1)

def print_devices(sp: spotipy.Spotify):
    devices = get_devices(sp)
    if not devices:
        print("No available devices. Open Spotify on at least one device, then try again.")
        return
    print("Devices:")
    for dev in devices:
        active = " (active)" if dev.get("is_active") else ""
        vol = dev.get("volume_percent")
        vol_str = f" vol={vol}%" if vol is not None else ""
        print(f" - {dev['name']} [{dev['type']}] id={dev['id']}{active}{vol_str}")

def print_status(sp: spotipy.Spotify):
    pb = sp.current_playback()
    if not pb:
        print("Nothing is playing.")
        return
    item = pb.get("item")
    is_playing = pb.get("is_playing")
    device = pb.get("device", {})
    progress = pb.get("progress_ms", 0)
    shuffle = pb.get("shuffle_state")
    repeat = pb.get("repeat_state")
    name = item.get("name") if item else "—"
    artists = ", ".join(a["name"] for a in (item.get("artists") or [])) if item else "—"
    duration = item.get("duration_ms") if item else None

    print(f"{'▶️' if is_playing else '⏸️'} {name} — {artists}")
    print(f"Device: {device.get('name','?')}  |  {ms_to_mmss(progress)} / {ms_to_mmss(duration)}")
    print(f"Shuffle: {shuffle}  |  Repeat: {repeat}")

# -------- Commands --------

def cmd_devices(sp, args):
    print_devices(sp)

def cmd_device_set(sp, args):
    target = find_device(sp, args.device)
    if not target:
        print(f"[!] No device matching '{args.device}' found.")
        sys.exit(1)
    try:
        sp.transfer_playback(target, force_play=args.play)
        print(f"Transferred playback to device: {args.device}")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "transfer playback")

def cmd_play(sp, args):
    device_id = ensure_device(sp, args.device, force_play=True)
    if args.uri:
        # If URL is given, Spotipy accepts it as-is
        try:
            sp.start_playback(device_id=device_id, uris=[args.uri])
            print("Playing:", args.uri)
        except spotipy.SpotifyException as e:
            handle_spotify_exception(e, "start playback (uri)")
    else:
        try:
            sp.start_playback(device_id=device_id)
            print("Resumed playback.")
        except spotipy.SpotifyException as e:
            handle_spotify_exception(e, "resume playback")

def cmd_pause(sp, args):
    try:
        sp.pause_playback()
        print("Paused.")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "pause")

def cmd_next(sp, args):
    try:
        sp.next_track()
        print("Skipped to next track.")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "next track")

def cmd_prev(sp, args):
    try:
        sp.previous_track()
        print("Went to previous track.")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "previous track")

def cmd_queue_add(sp, args):
    device_id = ensure_device(sp, args.device)
    try:
        sp.add_to_queue(args.uri, device_id=device_id)
        print("Added to queue:", args.uri)
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "add to queue")

def cmd_shuffle(sp, args):
    state = args.state.lower()
    if state not in ("on", "off", "toggle"):
        print("[!] shuffle expects: on | off | toggle")
        sys.exit(1)
    try:
        if state == "toggle":
            pb = sp.current_playback()
            cur = pb.get("shuffle_state") if pb else False
            sp.shuffle(not cur)
            print(f"Shuffle {'on' if not cur else 'off'}.")
        else:
            sp.shuffle(state == "on")
            print(f"Shuffle {state}.")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "set shuffle")

def cmd_repeat(sp, args):
    state = args.state.lower()
    if state not in ("off", "context", "track"):
        print("[!] repeat expects: off | context | track")
        sys.exit(1)
    try:
        sp.repeat(state)
        print(f"Repeat set to: {state}")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "set repeat")

def cmd_volume(sp, args):
    pct = args.percent
    if pct < 0 or pct > 100:
        print("[!] volume percent must be between 0 and 100")
        sys.exit(1)
    try:
        sp.volume(pct)
        print(f"Volume set to {pct}%")
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "set volume")

def cmd_status(sp, args):
    print_status(sp)

def cmd_search(sp, args):
    qtype = args.type.lower()
    if qtype not in ("track", "album", "playlist", "artist"):
        print("[!] search --type must be one of: track, album, playlist, artist")
        sys.exit(1)

    try:
        res = sp.search(q=args.query, type=qtype, limit=args.limit)
    except spotipy.SpotifyException as e:
        handle_spotify_exception(e, "search")

    items_key = qtype + "s"
    items = res.get(items_key, {}).get("items", [])
    if not items:
        print("No results.")
        return

    # Print results
    for i, it in enumerate(items, start=1):
        if qtype == "track":
            artists = ", ".join(a["name"] for a in it["artists"])
            print(f"{i:2d}. {it['name']} — {artists}  ({it['uri']})")
        else:
            print(f"{i:2d}. {it['name']}  ({it['uri']})")

    if args.play:
        uri = items[0]["uri"]
        device_id = ensure_device(sp, args.device, force_play=True)
        try:
            if qtype == "track":
                sp.start_playback(device_id=device_id, uris=[uri])
            else:
                sp.start_playback(device_id=device_id, context_uri=uri)
            print(f"Playing top {qtype}: {uri}")
        except spotipy.SpotifyException as e:
            handle_spotify_exception(e, "start playback (search result)")

# -------- Main / CLI --------

def main():
    parser = argparse.ArgumentParser(
        prog="spotify_cli.py",
        description="Control Spotify playback from your terminal."
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # devices
    p = sub.add_parser("devices", help="List available devices")
    p.set_defaults(func=cmd_devices)

    # device set
    p = sub.add_parser("device", help="Manage devices")
    sub2 = p.add_subparsers(dest="subcmd", required=True)
    pset = sub2.add_parser("set", help="Transfer playback to a device (by name or id)")
    pset.add_argument("device", help="Device name or id (substring match on name allowed)")
    pset.add_argument("--play", action="store_true", help="Start playback after transfer")
    pset.set_defaults(func=cmd_device_set)

    # play
    p = sub.add_parser("play", help="Resume playback or play a specific URI/URL")
    p.add_argument("--uri", help="Track/album/playlist URI or open.spotify.com URL")
    p.add_argument("--device", help="Device name or id")
    p.set_defaults(func=cmd_play)

    # pause
    p = sub.add_parser("pause", help="Pause playback")
    p.set_defaults(func=cmd_pause)

    # next
    p = sub.add_parser("next", help="Skip to next track")
    p.set_defaults(func=cmd_next)

    # prev
    p = sub.add_parser("prev", help="Go to previous track")
    p.set_defaults(func=cmd_prev)

    # queue add
    p = sub.add_parser("queue", help="Manage queue")
    subq = p.add_subparsers(dest="subcmd", required=True)
    padd = subq.add_parser("add", help="Add a track to the queue by URI/URL")
    padd.add_argument("uri", help="Track URI/URL to queue")
    padd.add_argument("--device", help="Device name or id (optional)")
    padd.set_defaults(func=cmd_queue_add)

    # shuffle
    p = sub.add_parser("shuffle", help="Turn shuffle on/off or toggle")
    p.add_argument("state", help="on | off | toggle")
    p.set_defaults(func=cmd_shuffle)

    # repeat
    p = sub.add_parser("repeat", help="Set repeat mode")
    p.add_argument("state", help="off | context | track")
    p.set_defaults(func=cmd_repeat)

    # volume
    p = sub.add_parser("volume", help="Set volume percent (0–100)")
    p.add_argument("percent", type=int)
    p.set_defaults(func=cmd_volume)

    # status
    p = sub.add_parser("status", help="Show now playing and device")
    p.set_defaults(func=cmd_status)

    # search
    p = sub.add_parser("search", help="Search for tracks/albums/playlists/artists")
    p.add_argument("query", help="Search query (quotes recommended)")
    p.add_argument("--type", default="track", help="track | album | playlist | artist (default: track)")
    p.add_argument("--limit", type=int, default=5, help="Max number of results to print (default: 5)")
    p.add_argument("--play", action="store_true", help="Play the top result immediately")
    p.add_argument("--device", help="Device name or id (optional)")
    p.set_defaults(func=cmd_search)

    args = parser.parse_args()
    sp = make_spotify_client()
    args.func(sp, args)

if __name__ == "__main__":
    main()
