"""
Tests for DX7Bank class.
"""

from pathlib import Path
import pytest
from dxpatchgen.core.bank import DX7Bank
from dxpatchgen.core.models import DX7Patch


def test_bank_init_and_size():
    bank = DX7Bank()
    assert len(bank) == 32
    assert bank[1].name.startswith("INIT VOIC")
    assert bank[32].name.startswith("INIT VOIC")


def test_bank_indexing_and_iteration():
    bank = DX7Bank()
    patch = DX7Patch(name="CUSTOM 01")
    bank[1] = patch
    assert bank[1].name.strip() == "CUSTOM 01"

    count = 0
    for p in bank:
        assert isinstance(p, DX7Patch)
        count += 1
    assert count == 32


def test_bank_save_and_load(tmp_path: Path):
    bank = DX7Bank()
    bank[1] = DX7Patch(name="MY LEAD", algorithm=16)
    bank[32] = DX7Patch(name="MY BASS", algorithm=1)

    file_path = tmp_path / "bank.syx"
    bank.save(file_path)

    loaded = DX7Bank.load(file_path)
    assert len(loaded) == 32
    assert loaded[1].name.strip() == "MY LEAD"
    assert loaded[1].algorithm == 16
    assert loaded[32].name.strip() == "MY BASS"
    assert loaded[32].algorithm == 1
