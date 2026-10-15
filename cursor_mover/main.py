import time
from typing import Optional

import pyautogui
import typer

app = typer.Typer()

CURSOR_MOVE_DURATION = 5
STOP_AT_CORNER_TIME = 15.0
SIDE_LENGTH = 200


def _move_cursor(web_ping: bool) -> None:
    for move in [
        (SIDE_LENGTH, 0),
        (0, SIDE_LENGTH),
        (-SIDE_LENGTH, 0),
        (0, -SIDE_LENGTH),
    ]:
        pyautogui.moveRel(*move, duration=CURSOR_MOVE_DURATION)
        time.sleep(STOP_AT_CORNER_TIME)
    if web_ping:
        _ping_website()


def _format_elapsed(elapsed: float) -> str:
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def _ping_website() -> None:
    import requests
    import random

    websites = [
        "http://connectivitycheck.gstatic.com/generate_204",
        "http://clients3.google.com/generate_204",
        "http://www.gstatic.com/generate_204",
        "http://cp.cloudflare.com/generate_204",
        "http://connectivity-check.ubuntu.com/",
        "http://network-test.debian.org/nm",
        "http://nmcheck.gnome.org/check_network_status.txt",
        "http://detectportal.firefox.com/success.txt",
        "http://www.msftconnecttest.com/connecttest.txt",
        "http://captive.apple.com/hotspot-detect.html",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
        "https://api.ipify.org",
        "https://1.1.1.1/cdn-cgi/trace",
        "https://example.com"
    ]

    try:
        website = random.choice(websites)
        response = requests.get(website, timeout=5)
        if response.status_code == 200:
            pass
        else:
            print(f"Failed to ping website {website} - Status code: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error pinging website: {e}")

@app.command()
def run(
    timeout: Optional[int] = typer.Option(None, "--time", "-t", help="Time in seconds to run the script"),
    web_ping: Optional[bool] = typer.Option(False, "--web-ping", "-w", help="Ping a website to keep the internet connection alive"),
) -> None:
    """Move the cursor in a square pattern."""
    print("Starting in 3 seconds...")
    time.sleep(3)

    start_time = time.time()
    try:
        if timeout is not None:
            while time.time() - start_time < timeout:
                _move_cursor(web_ping)
        else:
            while True:
                _move_cursor(web_ping)

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\nApp ran for {_format_elapsed(elapsed)}")


if __name__ == "__main__":
    app()
