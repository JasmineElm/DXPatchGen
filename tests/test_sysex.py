"""
Tests for Yamaha DX7 SysEx encoding, decoding, checksums, and file I/O.
"""

from pathlib import Path
import pytest

from dxpatchgen.core.models import DX7Patch, Operator, PitchEG, LFO
from dxpatchgen.core.sysex import (
    calculate_checksum,
    pack_voice_128,
    unpack_voice_128,
    pack_voice_155,
    unpack_voice_155,
    encode_single_voice_sysex,
    decode_single_voice_sysex,
    encode_bank_sysex,
    decode_bank_sysex,
    read_sysex,
    write_sysex,
)


def create_sample_patch() -> DX7Patch:
    """Create a test patch with known distinctive parameters."""
    patch = DX7Patch(
        name="TEST PATCH",
        algorithm=7,
        feedback=5,
        key_sync=1,
        transpose=24,
    )
    # Customize OP1
    patch.op(1).output_level = 95
    patch.op(1).freq_coarse = 1
    patch.op(1).freq_fine = 25
    patch.op(1).detune = 9  # +2
    patch.op(1).eg_rate_1 = 88
    patch.op(1).eg_level_2 = 72
    patch.op(1).key_vel_sens = 4

    # Customize OP6
    patch.op(6).output_level = 78
    patch.op(6).freq_coarse = 5
    patch.op(6).freq_fine = 10
    patch.op(6).detune = 5  # -2
    patch.op(6).osc_mode = 0

    # LFO
    patch.lfo.speed = 42
    patch.lfo.waveform = 3  # Square

    # Pitch EG
    patch.pitch_eg.rate_1 = 80
    patch.pitch_eg.level_1 = 55

    return patch


def test_checksum_calculation():
    # Sum of bytes modulo 128, two's complement 7-bit
    data = bytes([10, 20, 30])  # sum = 60 => (-60) & 0x7F = 68
    assert calculate_checksum(data) == 68

    zero_data = bytes([128, 0])
    assert calculate_checksum(zero_data) == 0


def test_128_byte_packing_roundtrip():
    original = create_sample_patch()
    packed = pack_voice_128(original)
    assert len(packed) == 128

    restored = unpack_voice_128(packed)

    assert restored.name == original.name
    assert restored.algorithm == original.algorithm
    assert restored.feedback == original.feedback
    assert restored.transpose == original.transpose
    assert restored.key_sync == original.key_sync

    # OP1 check
    assert restored.op(1).output_level == original.op(1).output_level
    assert restored.op(1).freq_coarse == original.op(1).freq_coarse
    assert restored.op(1).freq_fine == original.op(1).freq_fine
    assert restored.op(1).detune == original.op(1).detune
    assert restored.op(1).eg_rate_1 == original.op(1).eg_rate_1
    assert restored.op(1).eg_level_2 == original.op(1).eg_level_2
    assert restored.op(1).key_vel_sens == original.op(1).key_vel_sens

    # OP6 check
    assert restored.op(6).output_level == original.op(6).output_level
    assert restored.op(6).freq_coarse == original.op(6).freq_coarse
    assert restored.op(6).freq_fine == original.op(6).freq_fine
    assert restored.op(6).detune == original.op(6).detune

    # LFO check
    assert restored.lfo.speed == original.lfo.speed
    assert restored.lfo.waveform == original.lfo.waveform

    # Pitch EG check
    assert restored.pitch_eg.rate_1 == original.pitch_eg.rate_1
    assert restored.pitch_eg.level_1 == original.pitch_eg.level_1


def test_155_byte_packing_roundtrip():
    original = create_sample_patch()
    packed = pack_voice_155(original)
    assert len(packed) == 155

    restored = unpack_voice_155(packed)
    assert restored.name == original.name
    assert restored.algorithm == original.algorithm
    assert restored.feedback == original.feedback
    assert restored.op(1).output_level == original.op(1).output_level
    assert restored.op(6).freq_coarse == original.op(6).freq_coarse


def test_single_voice_sysex_message():
    original = create_sample_patch()
    syx = encode_single_voice_sysex(original, midi_channel=0)

    # Standard DX7 1-voice bulk message is 163 bytes
    assert len(syx) == 163
    assert syx[0] == 0xF0
    assert syx[1] == 0x43
    assert syx[2] == 0x00  # MIDI ch 1
    assert syx[3] == 0x00  # Format 00 = 1 voice
    assert syx[4] == 0x01
    assert syx[5] == 0x1B  # 155 bytes
    assert syx[-1] == 0xF7

    restored = decode_single_voice_sysex(syx)
    assert restored.name == original.name
    assert restored.algorithm == original.algorithm
    assert restored.op(1).output_level == original.op(1).output_level


def test_32_voice_bank_sysex_roundtrip(tmp_path: Path):
    patches = [create_sample_patch() for _ in range(32)]
    for i in range(32):
        patches[i].name = f"VOICE {i+1:02d}"

    bank_syx = encode_bank_sysex(patches, midi_channel=0)
    # Standard DX7 32-voice bank message is 4104 bytes
    assert len(bank_syx) == 4104
    assert bank_syx[0] == 0xF0
    assert bank_syx[1] == 0x43
    assert bank_syx[2] == 0x00
    assert bank_syx[3] == 0x09  # Format 09 = 32 voices
    assert bank_syx[4] == 0x20
    assert bank_syx[5] == 0x00  # 4096 bytes
    assert bank_syx[-1] == 0xF7

    decoded_patches = decode_bank_sysex(bank_syx)
    assert len(decoded_patches) == 32
    assert decoded_patches[0].name.strip() == "VOICE 01"
    assert decoded_patches[31].name.strip() == "VOICE 32"

    # Test file I/O
    file_path = tmp_path / "test_bank.syx"
    write_sysex(patches, file_path)
    loaded = read_sysex(file_path)
    assert isinstance(loaded, list)
    assert len(loaded) == 32
    assert loaded[0].name.strip() == "VOICE 01"
