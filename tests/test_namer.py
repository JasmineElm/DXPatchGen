"""
Tests for 10-character DX7 patch namer.
"""

import random
from dxpatchgen.generator.namer import PatchNamer


def test_namer_length_and_valid_ascii():
    rng = random.Random(42)
    categories = ["keys", "bass", "pad", "lead", "bell", "brass", "pluck", "fx", "random"]

    for cat in categories:
        for _ in range(20):
            name = PatchNamer.generate(category=cat, rng=rng)
            assert len(name) == 10, f"Expected 10 chars, got '{name}' (len {len(name)})"
            # Ensure valid ASCII printable characters
            for char in name:
                assert 32 <= ord(char) <= 126


def test_namer_with_custom_style():
    rng = random.Random(7)
    name = PatchNamer.generate(rng=rng, style="CYBER")
    assert len(name) == 10
    assert name.startswith("CYBER")
