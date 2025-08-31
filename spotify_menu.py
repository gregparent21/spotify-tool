#!/usr/bin/env python3
import os
import sys
import time
from typing import Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheFileHandler

SCOPES = [
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
]
SCOPE_STR = " ".join(SCOPES)

def ms_to_mmss(ms: int) -> str:
    if ms is None:
        return "--:--"
    s = int(ms // 1000)
    return f"{s // 60:02d}:{s % 60:02d}"

def make_spotify_client() -> spotipy.Spotify:
    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8080/callback")

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

def print_status(sp: spotipy.Spotify):
    try:
        pb = sp.current_playback()
    except spotipy.SpotifyException as e:
        print_api_error(e, "get current playback")
        return
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

def print_devices(sp: spotipy.Spotify):
    try:
        d = sp.devices()
    except spotipy.SpotifyException as e:
        print_api_error(e, "list devices")
        return []
    devices = d.get("devices", [])
    if not devices:
        print("No available devices. Open Spotify on at least one device, then try again.")
    else:
        print("Devices:")
        for i, dev in enumerate(devices, start=1):
            active = " (active)" if dev.get("is_active") else ""
            vol = dev.get("volume_percent")
            vol_str = f" vol={vol}%" if vol is not None else ""
            print(f" {i:2d}. {dev['name']} [{dev['type']}] id={dev['id']}{active}{vol_str}")
    return devices

def choose_device(sp: spotipy.Spotify) -> Optional[str]:
    devices = print_devices(sp)
    if not devices:
        return None
    try:
        sel = input("\nSelect device # (or press Enter to cancel): ").strip()
        if not sel:
            return None
        idx = int(sel) - 1
        if idx < 0 or idx >= len(devices):
            print("[!] Invalid selection.")
            return None
        target = devices[idx]["id"]
        sp.transfer_playback(target, force_play=False)
        print(f"Transferred playback to: {devices[idx]['name']}")
        return target
    except ValueError:
        print("[!] Please enter a number.")
    except spotipy.SpotifyException as e:
        print_api_error(e, "transfer playback")
    return None

def print_api_error(e: spotipy.SpotifyException, action: str):
    status = getattr(e, "http_status", None)
    msg = getattr(e, "msg", str(e))
    if status == 403:
        print(f"[!] 403 while trying to {action}. Spotify Premium is required for playback control.")
    elif status == 401:
        print("[!] 401 Unauthorized. Your token may be expired. Delete the cache at ~/.config/spotify-cli/.cache and re-auth.")
    else:
        print(f"[!] Spotify API error during {action}: {msg}")

def prompt(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except (EOFError, KeyboardInterrupt):
        print("\nExiting.")
        sys.exit(0)

def main_menu():
    print("\n=== Spotify Terminal Controller ===")
    print(" 1) Status (now playing)")
    print(" 2) Play / Resume")
    print(" 3) Pause")
    print(" 4) Next track")
    print(" 5) Previous track")
    print(" 6) Add to queue")
    print(" 7) Volume 0–100")
    print(" 8) Shuffle on/off/toggle")
    print(" 9) Repeat off/context/track")
    print("10) Devices (list)")
    print("11) Switch device")
    print("12) Play a specific URI/URL")
    print("13) Search & (optionally) play")
    print("14) Refresh")
    print("15) Quit")
    choice = prompt("\nSelect option #: ").strip()
    return choice

def run():
    sp = make_spotify_client()
    while True:
        try:
            choice = main_menu()

            if choice == "1":
                print_status(sp)

            elif choice == "2":
                try:
                    sp.start_playback()
                    print("Resumed playback.")
                except spotipy.SpotifyException as e:
                    print_api_error(e, "resume playback")

            elif choice == "3":
                try:
                    sp.pause_playback()
                    print("Paused.")
                except spotipy.SpotifyException as e:
                    print_api_error(e, "pause")

            elif choice == "4":
                try:
                    sp.next_track()
                    print("Skipped to next track.")
                except spotipy.SpotifyException as e:
                    print_api_error(e, "next track")

            elif choice == "5":
                try:
                    sp.previous_track()
                    print("Went to previous track.")
                except spotipy.SpotifyException as e:
                    print_api_error(e, "previous track")

            elif choice == "6":
                uri = prompt("Track URI/URL to add to queue: ").strip()
                if uri:
                    try:
                        sp.add_to_queue(uri)
                        print("Added to queue.")
                    except spotipy.SpotifyException as e:
                        print_api_error(e, "add to queue")

            elif choice == "7":
                val = prompt("Volume (0–100): ").strip()
                try:
                    pct = int(val)
                    if 0 <= pct <= 100:
                        sp.volume(pct)
                        print(f"Volume set to {pct}%")
                    else:
                        print("[!] Volume must be 0–100.")
                except ValueError:
                    print("[!] Enter a number.")

            elif choice == "8":
                state = prompt("Shuffle (on/off/toggle): ").strip().lower()
                if state not in ("on","off","toggle"):
                    print("[!] Use on/off/toggle.")
                else:
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
                        print_api_error(e, "set shuffle")

            elif choice == "9":
                state = prompt("Repeat (off/context/track): ").strip().lower()
                if state not in ("off","context","track"):
                    print("[!] Use off/context/track.")
                else:
                    try:
                        sp.repeat(state)
                        print(f"Repeat set to {state}.")
                    except spotipy.SpotifyException as e:
                        print_api_error(e, "set repeat")

            elif choice == "10":
                print_devices(sp)

            elif choice == "11":
                choose_device(sp)

            elif choice == "12":
                uri = prompt("Enter track/album/playlist URI or URL: ").strip()
                if not uri:
                    continue
                # Heuristic: tracks require uris=[...]; contexts (album/playlist/artist) use context_uri=...
                try:
                    if "track" in uri:
                        sp.start_playback(uris=[uri])
                    else:
                        sp.start_playback(context_uri=uri)
                    print("Started playback.")
                except spotipy.SpotifyException as e:
                    print_api_error(e, "start playback")

            elif choice == "13":
                q = prompt("Search query: ").strip()
                t = prompt("Type (track/album/playlist/artist) [default: track]: ").strip().lower() or "track"
                try:
                    res = sp.search(q=q, type=t, limit=10)
                except spotipy.SpotifyException as e:
                    print_api_error(e, "search")
                    continue
                items_key = t + "s"
                items = res.get(items_key, {}).get("items", [])
                if not items:
                    print("No results.")
                    continue
                for i, it in enumerate(items, start=1):
                    if t == "track":
                        artists = ", ".join(a["name"] for a in it["artists"])
                        print(f"{i:2d}. {it['name']} — {artists}  ({it['uri']})")
                    else:
                        print(f"{i:2d}. {it['name']}  ({it['uri']})")
                play = prompt("Play # (or Enter to skip): ").strip()
                if play:
                    try:
                        idx = int(play) - 1
                        if idx < 0 or idx >= len(items):
                            print("[!] Invalid selection.")
                        else:
                            uri = items[idx]["uri"]
                            if t == "track":
                                sp.start_playback(uris=[uri])
                            else:
                                sp.start_playback(context_uri=uri)
                            print("Playing selection.")
                    except ValueError:
                        print("[!] Enter a number.")
                    except spotipy.SpotifyException as e:
                        print_api_error(e, "start playback from search")

            elif choice == "14":
                # Just loop to refresh
                print_status(sp)

            elif choice == "15":
                print("Goodbye!")
                break

            else:
                print("[!] Unknown option.")

            # tiny pause for nicer UX
            time.sleep(0.3)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

if __name__ == "__main__":
    run()
