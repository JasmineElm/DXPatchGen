"""
Tests for DX7 32 algorithms topology and metadata.
"""

import pytest
from dxpatchgen.core.algorithms import (
    ALGORITHMS,
    get_algorithm,
    is_carrier,
    get_carrier_ops,
    get_modulator_ops,
)


def test_all_32_algorithms_defined():
    assert len(ALGORITHMS) == 32
    for alg_id in range(1, 33):
        alg = get_algorithm(alg_id)
        assert alg.id == alg_id
        assert len(alg.carriers) >= 1
        assert 1 <= alg.feedback_op <= 6
        assert len(alg.ascii_diagram) > 0
        assert len(alg.description) > 0

        # Carriers + Modulators should form set of 1..6
        all_ops = set(alg.carriers) | set(alg.modulators)
        assert all_ops == {1, 2, 3, 4, 5, 6}
        assert set(alg.carriers).isdisjoint(set(alg.modulators))


def test_algorithm_helpers():
    # Alg 1: Carriers are 1 and 3
    assert is_carrier(1, 1) is True
    assert is_carrier(1, 3) is True
    assert is_carrier(1, 2) is False
    assert is_carrier(1, 6) is False

    assert get_carrier_ops(1) == (1, 3)
    assert set(get_modulator_ops(1)) == {2, 4, 5, 6}

    # Alg 32: All 6 are carriers
    assert len(get_carrier_ops(32)) == 6
    assert len(get_modulator_ops(32)) == 0


def test_invalid_algorithm_id():
    with pytest.raises(ValueError):
        get_algorithm(0)
    with pytest.raises(ValueError):
        get_algorithm(33)
