"""
Domain models for Yamaha DX7 synthesizer voices and components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence, Tuple


def clamp(val: int, min_val: int, max_val: int) -> int:
    """Clamp an integer value within [min_val, max_val]."""
    return max(min_val, min(val, max_val))


@dataclass
class Operator:
    """
    Represents one of the 6 DX7 FM operators (oscillators).

    All parameters conform to the Yamaha DX7 hardware specifications:
    - Envelope Rates (R1-R4): 0-99
    - Envelope Levels (L1-L4): 0-99
    - Keyboard Level Scaling Breakpoint: 0-99 (0 = A-1, 39 = C3, 99 = C7)
    - Keyboard Level Scaling Depths: 0-99 (Left & Right)
    - Keyboard Level Scaling Curves: 0-3 (0: -LIN, 1: -EXP, 2: +EXP, 3: +LIN)
    - Keyboard Rate Scaling: 0-7
    - Amplitude Modulation Sensitivity: 0-3
    - Key Velocity Sensitivity: 0-7
    - Output Level: 0-99
    - Oscillator Mode: 0 (Frequency/Ratio) or 1 (Fixed Frequency)
    - Frequency Coarse: 0-31 (In ratio mode: 0.5, 1..31)
    - Frequency Fine: 0-99 (0.00 to 0.99 added to coarse ratio)
    - Detune: 0-14 (7 = 0 detune center, 0 = -7, 14 = +7)
    """

    # Envelope Generator (EG) Rates & Levels
    eg_rate_1: int = 99
    eg_rate_2: int = 99
    eg_rate_3: int = 99
    eg_rate_4: int = 99
    eg_level_1: int = 99
    eg_level_2: int = 99
    eg_level_3: int = 99
    eg_level_4: int = 0

    # Keyboard Level Scaling (KLS)
    break_point: int = 39  # C3
    left_depth: int = 0
    right_depth: int = 0
    left_curve: int = 0  # 0: -LIN, 1: -EXP, 2: +EXP, 3: +LIN
    right_curve: int = 0

    # Scaling & Sensitivity
    rate_scaling: int = 0  # 0..7
    amp_mod_sens: int = 0  # 0..3
    key_vel_sens: int = 0  # 0..7

    # Output & Frequency
    output_level: int = 99  # 0..99
    osc_mode: int = 0  # 0 = Ratio, 1 = Fixed
    freq_coarse: int = 1  # 0..31
    freq_fine: int = 0  # 0..99
    detune: int = 7  # 0..14 (7 = 0)

    # UI/Audition state
    enabled: bool = True

    def __post_init__(self) -> None:
        self.clamp_all()

    def clamp_all(self) -> None:
        """Clamp all parameters to valid DX7 ranges."""
        self.eg_rate_1 = clamp(self.eg_rate_1, 0, 99)
        self.eg_rate_2 = clamp(self.eg_rate_2, 0, 99)
        self.eg_rate_3 = clamp(self.eg_rate_3, 0, 99)
        self.eg_rate_4 = clamp(self.eg_rate_4, 0, 99)
        self.eg_level_1 = clamp(self.eg_level_1, 0, 99)
        self.eg_level_2 = clamp(self.eg_level_2, 0, 99)
        self.eg_level_3 = clamp(self.eg_level_3, 0, 99)
        self.eg_level_4 = clamp(self.eg_level_4, 0, 99)

        self.break_point = clamp(self.break_point, 0, 99)
        self.left_depth = clamp(self.left_depth, 0, 99)
        self.right_depth = clamp(self.right_depth, 0, 99)
        self.left_curve = clamp(self.left_curve, 0, 3)
        self.right_curve = clamp(self.right_curve, 0, 3)

        self.rate_scaling = clamp(self.rate_scaling, 0, 7)
        self.amp_mod_sens = clamp(self.amp_mod_sens, 0, 3)
        self.key_vel_sens = clamp(self.key_vel_sens, 0, 7)

        self.output_level = clamp(self.output_level, 0, 99)
        self.osc_mode = clamp(self.osc_mode, 0, 1)
        self.freq_coarse = clamp(self.freq_coarse, 0, 31)
        self.freq_fine = clamp(self.freq_fine, 0, 99)
        self.detune = clamp(self.detune, 0, 14)

    @property
    def frequency_ratio(self) -> float:
        """Calculate effective frequency ratio when in Ratio mode."""
        if self.osc_mode == 1:
            # Fixed mode: base frequency depends on coarse
            # Coarse 0: 1Hz, 1: 10Hz, 2: 100Hz, 3: 1000Hz base...
            base = 10.0 ** (self.freq_coarse % 4)
            return base * (1.0 + self.freq_fine / 100.0)
        coarse = 0.5 if self.freq_coarse == 0 else float(self.freq_coarse)
        fine = self.freq_fine / 100.0
        return coarse * (1.0 + fine)

    @property
    def detune_cents(self) -> int:
        """Detune offset in nominal steps (-7 to +7)."""
        return self.detune - 7

    def copy(self) -> Operator:
        """Return a deep copy of this Operator."""
        return Operator(**self.__dict__)


@dataclass
class PitchEG:
    """
    Pitch Envelope Generator for DX7 voice.
    - Rates (R1-R4): 0-99
    - Levels (L1-L4): 0-99 (50 = Center/No pitch shift, 0 = lowest, 99 = highest)
    """

    rate_1: int = 99
    rate_2: int = 99
    rate_3: int = 99
    rate_4: int = 99
    level_1: int = 50
    level_2: int = 50
    level_3: int = 50
    level_4: int = 50

    def __post_init__(self) -> None:
        self.clamp_all()

    def clamp_all(self) -> None:
        self.rate_1 = clamp(self.rate_1, 0, 99)
        self.rate_2 = clamp(self.rate_2, 0, 99)
        self.rate_3 = clamp(self.rate_3, 0, 99)
        self.rate_4 = clamp(self.rate_4, 0, 99)
        self.level_1 = clamp(self.level_1, 0, 99)
        self.level_2 = clamp(self.level_2, 0, 99)
        self.level_3 = clamp(self.level_3, 0, 99)
        self.level_4 = clamp(self.level_4, 0, 99)

    def copy(self) -> PitchEG:
        return PitchEG(**self.__dict__)


@dataclass
class LFO:
    """
    Low Frequency Oscillator for DX7 voice.
    - speed: 0-99
    - delay: 0-99
    - pitch_mod_depth: 0-99
    - amp_mod_depth: 0-99
    - key_sync: 0-1 (0: Off, 1: On)
    - waveform: 0-5 (0: Triangle, 1: Saw Down, 2: Saw Up, 3: Square, 4: Sine, 5: S&H)
    - pitch_mod_sens: 0-7
    """

    speed: int = 35
    delay: int = 0
    pitch_mod_depth: int = 0
    amp_mod_depth: int = 0
    key_sync: int = 1
    waveform: int = 0  # 0: Triangle
    pitch_mod_sens: int = 0

    WAVEFORM_NAMES = [
        "Triangle",
        "Saw Down",
        "Saw Up",
        "Square",
        "Sine",
        "Sample & Hold",
    ]

    def __post_init__(self) -> None:
        self.clamp_all()

    def clamp_all(self) -> None:
        self.speed = clamp(self.speed, 0, 99)
        self.delay = clamp(self.delay, 0, 99)
        self.pitch_mod_depth = clamp(self.pitch_mod_depth, 0, 99)
        self.amp_mod_depth = clamp(self.amp_mod_depth, 0, 99)
        self.key_sync = clamp(self.key_sync, 0, 1)
        self.waveform = clamp(self.waveform, 0, 5)
        self.pitch_mod_sens = clamp(self.pitch_mod_sens, 0, 7)

    @property
    def waveform_name(self) -> str:
        return self.WAVEFORM_NAMES[self.waveform]

    def copy(self) -> LFO:
        return LFO(**self.__dict__)


@dataclass
class DX7Patch:
    """
    Complete Yamaha DX7 Voice (Patch).

    Contains:
    - 6 Operators (OP1 to OP6, indexed 1..6 or via patch.operators[0..5])
    - Pitch Envelope Generator
    - Low Frequency Oscillator
    - Algorithm (1-32)
    - Feedback (0-7)
    - Oscillator Key Sync (0-1)
    - Transpose (0-48, 24 = C3)
    - Name (10 ASCII characters)
    """

    name: str = "INIT VOICE"
    operators: List[Operator] = field(default_factory=lambda: [Operator() for _ in range(6)])
    pitch_eg: PitchEG = field(default_factory=PitchEG)
    lfo: LFO = field(default_factory=LFO)
    algorithm: int = 1  # 1 to 32 (1-based for users)
    feedback: int = 0  # 0 to 7
    key_sync: int = 1  # 0 or 1
    transpose: int = 24  # 0..48 (24 = C3)

    def __post_init__(self) -> None:
        if len(self.operators) != 6:
            raise ValueError(f"DX7Patch must have exactly 6 operators, got {len(self.operators)}")
        self.name = self.sanitize_name(self.name)
        self.clamp_all()

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Ensure voice name is exactly 10 valid ASCII characters."""
        # Replace non-ascii or non-printable chars
        cleaned = "".join(c if 32 <= ord(c) <= 126 else " " for c in name)
        # Pad or truncate to 10 chars
        return cleaned[:10].ljust(10, " ")

    def clamp_all(self) -> None:
        """Clamp all voice and sub-component parameters."""
        self.algorithm = clamp(self.algorithm, 1, 32)
        self.feedback = clamp(self.feedback, 0, 7)
        self.key_sync = clamp(self.key_sync, 0, 1)
        self.transpose = clamp(self.transpose, 0, 48)
        self.pitch_eg.clamp_all()
        self.lfo.clamp_all()
        for op in self.operators:
            op.clamp_all()

    def op(self, op_num: int) -> Operator:
        """
        Access an operator by its 1-based index (1 to 6).
        OP1 is operators[0], OP6 is operators[5].
        """
        if not 1 <= op_num <= 6:
            raise IndexError(f"Operator number must be 1-6, got {op_num}")
        return self.operators[op_num - 1]

    @property
    def algorithm_0indexed(self) -> int:
        """0-indexed algorithm value (0-31) for SysEx encoding."""
        return self.algorithm - 1

    @property
    def transpose_note(self) -> str:
        """Human-readable transpose note name (e.g. C3 for 24, C1 for 0, C5 for 48)."""
        notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        octave = (self.transpose // 12) + 1
        note = notes[self.transpose % 12]
        return f"{note}{octave}"

    def copy(self) -> DX7Patch:
        """Deep copy the patch."""
        return DX7Patch(
            name=self.name,
            operators=[op.copy() for op in self.operators],
            pitch_eg=self.pitch_eg.copy(),
            lfo=self.lfo.copy(),
            algorithm=self.algorithm,
            feedback=self.feedback,
            key_sync=self.key_sync,
            transpose=self.transpose,
        )

    def summary(self) -> str:
        """One-line summary of patch."""
        return f"Patch '{self.name}' (Alg {self.algorithm}, FB {self.feedback}, Trans {self.transpose_note})"
