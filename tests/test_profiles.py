"""
Tests for Sonic Profile Layer (Warm, Atonal, Crisp, Gritty, Ethereal) and Percussive Generator.
"""

import pytest
from dxpatchgen.core.algorithms import get_algorithm
from dxpatchgen.generator.base import GenerationOptions
from dxpatchgen.generator.profiles import (
    WarmProfile,
    AtonalProfile,
    CrispProfile,
    GrittyProfile,
    EtherealProfile,
    get_profile,
    PROFILE_REGISTRY,
)
from dxpatchgen.generator.templates import (
    PadGenerator,
    PercussiveGenerator,
    KeysGenerator,
    get_generator,
)


def test_profile_registry():
    assert "warm" in PROFILE_REGISTRY
    assert "atonal" in PROFILE_REGISTRY
    assert "crisp" in PROFILE_REGISTRY
    assert "gritty" in PROFILE_REGISTRY
    assert "ethereal" in PROFILE_REGISTRY

    assert isinstance(get_profile("warm"), WarmProfile)
    assert isinstance(get_profile("atonal"), AtonalProfile)
    assert get_profile("none") is None
    assert get_profile(None) is None


def test_warm_profile_pad():
    gen = PadGenerator()
    opts = GenerationOptions(category="pad", profile="warm", seed=100)
    patch = gen.generate(opts)

    # Warm pad uses Algorithm 5 (3x 2-op stacks for lush detuned pairs)
    assert patch.algorithm == 5

    alg_info = get_algorithm(patch.algorithm)
    carrier_set = set(alg_info.carriers)

    # Modulators should have negative exponential curve (-EXP = 1) for analog rolloff
    for op_num in range(1, 7):
        if op_num not in carrier_set:
            op = patch.op(op_num)
            assert op.right_curve == 1  # -EXP
            assert op.right_depth > 0  # rolloff depth applied


def test_atonal_profile_percussive():
    gen = PercussiveGenerator()
    opts = GenerationOptions(category="percussive", profile="atonal", seed=200)
    patch = gen.generate(opts)

    # In atonal mode, multiple operators are set to Fixed Frequency Mode (osc_mode = 1)
    fixed_ops = [op for op in patch.operators if op.osc_mode == 1]
    assert len(fixed_ops) >= 2

    # Fast pitch dive in pitch EG
    assert patch.pitch_eg.rate_1 >= 80
    assert patch.pitch_eg.level_1 != 50


def test_crisp_profile():
    gen = KeysGenerator()
    opts = GenerationOptions(category="keys", profile="crisp", seed=300)
    patch = gen.generate(opts)

    alg_info = get_algorithm(patch.algorithm)
    carrier_set = set(alg_info.carriers)

    # Modulators should have positive scaling (+LIN = 3) for top-end sparkle
    for op_num in range(1, 7):
        if op_num not in carrier_set:
            op = patch.op(op_num)
            assert op.right_curve == 3  # +LIN
            assert op.right_depth > 0


def test_gritty_profile():
    gen = KeysGenerator()
    opts = GenerationOptions(category="keys", profile="gritty", seed=400)
    patch = gen.generate(opts)

    # High feedback saturation
    assert patch.feedback >= 5


def test_ethereal_profile():
    gen = PadGenerator()
    opts = GenerationOptions(category="pad", profile="ethereal", seed=500)
    patch = gen.generate(opts)

    # Slow attack across operators
    for op in patch.operators:
        assert op.eg_rate_1 <= 45

    # LFO should be enabled for lush movement
    assert patch.lfo.pitch_mod_depth > 0
