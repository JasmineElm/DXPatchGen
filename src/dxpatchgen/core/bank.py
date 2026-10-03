"""
DX7 32-Voice Bank management.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional, Sequence, Union

from dxpatchgen.core.models import DX7Patch
from dxpatchgen.core.sysex import decode_bank_sysex, encode_bank_sysex, read_sysex, write_sysex


class DX7Bank:
    """
    Represents a full 32-voice bank for Yamaha DX7.
    """

    BANK_SIZE = 32

    def __init__(self, patches: Optional[Sequence[DX7Patch]] = None) -> None:
        self._patches: List[DX7Patch] = []
        if patches:
            for i, patch in enumerate(patches[: self.BANK_SIZE]):
                self._patches.append(patch.copy())

        # Pad remaining slots with default init voices if less than 32
        while len(self._patches) < self.BANK_SIZE:
            idx = len(self._patches) + 1
            self._patches.append(DX7Patch(name=f"INIT VOIC{idx:02d}"))

    def __len__(self) -> int:
        return self.BANK_SIZE

    def __getitem__(self, index: int) -> DX7Patch:
        """0-based or 1-based index access. If 1..32, converts to 0..31."""
        if 1 <= index <= 32:
            return self._patches[index - 1]
        elif 0 <= index < 32:
            return self._patches[index]
        raise IndexError(f"Bank index out of range (1-32 or 0-31): {index}")

    def __setitem__(self, index: int, patch: DX7Patch) -> None:
        if not isinstance(patch, DX7Patch):
            raise TypeError(f"Expected DX7Patch, got {type(patch)}")
        if 1 <= index <= 32:
            self._patches[index - 1] = patch.copy()
        elif 0 <= index < 32:
            self._patches[index] = patch.copy()
        else:
            raise IndexError(f"Bank index out of range: {index}")

    def __iter__(self) -> Iterator[DX7Patch]:
        return iter(self._patches)

    @property
    def patches(self) -> List[DX7Patch]:
        """Return list of all 32 patches in the bank."""
        return list(self._patches)

    def set_patch(self, slot: int, patch: DX7Patch) -> None:
        """Set patch at 1-based slot (1..32)."""
        self[slot] = patch

    def get_patch(self, slot: int) -> DX7Patch:
        """Get patch at 1-based slot (1..32)."""
        return self[slot]

    @classmethod
    def load(cls, file_path: Union[str, Path]) -> DX7Bank:
        """Load bank from a .syx file."""
        res = read_sysex(file_path)
        if isinstance(res, list):
            return cls(patches=res)
        elif isinstance(res, DX7Patch):
            bank = cls()
            bank[1] = res
            return bank
        raise ValueError(f"Could not load bank from {file_path}")

    def save(self, file_path: Union[str, Path], midi_channel: int = 0) -> Path:
        """Save bank to a 4104-byte .syx file."""
        return write_sysex(self._patches, file_path, midi_channel=midi_channel)
