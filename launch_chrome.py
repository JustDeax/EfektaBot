#!/usr/bin/env python3
"""Cross-platform launcher for Google Chrome / Chromium with remote debugging enabled (port 9222).

Supports Linux, Windows, and macOS.
"""

import os
import platform
import subprocess
import sys
import time
import urllib.request

try:
    import psutil
except ImportError:
    psutil = None

from bot import find_chrome_executable, is_cdp_ready, CDP_URL

TARGET_URL = "https://learn.better.efekta.com/gap/ui/self-study"
PROFILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chrome_profile")


def kill_existing_chrome_instances():
    """Cross-platform termination of existing Chrome instances using debugging port or profile."""
    print("[*] Checking and closing existing Chrome instances...")
    terminated_any = False

    # Method 1: psutil (cleanest cross-platform method)
    if psutil:
        try:
            current_pid = os.getpid()
            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    if proc.info["pid"] == current_pid:
                        continue
                    cmdline = proc.info.get("cmdline") or []
                    cmd_str = " ".join(cmdline).lower()
                    name = (proc.info.get("name") or "").lower()

                    is_chrome_proc = any(b in name for b in ("chrome", "chromium"))
                    is_debug_port = "remote-debugging-port=9222" in cmd_str
                    is_our_profile = "chrome_profile" in cmd_str

                    if (is_chrome_proc and is_debug_port) or is_our_profile:
                        proc.terminate()
                        terminated_any = True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            if terminated_any:
                time.sleep(1.0)
                # Force kill if still lingering
                for proc in psutil.process_iter(["pid", "cmdline"]):
                    try:
                        cmd_str = " ".join(proc.info.get("cmdline") or []).lower()
                        if "remote-debugging-port=9222" in cmd_str or "chrome_profile" in cmd_str:
                            proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
        except Exception as e:
            print(f"  [!] Note during psutil process cleanup: {e}")

    # Method 2: System utilities fallback
    system = platform.system().lower()
    try:
        if "windows" in system or system == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["taskkill", "/F", "/IM", "chromium.exe", "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif "darwin" in system:
            subprocess.run(["pkill", "-f", "Google Chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["killall", "Google Chrome"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:  # Linux / other Unix
            subprocess.run(["pkill", "-f", "remote-debugging-port=9222"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    time.sleep(1.0)


def launch_chrome():
    """Locates and starts Chrome/Chromium with remote debugging port 9222."""
    chrome_exe = find_chrome_executable()
    if not chrome_exe:
        print("\n[!] Error: Google Chrome or Chromium executable could not be found.")
        print("[*] Please install Google Chrome or Chromium, or set the CHROME_BIN environment variable:")
        print("    Linux / macOS:  export CHROME_BIN=/path/to/google-chrome")
        print("    Windows:        set CHROME_BIN=C:\\path\\to\\chrome.exe")
        sys.exit(1)

    kill_existing_chrome_instances()

    os.makedirs(PROFILE_DIR, exist_ok=True)
    print(f"[*] Launching: {chrome_exe}")
    print(f"[*] Debugging Port: 9222")
    print(f"[*] User Data Dir:  {PROFILE_DIR}")
    print(f"[*] Target URL:     {TARGET_URL}\n")

    cmd = [
        chrome_exe,
        "--remote-debugging-port=9222",
        f"--user-data-dir={PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--autoplay-policy=no-user-gesture-required",
        TARGET_URL,
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("[*] Waiting for Chrome remote debugging endpoint to become ready...")
    for _ in range(25):
        if is_cdp_ready():
            print("\n[✓] Google Chrome / Chromium is active and listening on port 9222!")
            print("[*] If prompted, log into your Efekta account in the open browser window.")
            print("[*] Then run the autonomous bot with:")
            print("    python bot.py\n")
            return
        time.sleep(0.5)

    print("\n[!] Warning: Timed out waiting for Chrome debugging port 9222.")
    print("[*] Check if another process is occupying port 9222 or if Chrome was blocked.")


if __name__ == "__main__":
    launch_chrome()
