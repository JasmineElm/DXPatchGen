"""
Sonic Profile and Character Layers for DX7 FM Patch Generation.
Applies acoustic, harmonic, and timbral modifiers (Warm, Atonal, Crisp, Gritty, Ethereal)
orthogonally across any patch category.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Type

from dxpatchgen.core.algorithms import get_algorithm
from dxpatchgen.core.models import DX7Patch, Operator, PitchEG, LFO, clamp
from dxpatchgen.generator.base import GenerationOptions


class SonicProfile(ABC):
    """
    Abstract base class for sonic character profiles.
    Transforms and shapes patch parameters according to specific acoustic aesthetics.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def apply(self, patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
        """Apply profile modifications to the patch in-place or return modified patch."""
        pass


class WarmProfile(SonicProfile):
    """
    Warm & Analog Sonic Profile:
    - Lower modulator levels (avoids harsh digital glassiness)
    - Negative exponential keyboard level scaling (-EXP curve) on higher frequencies
    - Subtle detuning between carrier pairs (thick analog chorusing)
    - Optional low-frequency sub-oscillator carrier (adds weight)
    - Moderate feedback saturation (level 2-4)
    - Softer attack transients
    """

    @property
    def name(self) -> str:
        return "warm"

    @property
    def description(self) -> str:
        return "Warm analog character: softened modulators, -EXP high-key rolloff, detuned chorus pairs, and rich low-end"

    def apply(self, patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
        alg_info = get_algorithm(patch.algorithm)
        carrier_set = set(alg_info.carriers)

        # 1. Warm saturation feedback
        if options.feedback is None:
            patch.feedback = rng.choice([2, 3, 4])

        # 2. Process operators
        carrier_count = len(carrier_set)
        carrier_seen = 0

        for op_num in range(1, 7):
            op = patch.op(op_num)
            is_carr = op_num in carrier_set

            if is_carr:
                carrier_seen += 1
                # Sub-oscillator on first carrier if multi-carrier
                if carrier_seen == 1 and carrier_count > 1 and rng.random() < 0.6:
                    op.freq_coarse = 0  # 0.5 ratio sub-harmonic
                    op.freq_fine = 0
                    op.detune = 7  # center
                else:
                    # Detune carrier pairs for lush analog chorus
                    det_offset = rng.choice([-2, -1, 1, 2])
                    op.detune = clamp(7 + det_offset, 0, 14)

                # Soften attack transient slightly (less clicky)
                op.eg_rate_1 = clamp(op.eg_rate_1, 35, 90)
                # Warm sustain
                op.eg_level_3 = clamp(op.eg_level_3, 70, 95)
            else:
                # Modulators: lower output level to avoid harsh FM sizzle
                op.output_level = clamp(int(op.output_level * 0.82) + rng.randint(-4, 4), 20, 85)

                # Negative Exponential keyboard scaling to roll off high-frequency sidebands (like an analog filter)
                op.break_point = rng.randint(39, 55)  # C3 - G4
                op.right_curve = 1  # 1 = -EXP (negative exponential)
                op.right_depth = rng.randint(25, 65)  # progressively dampens highs
                op.left_curve = rng.choice([0, 2])  # 0: -LIN, 2: +EXP

                # Gentle detune
                op.detune = clamp(7 + rng.randint(-2, 2), 0, 14)

        return patch


class AtonalProfile(SonicProfile):
    """
    Atonal & Metallic / Percussive Profile:
    - Favours fixed frequencies (osc_mode = 1) over pitch-tracking ratio mode
    - Inharmonic ratio combinations (non-integer sidebands)
    - Zero or flat key rate scaling (decouples pitch from standard 12-TET keys)
    - Fast pitch envelope dives for percussive punch
    - Metallic feedback noise
    """

    @property
    def name(self) -> str:
        return "atonal"

    @property
    def description(self) -> str:
        return "Atonal & metallic: fixed pitch frequencies, inharmonic ratios, and unpitched percussive clangs"

    def apply(self, patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
        alg_info = get_algorithm(patch.algorithm)
        carrier_set = set(alg_info.carriers)

        # Higher feedback for metallic noise/sizzle
        if options.feedback is None:
            patch.feedback = rng.choice([3, 4, 5, 6])

        # Pick 2-4 operators to force to Fixed Frequency Mode (Hz instead of ratio)
        num_fixed = rng.randint(2, 5)
        fixed_indices = set(rng.sample(range(6), num_fixed))

        for idx in range(6):
            op = patch.operators[idx]
            op_num = idx + 1
            is_carr = op_num in carrier_set

            if idx in fixed_indices:
                op.osc_mode = 1  # Fixed frequency
                op.freq_coarse = rng.choice([0, 1, 2, 3])  # 1Hz, 10Hz, 100Hz, 1000Hz base
                op.freq_fine = rng.randint(5, 95)
            else:
                op.osc_mode = 0
                # Inharmonic coarse ratios
                op.freq_coarse = rng.choice([0, 1, 3, 7, 11, 13, 17, 19, 23, 29, 31])
                op.freq_fine = rng.randint(15, 85)

            # Flat key tracking / rate scaling
            op.rate_scaling = 0
            op.break_point = rng.randint(20, 80)
            op.left_depth = rng.randint(0, 15)
            op.right_depth = rng.randint(0, 15)

            # Fast snappy envelopes for clangs/percussion
            if not is_carr:
                op.output_level = rng.randint(60, 98)
                op.eg_rate_1 = 99
                op.eg_rate_2 = rng.randint(50, 85)
                op.eg_level_2 = rng.randint(0, 40)
                op.eg_level_3 = 0

        # Pitch dive envelope for percussive impact
        if rng.random() < 0.7:
            patch.pitch_eg = PitchEG(
                rate_1=rng.randint(85, 99),
                rate_2=rng.randint(60, 90),
                rate_3=90,
                rate_4=90,
                level_1=rng.choice([80, 88, 95, 20, 15]),  # pitch drop from above or below
                level_2=50,
                level_3=50,
                level_4=50,
            )

        return patch


class CrispProfile(SonicProfile):
    """
    Crisp, Bright & Glassy Profile:
    - Elevated modulator levels
    - High-harmonic coarse ratios (3, 5, 7, 9, 14)
    - Positive keyboard level scaling for brilliant, sparkling highs
    - Clean detuning
    """

    @property
    def name(self) -> str:
        return "crisp"

    @property
    def description(self) -> str:
        return "Crisp & glassy: heightened modulator index, high-order harmonics, and brilliant top-end sparkle"

    def apply(self, patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
        alg_info = get_algorithm(patch.algorithm)
        carrier_set = set(alg_info.carriers)

        for op_num in range(1, 7):
            op = patch.op(op_num)
            is_carr = op_num in carrier_set

            if not is_carr:
                # Boost brightness
                op.output_level = clamp(int(op.output_level * 1.15) + rng.randint(3, 8), 50, 99)
                op.freq_coarse = rng.choice([2, 3, 4, 5, 7, 9, 14])

                # Positive scaling for bright treble
                op.right_curve = 3  # +LIN
                op.right_depth = rng.randint(15, 40)

            op.detune = clamp(7 + rng.choice([-1, 0, 1]), 0, 14)

        return patch


class GrittyProfile(SonicProfile):
    """
    Gritty & Aggressive Drive Profile:
    - High feedback (5 to 7) for sawtooth/square wave distortion
    - High velocity sensitivity on modulators for explosive dynamic punch
    - Dense modulation indices
    """

    @property
    def name(self) -> str:
        return "gritty"

    @property
    def description(self) -> str:
        return "Gritty & aggressive: high feedback saturation, heavy modulation drive, and punchy velocity bite"

    def apply(self, patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
        patch.feedback = rng.choice([5, 6, 7])

        for op in patch.operators:
            op.key_vel_sens = rng.randint(4, 7)
            op.output_level = clamp(op.output_level + rng.randint(5, 12), 40, 99)
            op.detune = clamp(7 + rng.choice([-3, -2, 2, 3]), 0, 14)

        return patch


class EtherealProfile(SonicProfile):
    """
    Ethereal & Ambient Profile:
    - Slow, evolving envelope attacks
    - Long sustained release tails
    - Slow LFO pitch/amp movement and stereo chorus detune
    """

    @property
    def name(self) -> str:
        return "ethereal"

    @property
    def description(self) -> str:
        return "Ethereal & ambient: slow evolving swell envelopes, long release tails, and gentle LFO vibrato"

    def apply(self, patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
        for op in patch.operators:
            # Slow swell attack
            op.eg_rate_1 = rng.randint(20, 42)
            op.eg_rate_2 = rng.randint(20, 45)
            # Long lingering release
            op.eg_rate_4 = rng.randint(18, 38)
            op.detune = clamp(7 + rng.choice([-3, -2, -1, 1, 2, 3]), 0, 14)

        patch.lfo = LFO(
            speed=rng.randint(25, 38),
            delay=rng.randint(20, 45),
            pitch_mod_depth=rng.randint(15, 35),
            waveform=0,  # Triangle
            pitch_mod_sens=2,
        )

        return patch


# Registry of available sonic profiles
PROFILE_REGISTRY: Dict[str, Type[SonicProfile]] = {
    "warm": WarmProfile,
    "atonal": AtonalProfile,
    "crisp": CrispProfile,
    "gritty": GrittyProfile,
    "ethereal": EtherealProfile,
}


def get_profile(profile_name: Optional[str]) -> Optional[SonicProfile]:
    """Retrieve SonicProfile instance by name, or None if neutral/none."""
    if not profile_name:
        return None
    key = profile_name.lower().strip()
    cls = PROFILE_REGISTRY.get(key)
    return cls() if cls else None
