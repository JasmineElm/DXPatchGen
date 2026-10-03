"""
Yamaha DX7 10-character patch name generator.
Generates authentic, evocative, and disemvoweled vintage synthesizer names tailored to categories and profiles.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional


CATEGORY_PREFIXES: Dict[str, List[str]] = {
    "keys": [
        "E.PNO", "TINE", "RHODS", "DX-PNO", "CLAV", "HRPSI", "DYNA-EP", "GLS-EP",
        "FM-KEY", "JAZZ-EP", "WRTZR", "PNO-DX", "STNG-EP", "TNE-PNO", "VIB-PNO"
    ],
    "bass": [
        "SLAP-BS", "SUB-BS", "SLD-BS", "ACD-BS", "FNK-BS", "DX-B", "SYN-B", "PNCH-BS",
        "SUB-LOW", "THMP-BS", "REZ-BS", "FZZ-BS", "GRT-BS", "PLK-BS", "303-BS", "WOB-BS"
    ],
    "pad": [
        "LSH-PD", "WM-PD", "SPCE-PD", "GLS-PD", "VOX-PD", "SOLAR-PD", "AURA-PD", "DRM-PD",
        "NBLA-PD", "ETHR-PD", "STRG-PD", "CHOR-PD", "VOID-PD", "SWP-PD", "ANLG-PD", "DARK-PD"
    ],
    "pd": [
        "LSH-PD", "WM-PD", "SPCE-PD", "GLS-PD", "VOX-PD", "SOLAR-PD", "AURA-PD", "DRM-PD",
        "NBLA-PD", "ETHR-PD", "STRG-PD", "CHOR-PD", "VOID-PD", "SWP-PD", "ANLG-PD", "DARK-PD"
    ],
    "percussive": [
        "BONK", "K-1", "SN-FM", "TOM-DX", "CYMBAL", "CLANG", "HIT-FM", "MET-DRUM",
        "HIHAT", "BARREL", "RIM-SHT", "KCK-SUB", "ZAP-PRC", "COWBL", "SHKR", "LOG-DRM",
        "KICK", "SNARE", "CLST-DR", "MRZBW-D", "THUMP"
    ],
    "drum": [
        "BONK", "K-1", "SN-FM", "TOM-DX", "CYMBAL", "CLANG", "HIT-FM", "MET-DRUM",
        "HIHAT", "BARREL", "RIM-SHT", "KCK-SUB", "ZAP-PRC", "COWBL", "SHKR", "LOG-DRM",
        "KICK", "SNARE", "CLST-DR", "MRZBW-D", "THUMP"
    ],
    "lead": [
        "SYNC-LD", "SOLO-LD", "SAW-LD", "PULS-LD", "DIGI-LD", "NEO-LD", "LZR-LD",
        "EDGE-LD", "HYPER-LD", "HERO-LD", "REZ-LD", "DIST-LD", "SHRP-LD", "GLD-LD",
        "TOX-LD", "VNTG-LD"
    ],
    "bell": [
        "CHIME", "TUBULAR", "CRYSTAL", "GLCK", "MARIMBA", "VIBES", "GAMELAN", "BELL",
        "ICE-BELL", "CELESTE", "TNE-BEL", "GLS-BEL", "METL-CHM", "RING-BL", "TIN-BEL"
    ],
    "brass": [
        "BRASS 1", "SYN-BRS", "HORNS", "TRUMPET", "FANFARE", "POLY-BRS", "BRASS-ST",
        "MELLOW-B", "WM-BRS", "HI-BRS", "FR-HORN", "STB-BRS", "POW-BRS", "BRS-SEC", "MUT-BRS"
    ],
    "pluck": [
        "KOTO", "KALIMBA", "HARP", "PLUCK-1", "SITAR", "ZITHER", "PIZZ-STR", "MET-PLK",
        "GUIT-FM", "RAZOR-PLK", "MNDLN", "STNG-PK", "BJO-FM", "HRPS-PK", "SHRP-PK"
    ],
    "fx": [
        "COSMIC", "WARP.FX", "ALIEN", "RISE", "DROP.FX", "CYBER", "LZR", "NOISE.X",
        "GLITCH", "VRTX", "DRONE", "ZAP-FX", "SWEEP", "ALRM", "RAYGUN", "VOX-FX", "BLIP-FX"
    ],
    "random": [
        "DX-SYNTH", "FM-TONE", "MATRIX", "VECTOR", "HYBRID", "SPECTRA", "QUANTUM",
        "CYBER", "CHROMA", "SONIC", "NEXUS", "PRSM", "FLUX", "PULSE", "VIBE", "ORBIT"
    ],
}

PROFILE_ADJECTIVES: Dict[str, List[str]] = {
    "warm": [
        "WM", "ANALOG", "MLW", "DEEP", "FAT", "RICH", "SMOOTH", "TUBE",
        "VNTG", "DK-WM", "LSH-WM", "GLOW", "WOOL"
    ],
    "atonal": [
        "ATONAL", "MTL", "CLANG", "NOISE", "MRZBW", "HIT", "PERC", "RNG",
        "DSNT", "INHRM", "RAW-NZ", "ZAP", "METL", "CLST"
    ],
    "crisp": [
        "CRISP", "GLASS", "CRYSTAL", "BRIGHT", "RAZOR", "ICE", "CLEAN", "COLD",
        "PURE", "DIGI", "HYPER", "SPARK", "SHARP", "GLNT", "SHN"
    ],
    "gritty": [
        "GRITTY", "DIRTY", "DRIVE", "RAW", "BITE", "FUZZ", "PUNCH", "ACID",
        "CRNCH", "EDGE", "AGGR", "HARD", "DIST", "TOXIC", "RUST"
    ],
    "ethereal": [
        "ETHER", "AURA", "SPACE", "DREAM", "DRIFT", "VOID", "LUSH", "SOLAR",
        "ASTR", "NBLA", "MYST", "GLOW", "COSM", "HAZE"
    ],
}

ADJECTIVES: List[str] = [
    "WM", "COLD", "DARK", "BRGHT", "LUSH", "HARD", "SOFT", "DEEP",
    "PURE", "RAW", "SILK", "NEO", "VNTG", "RETRO", "MEGA", "HYPR",
    "SWT", "FAT", "THIN", "CRISP", "SLOW", "FAST", "ACID", "GLAS",
    "SOLAR", "LUNAR", "POLY", "MONO", "FM", "DX", "DIGI", "CYBER",
    "SHRP", "AIRY", "DENSE", "HVY", "MUTNT", "REZ", "TOXIC", "ASTR",
    "GLD", "DRTY", "GRTY", "CHRM", "FLUX", "VIBE", "DRFT", "FST",
    "SLW", "SMTH", "MLW", "NOIR", "ELEC", "HYBD", "PRSM", "VOID",
    "NBLA", "GLOW", "SHN", "ICE", "RUST"
]

NOUNS: List[str] = [
    "PNO", "B", "PD", "LEAD", "BELL", "BRS", "PLK", "STRNG", "STRNGS",
    "FLT", "REED", "ORGN", "HORN", "VOX", "WAVE", "PULS", "TONE",
    "CHM", "VIBE", "TINE", "CLAV", "WOOD", "MTL", "WIND", "SYN",
    "SWP", "AURA", "SPCE", "DRM", "STRK", "FRC", "ECHO", "BEAT",
    "DRUM", "K", "SN", "TOM", "HIT", "CLNG", "CYMB", "ZAP",
    "NOIZ", "DROP", "RISR", "SHK", "GLCH", "TXTR", "CLST", "KOTO",
    "KLMB", "SITR", "CHOR", "GONG", "PRC", "SLAP", "STAB", "BLIP",
    "DRON", "PULZ", "FLAR", "ZONE", "RAY", "GLNT", "CHRD", "VOICE",
    "BASS", "TIN", "TUB", "SAW", "SQR", "PIANO", "BRASS", "PLUCK", "FLUTE"
]

SHORT_PREFIXES: List[str] = [
    "DX", "FM", "HI", "LO", "80S", "PRO", "NEO", "BIG", "DRY", "WET",
    "DK", "WM", "RAW", "REZ", "SUB", "FAT", "VNT", "DIG", "FX", "HOT"
]

SUFFIX_TAGS: List[str] = [
    "I", "II", "III", "IV", "V", "VI", "VII", "1", "2", "3", "4", "5",
    "6", "7", "8", "9", "0", "A", "B", "C", "D", "E", "F", "G", "H",
    "V", "W", "X", "Y", "Z", "DX", "FM", "86", "88", "303", "808", "909", "MAX", "PRO"
]


def disemvowel(word: str, max_len: int) -> str:
    """
    Squeeze a word down to `max_len` by removing internal vowels if necessary,
    while preserving the first letter.
    """
    if len(word) <= max_len:
        return word
    vowels = set("AEIOU")
    # Preserve first char, remove subsequent vowels
    chars = [word[0]]
    for c in word[1:]:
        if c not in vowels or len(chars) < 2:
            chars.append(c)
        if len(chars) == max_len:
            break
    result = "".join(chars)
    return result[:max_len]


class PatchNamer:
    """
    Generator for authentic 10-character DX7 patch names.
    """

    @staticmethod
    def generate(
        category: str = "random",
        rng: Optional[random.Random] = None,
        style: Optional[str] = None,
        profile: Optional[str] = None,
    ) -> str:
        """
        Generate a strictly 10-character DX7 patch name.
        """
        r = rng if rng is not None else random.Random()
        cat = category.lower().strip()

        if style:
            # Custom style string as base
            base = style.upper()
            suffix = str(r.randint(1, 99))
            combined = f"{base} {suffix}"
            return combined[:10].ljust(10, " ")

        mode = r.randint(0, 4)

        if profile and profile.lower() in PROFILE_ADJECTIVES and r.random() < 0.65:
            # Profile-directed naming (e.g. WM PD, ATONAL CLANG, MRZBW HIT)
            p_adj = r.choice(PROFILE_ADJECTIVES[profile.lower()])
            noun = r.choice(NOUNS)
            raw_name = f"{p_adj} {noun}"
        elif mode == 0 and cat in CATEGORY_PREFIXES:
            # Category prefix + tag/number
            base = r.choice(CATEGORY_PREFIXES[cat])
            tag = r.choice(["1", "2", "3", "7", "8", "9", "I", "II", "A", "B", "X", "DX", "FM"])
            if len(base) + 1 + len(tag) <= 10:
                raw_name = f"{base} {tag}"
            else:
                raw_name = base
        elif mode == 1:
            # ADJECTIVE + NOUN
            adj = r.choice(ADJECTIVES)
            noun = r.choice(NOUNS)
            raw_name = f"{adj} {noun}"
        elif mode == 2 and cat in CATEGORY_PREFIXES:
            # SHORT MODIFIER + CATEGORY PREFIX
            adj = r.choice(SHORT_PREFIXES)
            base = r.choice(CATEGORY_PREFIXES[cat])
            if len(adj) + 1 + len(base) <= 10:
                raw_name = f"{adj} {base}"
            else:
                # Squeeze base
                squeezed_base = disemvowel(base, 10 - len(adj) - 1)
                raw_name = f"{adj} {squeezed_base}"
        elif mode == 3:
            # NOUN + SUFFIX TAG
            noun = r.choice(NOUNS)
            tag = r.choice(SUFFIX_TAGS)
            raw_name = f"{noun} {tag}"
        else:
            # ADJECTIVE + SHORT NOUN
            adj = r.choice(ADJECTIVES)
            noun = r.choice(NOUNS)
            raw_name = f"{adj} {noun}"

        # If combined raw_name is too long, intelligently squeeze the parts
        if len(raw_name) > 10:
            parts = raw_name.split()
            if len(parts) == 2:
                w1, w2 = parts
                # Squeeze word 2 first, then word 1 if needed
                w2_squeezed = disemvowel(w2, 10 - len(w1) - 1)
                if len(w1) + 1 + len(w2_squeezed) <= 10:
                    raw_name = f"{w1} {w2_squeezed}"
                else:
                    w1_squeezed = disemvowel(w1, 4)
                    w2_squeezed = disemvowel(w2, 10 - len(w1_squeezed) - 1)
                    raw_name = f"{w1_squeezed} {w2_squeezed}"

        # Sanitize to exactly 10 valid ASCII characters
        clean = "".join(c if 32 <= ord(c) <= 126 else " " for c in raw_name.upper())
        return clean[:10].ljust(10, " ")
