"""DiceBear avatars. Each profile stores a seed; the SVG is rendered from the
DiceBear HTTP API. New profiles get a random seed, and users can pick a
different look from a grid of presets on their profile page."""

import secrets
from urllib.parse import quote

# DiceBear style + endpoint. "avataaars" is the classic cartoon-portrait look.
STYLE = "avataaars"
BASE_URL = "https://api.dicebear.com/9.x"

# Preset seeds offered in the picker. Any short token works as a seed; these
# just give a varied, repeatable set of faces to choose from.
PRESETS = [
    "Felix",
    "Aneka",
    "Bandit",
    "Midnight",
    "Cleo",
    "Oscar",
    "Luna",
    "Milo",
    "Nala",
    "Simba",
    "Ziggy",
    "Pepper",
    "Rocky",
    "Coco",
    "Bear",
    "Daisy",
    "Gizmo",
    "Hazel",
    "Jasper",
    "Kiki",
    "Loki",
    "Maple",
    "Nova",
    "Pixel",
    "Rusty",
    "Sage",
    "Tiger",
    "Willow",
    "Zoe",
    "Atlas",
]


def random_seed():
    """A unique-ish random seed, used as the default for new profiles."""
    return secrets.token_hex(4)


# Kept under its old name for the 0030 migration's historical default.
random_key = random_seed


def url(seed):
    """The DiceBear SVG URL for a seed."""
    return f"{BASE_URL}/{STYLE}/svg?seed={quote(str(seed), safe='')}"


def options(current=None):
    """Seeds for the picker — the current one first, then the presets."""
    seeds = [current] if current else []
    seeds += [seed for seed in PRESETS if seed != current]
    return seeds
