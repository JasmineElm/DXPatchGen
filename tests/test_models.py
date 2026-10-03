"""
Tests for DX7 core domain models (DX7Patch, Operator, PitchEG, LFO).
"""

import pytest
from dxpatchgen.core.models import DX7Patch, Operator, PitchEG, LFO, clamp


def test_clamp_helper():
    assert clamp(50, 0, 99) == 50
    assert clamp(-5, 0, 99) == 0
    assert clamp(150, 0, 99) == 99


def test_operator_defaults_and_clamping():
    op = Operator(
        eg_rate_1=150,
        eg_level_4=-10,
        break_point=120,
        rate_scaling=10,
        amp_mod_sens=5,
        key_vel_sens=9,
        output_level=105,
        freq_coarse=35,
        freq_fine=110,
        detune=20,
    )
    assert op.eg_rate_1 == 99
    assert op.eg_level_4 == 0
    assert op.break_point == 99
    assert op.rate_scaling == 7
    assert op.amp_mod_sens == 3
    assert op.key_vel_sens == 7
    assert op.output_level == 99
    assert op.freq_coarse == 31
    assert op.freq_fine == 99
    assert op.detune == 14
    assert op.detune_cents == 7


def test_operator_frequency_ratio():
    # Coarse 1, fine 0 => 1.0
    op1 = Operator(freq_coarse=1, freq_fine=0, osc_mode=0)
    assert pytest.approx(op1.frequency_ratio, 0.001) == 1.0

    # Coarse 0 => 0.5 ratio
    op0 = Operator(freq_coarse=0, freq_fine=0, osc_mode=0)
    assert pytest.approx(op0.frequency_ratio, 0.001) == 0.5

    # Coarse 2, fine 50 => 2.0 * 1.5 = 3.0
    op2 = Operator(freq_coarse=2, freq_fine=50, osc_mode=0)
    assert pytest.approx(op2.frequency_ratio, 0.001) == 3.0


def test_patch_initialization_and_access():
    patch = DX7Patch(name="TEST VOICE", algorithm=5, feedback=4, transpose=24)
    assert len(patch.operators) == 6
    assert patch.name == "TEST VOICE"
    assert patch.algorithm == 5
    assert patch.algorithm_0indexed == 4
    assert patch.feedback == 4
    assert patch.transpose_note == "C3"

    # Test 1-based operator access
    op1 = patch.op(1)
    op6 = patch.op(6)
    assert op1 is patch.operators[0]
    assert op6 is patch.operators[5]

    with pytest.raises(IndexError):
        patch.op(0)

    with pytest.raises(IndexError):
        patch.op(7)


def test_patch_name_sanitization():
    # Exactly 10 chars
    assert DX7Patch.sanitize_name("EP 1") == "EP 1      "
    assert len(DX7Patch.sanitize_name("VERY LONG NAME HERE")) == 10
    assert DX7Patch.sanitize_name("VERY LONG NAME HERE") == "VERY LONG "


def test_patch_copy():
    patch = DX7Patch(name="ORIGINAL", algorithm=12)
    patch.op(1).output_level = 77

    copied = patch.copy()
    assert copied.name == "ORIGINAL  "
    assert copied.algorithm == 12
    assert copied.op(1).output_level == 77

    # Mutating copy must not affect original
    copied.name = "MODIFIED"
    copied.op(1).output_level = 99
    assert patch.name == "ORIGINAL  "
    assert patch.op(1).output_level == 77
