"""Preset avatars users can pick from — a Font Awesome glyph plus a two-colour
gradient. Stored on the profile by key; a random one is assigned by default."""

import secrets

# key -> {icon: Font Awesome class, c1/c2: gradient stops}
AVATARS = {
    "futbol": {"icon": "fa-futbol", "c1": "#5cd6e6", "c2": "#3b82f6"},
    "trophy": {"icon": "fa-trophy", "c1": "#f5c451", "c2": "#d9a533"},
    "crown": {"icon": "fa-crown", "c1": "#f6c177", "c2": "#c08a1e"},
    "moon": {"icon": "fa-moon", "c1": "#a78bfa", "c2": "#6d5bd0"},
    "sun": {"icon": "fa-sun", "c1": "#fbbf24", "c2": "#f97316"},
    "star": {"icon": "fa-star", "c1": "#fde68a", "c2": "#f5c451"},
    "meteor": {"icon": "fa-meteor", "c1": "#fb7185", "c2": "#e11d48"},
    "rocket": {"icon": "fa-rocket", "c1": "#34d399", "c2": "#0d9488"},
    "bolt": {"icon": "fa-bolt", "c1": "#facc15", "c2": "#ca8a04"},
    "fire": {"icon": "fa-fire", "c1": "#fb923c", "c2": "#dc2626"},
    "gem": {"icon": "fa-gem", "c1": "#67e8f9", "c2": "#0891b2"},
    "dragon": {"icon": "fa-dragon", "c1": "#4ade80", "c2": "#15803d"},
    "ghost": {"icon": "fa-ghost", "c1": "#c4b5fd", "c2": "#7c3aed"},
    "cat": {"icon": "fa-cat", "c1": "#fdba74", "c2": "#b45309"},
    "dog": {"icon": "fa-dog", "c1": "#fcd34d", "c2": "#92400e"},
    "crow": {"icon": "fa-crow", "c1": "#94a3b8", "c2": "#475569"},
    "frog": {"icon": "fa-frog", "c1": "#86efac", "c2": "#16a34a"},
    "horse": {"icon": "fa-horse", "c1": "#d6bcfa", "c2": "#9061f9"},
    "otter": {"icon": "fa-otter", "c1": "#fca5a5", "c2": "#b91c1c"},
    "hippo": {"icon": "fa-hippo", "c1": "#a5b4fc", "c2": "#4f46e5"},
    "spider": {"icon": "fa-spider", "c1": "#cbd5e1", "c2": "#334155"},
    "chess-knight": {"icon": "fa-chess-knight", "c1": "#fda4af", "c2": "#9f1239"},
}

DEFAULT = "futbol"
KEYS = list(AVATARS)


def random_key():
    """A random avatar key — used as the model default for new profiles."""
    return secrets.choice(KEYS)


def get(key):
    """Returns the avatar dict for a key, falling back to the default."""
    return AVATARS.get(key, AVATARS[DEFAULT])


def choices():
    """(key, data) pairs for rendering the picker."""
    return list(AVATARS.items())
