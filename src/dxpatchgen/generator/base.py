"""
Base classes, options, and interfaces for DX7 patch generation.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from dxpatchgen.core.models import DX7Patch


@dataclass
class GenerationOptions:
    """
    Configuration options and sonic constraints for patch generators.
    """

    # Reproducibility
    seed: Optional[int] = None

    # Structural constraints
    algorithm: Optional[int] = None  # Force algorithm 1-32 or None for auto/random
    category: str = "random"  # 'random', 'keys', 'bass', 'pad', 'lead', 'bell', 'brass', 'pluck', 'percussive', 'fx'
    profile: Optional[str] = None  # Sonic profile: 'warm', 'atonal', 'crisp', 'gritty', 'ethereal', or None

    # Timbre & Harmonic constraints (0.0 to 1.0)
    brightness: float = 0.6  # Modulator output levels / FM index
    dissonance: float = 0.0  # Inharmonicity: 0.0 = strictly harmonic, 1.0 = noisy/inharmonic
    envelope_speed: float = 0.5  # 0.0 = slow evolving, 1.0 = snappy/percussive
    detune_amount: float = 0.3  # 0.0 = unison, 1.0 = heavy chorus / detuning
    velocity_sensitivity: float = 0.5  # Dynamic response to keyboard velocity

    # Modulation & Feedback
    feedback: Optional[int] = None  # 0 to 7, or None to generate
    enable_lfo: bool = True  # Add vibrato/tremolo movement

    # Naming
    name: Optional[str] = None  # Custom name or None to auto-generate
    name_style: Optional[str] = None  # Naming theme/prefix


class PatchGenerator(ABC):
    """
    Abstract base class for all DX7 patch generators.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the generator / strategy."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what sound category or method this generator produces."""
        pass

    @abstractmethod
    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        """
        Generate a DX7Patch according to the provided options.
        """
        pass

    def get_rng(self, options: Optional[GenerationOptions]) -> random.Random:
        """Initialize random number generator with seed if provided."""
        if options and options.seed is not None:
            return random.Random(options.seed)
        return random.Random()
