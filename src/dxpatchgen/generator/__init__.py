"""
DX7 patch generation, synthesis templates, sonic profiles, mutation, and naming.
"""

from dxpatchgen.generator.base import GenerationOptions, PatchGenerator
from dxpatchgen.generator.random import (
    RandomPatchGenerator,
    ConstrainedRandomGenerator,
    HARMONIC_COARSE_RATIOS,
    INHARMONIC_COARSE_RATIOS,
)
from dxpatchgen.generator.profiles import (
    SonicProfile,
    WarmProfile,
    AtonalProfile,
    CrispProfile,
    GrittyProfile,
    EtherealProfile,
    PROFILE_REGISTRY,
    get_profile,
)
from dxpatchgen.generator.templates import (
    KeysGenerator,
    BassGenerator,
    PadGenerator,
    PercussiveGenerator,
    BellGenerator,
    LeadGenerator,
    FXGenerator,
    GENERATOR_REGISTRY,
    get_generator,
)
from dxpatchgen.generator.mutator import PatchMutator
from dxpatchgen.generator.namer import PatchNamer

__all__ = [
    "GenerationOptions",
    "PatchGenerator",
    "RandomPatchGenerator",
    "ConstrainedRandomGenerator",
    "SonicProfile",
    "WarmProfile",
    "AtonalProfile",
    "CrispProfile",
    "GrittyProfile",
    "EtherealProfile",
    "PROFILE_REGISTRY",
    "get_profile",
    "HARMONIC_COARSE_RATIOS",
    "INHARMONIC_COARSE_RATIOS",
    "KeysGenerator",
    "BassGenerator",
    "PadGenerator",
    "PercussiveGenerator",
    "BellGenerator",
    "LeadGenerator",
    "FXGenerator",
    "GENERATOR_REGISTRY",
    "get_generator",
    "PatchMutator",
    "PatchNamer",
]
