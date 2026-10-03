"""
Tests for DX7 patch generation engines, templates, and mutator.
"""

import pytest
from dxpatchgen.generator.base import GenerationOptions
from dxpatchgen.generator.random import RandomPatchGenerator, ConstrainedRandomGenerator
from dxpatchgen.generator.templates import (
    KeysGenerator,
    BassGenerator,
    PadGenerator,
    BellGenerator,
    LeadGenerator,
    FXGenerator,
    get_generator,
)
from dxpatchgen.generator.mutator import PatchMutator


def test_pure_random_generator():
    gen = RandomPatchGenerator()
    patch = gen.generate()
    assert 1 <= patch.algorithm <= 32
    assert 0 <= patch.feedback <= 7
    assert len(patch.operators) == 6
    assert len(patch.name) == 10


def test_deterministic_seeding():
    gen = ConstrainedRandomGenerator()
    opts1 = GenerationOptions(seed=4242, category="keys")
    opts2 = GenerationOptions(seed=4242, category="keys")

    patch1 = gen.generate(opts1)
    patch2 = gen.generate(opts2)

    assert patch1.name == patch2.name
    assert patch1.algorithm == patch2.algorithm
    assert patch1.feedback == patch2.feedback
    assert patch1.op(1).output_level == patch2.op(1).output_level
    assert patch1.op(1).freq_coarse == patch2.op(1).freq_coarse
    assert patch1.op(6).eg_rate_1 == patch2.op(6).eg_rate_1


def test_constrained_random_forced_algorithm():
    gen = ConstrainedRandomGenerator()
    opts = GenerationOptions(algorithm=16)  # Single 6-op stack
    patch = gen.generate(opts)
    assert patch.algorithm == 16


def test_category_generators():
    categories = ["keys", "bass", "pad", "lead", "bell", "fx"]
    for cat in categories:
        gen = get_generator(cat)
        patch = gen.generate(GenerationOptions(seed=100))
        assert 1 <= patch.algorithm <= 32
        assert len(patch.operators) == 6
        assert len(patch.name) == 10


def test_patch_mutator():
    gen = ConstrainedRandomGenerator()
    original = gen.generate(GenerationOptions(seed=123))

    # Low mutation: should retain algorithm and general character
    mutated = PatchMutator.mutate(original, mutation_rate=0.1, seed=999)
    assert mutated.algorithm == original.algorithm
    assert len(mutated.operators) == 6
    assert mutated.name != original.name or mutated.name.strip() != ""
