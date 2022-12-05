import json
import sys
import time
from pathlib import Path

import pygame


WEB = sys.platform == "emscripten"
DIR = Path(".")

SMALL_FONT = pygame.font.Font(DIR / "assets" / "VeraMono.ttf", 16)
LARGE_FONT = pygame.font.Font(DIR / "assets" / "VeraMono.ttf", 32)


def caesar(text: str, shift=3):
    return "".join(
        chr((ord(char) + shift - 65) % 26 + 65)
        if char.isupper()
        else chr((ord(char) + shift - 97) % 26 + 97)
        for char in text
    )


def lerp(x: float, x1: float, x2: float, y1: float, y2: float) -> float:
    return y1 + (x - x1) * (y2 - y1) / (x2 - x1)


def log(**kwargs):
    with open("log.txt", "a") as f:
        f.write(f"{time.time()}:")
        json.dump(kwargs, f)
        f.write(",")


def to_time(secs: int, with_days=False):
    day = int(secs // 86400)
    hour = int(secs // 3600 % 24)
    minute = int(secs // 60 % 60)
    second = int(secs % 60)

    if with_days:
        return (
            f"D{day} {str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"
        )
    else:
        return f"{str(hour).zfill(2)}:{str(minute).zfill(2)}:{str(second).zfill(2)}"
