"""
Yamaha DX7 SysEx encoding, decoding, checksum calculation, and file I/O.
Supports single-voice SysEx (163 bytes / 155 bytes / 128 bytes) and 32-voice banks (4104 bytes / 4096 bytes).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple, Union

from dxpatchgen.core.models import DX7Patch, Operator, PitchEG, LFO


SYSEX_START = 0xF0
SYSEX_END = 0xF7
YAMAHA_ID = 0x43

SINGLE_VOICE_FORMAT = 0x00
BANK_FORMAT = 0x09


def calculate_checksum(data: Union[bytes, bytearray, Sequence[int]]) -> int:
    """
    Calculate 7-bit two's complement checksum for Yamaha SysEx bulk dumps.
    checksum = (-sum(data)) & 0x7F
    """
    total = sum(data)
    return (-total) & 0x7F


def pack_voice_128(patch: DX7Patch) -> bytes:
    """
    Pack a DX7Patch into the standard 128-byte packed format (used in 32-voice banks).
    Operators are stored in order: OP6 down to OP1.
    """
    buf = bytearray(128)

    # 6 operators in reverse order: OP6 (idx 5), OP5 (idx 4) ... OP1 (idx 0)
    for op_idx in range(6):
        op_num = 6 - op_idx  # 6, 5, 4, 3, 2, 1
        op = patch.op(op_num)
        base = op_idx * 17

        buf[base + 0] = op.eg_rate_1 & 0x7F
        buf[base + 1] = op.eg_rate_2 & 0x7F
        buf[base + 2] = op.eg_rate_3 & 0x7F
        buf[base + 3] = op.eg_rate_4 & 0x7F
        buf[base + 4] = op.eg_level_1 & 0x7F
        buf[base + 5] = op.eg_level_2 & 0x7F
        buf[base + 6] = op.eg_level_3 & 0x7F
        buf[base + 7] = op.eg_level_4 & 0x7F
        buf[base + 8] = op.break_point & 0x7F
        buf[base + 9] = op.left_depth & 0x7F
        buf[base + 10] = op.right_depth & 0x7F
        buf[base + 11] = ((op.right_curve & 0x03) << 2) | (op.left_curve & 0x03)
        buf[base + 12] = ((op.detune & 0x0F) << 3) | (op.rate_scaling & 0x07)
        buf[base + 13] = ((op.key_vel_sens & 0x07) << 2) | (op.amp_mod_sens & 0x03)
        buf[base + 14] = op.output_level & 0x7F
        buf[base + 15] = ((op.freq_coarse & 0x1F) << 1) | (op.osc_mode & 0x01)
        buf[base + 16] = op.freq_fine & 0x7F

    # Common parameters (offset 102 to 127)
    buf[102] = patch.pitch_eg.rate_1 & 0x7F
    buf[103] = patch.pitch_eg.rate_2 & 0x7F
    buf[104] = patch.pitch_eg.rate_3 & 0x7F
    buf[105] = patch.pitch_eg.rate_4 & 0x7F
    buf[106] = patch.pitch_eg.level_1 & 0x7F
    buf[107] = patch.pitch_eg.level_2 & 0x7F
    buf[108] = patch.pitch_eg.level_3 & 0x7F
    buf[109] = patch.pitch_eg.level_4 & 0x7F
    buf[110] = patch.algorithm_0indexed & 0x1F
    buf[111] = ((patch.key_sync & 0x01) << 3) | (patch.feedback & 0x07)
    buf[112] = patch.lfo.speed & 0x7F
    buf[113] = patch.lfo.delay & 0x7F
    buf[114] = patch.lfo.pitch_mod_depth & 0x7F
    buf[115] = patch.lfo.amp_mod_depth & 0x7F
    buf[116] = (
        ((patch.lfo.pitch_mod_sens & 0x07) << 4)
        | ((patch.lfo.waveform & 0x07) << 1)
        | (patch.lfo.key_sync & 0x01)
    )
    buf[117] = patch.transpose & 0x7F

    # Name: 10 ASCII characters
    name_bytes = patch.name.encode("ascii", errors="replace")[:10].ljust(10, b" ")
    buf[118:128] = name_bytes

    return bytes(buf)


def unpack_voice_128(data: Union[bytes, bytearray, Sequence[int]], offset: int = 0) -> DX7Patch:
    """
    Unpack a 128-byte packed voice binary into a DX7Patch object.
    """
    if len(data) < offset + 128:
        raise ValueError(
            f"Expected at least {offset + 128} bytes for packed voice, got {len(data)}"
        )

    chunk = data[offset : offset + 128]
    operators: List[Operator] = [Operator() for _ in range(6)]

    # Operators OP6 down to OP1
    for op_idx in range(6):
        op_num = 6 - op_idx  # 6, 5, 4, 3, 2, 1
        base = op_idx * 17

        b11 = chunk[base + 11]
        b12 = chunk[base + 12]
        b13 = chunk[base + 13]
        b15 = chunk[base + 15]

        op = Operator(
            eg_rate_1=chunk[base + 0] & 0x7F,
            eg_rate_2=chunk[base + 1] & 0x7F,
            eg_rate_3=chunk[base + 2] & 0x7F,
            eg_rate_4=chunk[base + 3] & 0x7F,
            eg_level_1=chunk[base + 4] & 0x7F,
            eg_level_2=chunk[base + 5] & 0x7F,
            eg_level_3=chunk[base + 6] & 0x7F,
            eg_level_4=chunk[base + 7] & 0x7F,
            break_point=chunk[base + 8] & 0x7F,
            left_depth=chunk[base + 9] & 0x7F,
            right_depth=chunk[base + 10] & 0x7F,
            left_curve=b11 & 0x03,
            right_curve=(b11 >> 2) & 0x03,
            rate_scaling=b12 & 0x07,
            detune=(b12 >> 3) & 0x0F,
            amp_mod_sens=b13 & 0x03,
            key_vel_sens=(b13 >> 2) & 0x07,
            output_level=chunk[base + 14] & 0x7F,
            osc_mode=b15 & 0x01,
            freq_coarse=(b15 >> 1) & 0x1F,
            freq_fine=chunk[base + 16] & 0x7F,
        )
        operators[op_num - 1] = op

    # Pitch EG
    pitch_eg = PitchEG(
        rate_1=chunk[102] & 0x7F,
        rate_2=chunk[103] & 0x7F,
        rate_3=chunk[104] & 0x7F,
        rate_4=chunk[105] & 0x7F,
        level_1=chunk[106] & 0x7F,
        level_2=chunk[107] & 0x7F,
        level_3=chunk[108] & 0x7F,
        level_4=chunk[109] & 0x7F,
    )

    # Common
    alg_0 = chunk[110] & 0x1F
    b111 = chunk[111]
    feedback = b111 & 0x07
    key_sync = (b111 >> 3) & 0x01

    b116 = chunk[116]
    lfo = LFO(
        speed=chunk[112] & 0x7F,
        delay=chunk[113] & 0x7F,
        pitch_mod_depth=chunk[114] & 0x7F,
        amp_mod_depth=chunk[115] & 0x7F,
        key_sync=b116 & 0x01,
        waveform=(b116 >> 1) & 0x07,
        pitch_mod_sens=(b116 >> 4) & 0x07,
    )

    transpose = chunk[117] & 0x7F
    raw_name = bytes(chunk[118:128])
    name = raw_name.decode("ascii", errors="replace")

    return DX7Patch(
        name=name,
        operators=operators,
        pitch_eg=pitch_eg,
        lfo=lfo,
        algorithm=alg_0 + 1,
        feedback=feedback,
        key_sync=key_sync,
        transpose=transpose,
    )


def pack_voice_155(patch: DX7Patch) -> bytes:
    """
    Pack a DX7Patch into the standard 155-byte unpacked format (used in 1-voice bulk dumps).
    Parameters are 1 byte per parameter.
    """
    buf = bytearray(155)

    # 6 operators: OP6 down to OP1 (21 parameters each = 126 bytes)
    for op_idx in range(6):
        op_num = 6 - op_idx
        op = patch.op(op_num)
        base = op_idx * 21

        buf[base + 0] = op.eg_rate_1 & 0x7F
        buf[base + 1] = op.eg_rate_2 & 0x7F
        buf[base + 2] = op.eg_rate_3 & 0x7F
        buf[base + 3] = op.eg_rate_4 & 0x7F
        buf[base + 4] = op.eg_level_1 & 0x7F
        buf[base + 5] = op.eg_level_2 & 0x7F
        buf[base + 6] = op.eg_level_3 & 0x7F
        buf[base + 7] = op.eg_level_4 & 0x7F
        buf[base + 8] = op.break_point & 0x7F
        buf[base + 9] = op.left_depth & 0x7F
        buf[base + 10] = op.right_depth & 0x7F
        buf[base + 11] = op.left_curve & 0x03
        buf[base + 12] = op.right_curve & 0x03
        buf[base + 13] = op.rate_scaling & 0x07
        buf[base + 14] = op.amp_mod_sens & 0x03
        buf[base + 15] = op.key_vel_sens & 0x07
        buf[base + 16] = op.output_level & 0x7F
        buf[base + 17] = op.osc_mode & 0x01
        buf[base + 18] = op.freq_coarse & 0x1F
        buf[base + 19] = op.freq_fine & 0x7F
        buf[base + 20] = op.detune & 0x0F

    # 29 common parameters (offset 126 to 154)
    buf[126] = patch.pitch_eg.rate_1 & 0x7F
    buf[127] = patch.pitch_eg.rate_2 & 0x7F
    buf[128] = patch.pitch_eg.rate_3 & 0x7F
    buf[129] = patch.pitch_eg.rate_4 & 0x7F
    buf[130] = patch.pitch_eg.level_1 & 0x7F
    buf[131] = patch.pitch_eg.level_2 & 0x7F
    buf[132] = patch.pitch_eg.level_3 & 0x7F
    buf[133] = patch.pitch_eg.level_4 & 0x7F
    buf[134] = patch.algorithm_0indexed & 0x1F
    buf[135] = patch.feedback & 0x07
    buf[136] = patch.key_sync & 0x01
    buf[137] = patch.lfo.speed & 0x7F
    buf[138] = patch.lfo.delay & 0x7F
    buf[139] = patch.lfo.pitch_mod_depth & 0x7F
    buf[140] = patch.lfo.amp_mod_depth & 0x7F
    buf[141] = patch.lfo.key_sync & 0x01
    buf[142] = patch.lfo.waveform & 0x07
    buf[143] = patch.lfo.pitch_mod_sens & 0x07
    buf[144] = patch.transpose & 0x7F

    # Name
    name_bytes = patch.name.encode("ascii", errors="replace")[:10].ljust(10, b" ")
    buf[145:155] = name_bytes

    return bytes(buf)


def unpack_voice_155(data: Union[bytes, bytearray, Sequence[int]], offset: int = 0) -> DX7Patch:
    """
    Unpack a 155-byte raw parameter voice buffer into a DX7Patch object.
    """
    if len(data) < offset + 155:
        raise ValueError(
            f"Expected at least {offset + 155} bytes for 155-byte voice, got {len(data)}"
        )

    chunk = data[offset : offset + 155]
    operators: List[Operator] = [Operator() for _ in range(6)]

    for op_idx in range(6):
        op_num = 6 - op_idx
        base = op_idx * 21

        op = Operator(
            eg_rate_1=chunk[base + 0] & 0x7F,
            eg_rate_2=chunk[base + 1] & 0x7F,
            eg_rate_3=chunk[base + 2] & 0x7F,
            eg_rate_4=chunk[base + 3] & 0x7F,
            eg_level_1=chunk[base + 4] & 0x7F,
            eg_level_2=chunk[base + 5] & 0x7F,
            eg_level_3=chunk[base + 6] & 0x7F,
            eg_level_4=chunk[base + 7] & 0x7F,
            break_point=chunk[base + 8] & 0x7F,
            left_depth=chunk[base + 9] & 0x7F,
            right_depth=chunk[base + 10] & 0x7F,
            left_curve=chunk[base + 11] & 0x03,
            right_curve=chunk[base + 12] & 0x03,
            rate_scaling=chunk[base + 13] & 0x07,
            amp_mod_sens=chunk[base + 14] & 0x03,
            key_vel_sens=chunk[base + 15] & 0x07,
            output_level=chunk[base + 16] & 0x7F,
            osc_mode=chunk[base + 17] & 0x01,
            freq_coarse=chunk[base + 18] & 0x1F,
            freq_fine=chunk[base + 19] & 0x7F,
            detune=chunk[base + 20] & 0x0F,
        )
        operators[op_num - 1] = op

    pitch_eg = PitchEG(
        rate_1=chunk[126] & 0x7F,
        rate_2=chunk[127] & 0x7F,
        rate_3=chunk[128] & 0x7F,
        rate_4=chunk[129] & 0x7F,
        level_1=chunk[130] & 0x7F,
        level_2=chunk[131] & 0x7F,
        level_3=chunk[132] & 0x7F,
        level_4=chunk[133] & 0x7F,
    )

    alg_0 = chunk[134] & 0x1F
    feedback = chunk[135] & 0x07
    key_sync = chunk[136] & 0x01

    lfo = LFO(
        speed=chunk[137] & 0x7F,
        delay=chunk[138] & 0x7F,
        pitch_mod_depth=chunk[139] & 0x7F,
        amp_mod_depth=chunk[140] & 0x7F,
        key_sync=chunk[141] & 0x01,
        waveform=chunk[142] & 0x07,
        pitch_mod_sens=chunk[143] & 0x07,
    )

    transpose = chunk[144] & 0x7F
    raw_name = bytes(chunk[145:155])
    name = raw_name.decode("ascii", errors="replace")

    return DX7Patch(
        name=name,
        operators=operators,
        pitch_eg=pitch_eg,
        lfo=lfo,
        algorithm=alg_0 + 1,
        feedback=feedback,
        key_sync=key_sync,
        transpose=transpose,
    )


def encode_single_voice_sysex(patch: DX7Patch, midi_channel: int = 0) -> bytes:
    """
    Encode a single DX7 voice into a standard 163-byte SysEx message.
    Header: F0 43 (0n) 00 01 1B [155 bytes data] [chk] F7
    """
    channel_byte = midi_channel & 0x0F
    data = pack_voice_155(patch)
    checksum = calculate_checksum(data)

    header = bytes([SYSEX_START, YAMAHA_ID, channel_byte, SINGLE_VOICE_FORMAT, 0x01, 0x1B])
    footer = bytes([checksum, SYSEX_END])

    return header + data + footer


def decode_single_voice_sysex(syx_bytes: bytes) -> DX7Patch:
    """
    Decode a single voice from SysEx (163 bytes) or raw parameter data (155 or 128 bytes).
    """
    # 163-byte standard 1-voice SysEx dump
    if len(syx_bytes) == 163 and syx_bytes[0] == SYSEX_START and syx_bytes[-1] == SYSEX_END:
        data = syx_bytes[6:161]
        return unpack_voice_155(data)

    # 155-byte raw unpacked dump
    if len(syx_bytes) == 155:
        return unpack_voice_155(syx_bytes)

    # 128-byte raw packed voice
    if len(syx_bytes) == 128:
        return unpack_voice_128(syx_bytes)

    # Generic SysEx search for 1-voice format header
    if len(syx_bytes) > 163:
        idx = syx_bytes.find(bytes([SYSEX_START, YAMAHA_ID]))
        if idx != -1 and len(syx_bytes) >= idx + 163:
            return unpack_voice_155(syx_bytes[idx + 6 : idx + 161])

    raise ValueError(f"Unrecognized single voice SysEx format of length {len(syx_bytes)}")


def encode_bank_sysex(patches: Sequence[DX7Patch], midi_channel: int = 0) -> bytes:
    """
    Encode a 32-voice bank into a standard 4104-byte SysEx message.
    Header: F0 43 (0n) 09 20 00 [4096 bytes data] [chk] F7
    """
    if len(patches) != 32:
        raise ValueError(f"DX7 bank must contain exactly 32 patches, got {len(patches)}")

    channel_byte = midi_channel & 0x0F
    data_buf = bytearray()
    for patch in patches:
        data_buf.extend(pack_voice_128(patch))

    data_bytes = bytes(data_buf)
    checksum = calculate_checksum(data_bytes)

    header = bytes([SYSEX_START, YAMAHA_ID, channel_byte, BANK_FORMAT, 0x20, 0x00])
    footer = bytes([checksum, SYSEX_END])

    return header + data_bytes + footer


def decode_bank_sysex(syx_bytes: bytes) -> List[DX7Patch]:
    """
    Decode a 32-voice bank from SysEx (4104 bytes) or raw 4096-byte bank dump.
    """
    data_slice: bytes

    # 4104-byte standard bank SysEx message
    if len(syx_bytes) == 4104 and syx_bytes[0] == SYSEX_START and syx_bytes[-1] == SYSEX_END:
        data_slice = syx_bytes[6:4102]
    elif len(syx_bytes) == 4096:
        data_slice = syx_bytes
    else:
        # Search for bank header
        idx = syx_bytes.find(bytes([SYSEX_START, YAMAHA_ID]))
        if idx != -1 and len(syx_bytes) >= idx + 4104:
            data_slice = syx_bytes[idx + 6 : idx + 4102]
        else:
            raise ValueError(f"Unrecognized 32-voice bank SysEx length {len(syx_bytes)}")

    patches: List[DX7Patch] = []
    for i in range(32):
        patch = unpack_voice_128(data_slice, offset=i * 128)
        patches.append(patch)

    return patches


def read_sysex(file_path: Union[str, Path]) -> Union[DX7Patch, List[DX7Patch]]:
    """
    Read a `.syx` file and return either a single DX7Patch or a List[DX7Patch] (if 32-voice bank).
    """
    path = Path(file_path)
    raw_data = path.read_bytes()

    if len(raw_data) in (4104, 4096):
        return decode_bank_sysex(raw_data)
    elif len(raw_data) in (163, 155, 128):
        return decode_single_voice_sysex(raw_data)
    elif len(raw_data) > 163:
        # Check format byte in header
        if len(raw_data) >= 6 and raw_data[0] == SYSEX_START and raw_data[1] == YAMAHA_ID:
            format_num = raw_data[3]
            if format_num == BANK_FORMAT:
                return decode_bank_sysex(raw_data)
            elif format_num == SINGLE_VOICE_FORMAT:
                return decode_single_voice_sysex(raw_data)
        # Fallback attempts
        try:
            return decode_single_voice_sysex(raw_data)
        except Exception:
            return decode_bank_sysex(raw_data)

    raise ValueError(f"Cannot identify DX7 SysEx format in file {file_path} (size: {len(raw_data)} bytes)")


def write_sysex(
    patch_or_patches: Union[DX7Patch, Sequence[DX7Patch]],
    file_path: Union[str, Path],
    midi_channel: int = 0,
) -> Path:
    """
    Write a single patch or a 32-voice bank to a .syx file.
    Returns the Path object of written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(patch_or_patches, DX7Patch):
        syx_data = encode_single_voice_sysex(patch_or_patches, midi_channel=midi_channel)
    elif isinstance(patch_or_patches, (list, tuple)):
        if len(patch_or_patches) == 1:
            syx_data = encode_single_voice_sysex(patch_or_patches[0], midi_channel=midi_channel)
        elif len(patch_or_patches) == 32:
            syx_data = encode_bank_sysex(patch_or_patches, midi_channel=midi_channel)
        else:
            raise ValueError(
                f"Can only save 1 patch or a 32-patch bank (got {len(patch_or_patches)} patches)"
            )
    else:
        raise TypeError(f"Expected DX7Patch or sequence of DX7Patch, got {type(patch_or_patches)}")

    path.write_bytes(syx_data)
    return path
