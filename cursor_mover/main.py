import time
from typing import Optional

import pyautogui
import typer

app = typer.Typer()

CURSOR_MOVE_DURATION = 1
STOP_AT_CORNER_TIME = 0.5
SIDE_LENGTH = 200


def _move_cursor() -> None:
    for move in [
        (SIDE_LENGTH, 0),
        (0, SIDE_LENGTH),
        (-SIDE_LENGTH, 0),
        (0, -SIDE_LENGTH),
    ]:
        pyautogui.moveRel(*move, duration=CURSOR_MOVE_DURATION)
        time.sleep(STOP_AT_CORNER_TIME)


def _format_elapsed(elapsed: float) -> str:
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


@app.command()
def run(
    timeout: Optional[int] = typer.Option(None, "--time", "-t", help="Time in seconds to run the script"),
) -> None:
    """Move the cursor in a square pattern."""
    print("Starting in 3 seconds...")
    time.sleep(3)

    start_time = time.time()
    try:
        if timeout is not None:
            while time.time() - start_time < timeout:
                _move_cursor()
        else:
            while True:
                _move_cursor()
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\nApp ran for {_format_elapsed(elapsed)}")


if __name__ == "__main__":
    app()
