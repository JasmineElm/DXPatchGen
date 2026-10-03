"""
Sound design category templates for DX7 FM synthesis.
Provides specialized generators for electric pianos, basses, pads, leads, bells, brass, plucks, percussive drums, and FX.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Type

from dxpatchgen.core.algorithms import get_algorithm
from dxpatchgen.core.models import DX7Patch, Operator, PitchEG, LFO, clamp
from dxpatchgen.generator.base import GenerationOptions, PatchGenerator
from dxpatchgen.generator.namer import PatchNamer
from dxpatchgen.generator.profiles import get_profile
from dxpatchgen.generator.random import ConstrainedRandomGenerator, RandomPatchGenerator


def _apply_profile_if_specified(patch: DX7Patch, options: GenerationOptions, rng: random.Random) -> DX7Patch:
    """Helper to apply optional sonic profile layer (Warm, Atonal, Crisp, etc.)."""
    if options.profile:
        profile = get_profile(options.profile)
        if profile:
            patch = profile.apply(patch, options, rng)
    return patch


class KeysGenerator(PatchGenerator):
    """Generates classic 80s FM Electric Pianos, Tines, Clavinets, and Harpsichords."""

    @property
    def name(self) -> str:
        return "keys"

    @property
    def description(self) -> str:
        return "Electric pianos, FM tines, rhodes, clavs and harpsichords"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="keys")
        rng = self.get_rng(opts)

        # Alg 5 (3x 2-op stacks) or Alg 1 / 3 / 11 are legendary for FM pianos
        alg = opts.algorithm if opts.algorithm is not None else rng.choice([5, 1, 3, 11, 7])
        carriers = set(get_algorithm(alg).carriers)

        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carriers
            if is_carr:
                # Body / fundamental carrier
                coarse = rng.choice([1, 1, 2])
                fine = rng.randint(0, 3)
                out_lvl = rng.randint(90, 99)
                r1, r2, r3, r4 = 95, rng.randint(25, 45), rng.randint(15, 30), 45
                l1, l2, l3, l4 = 99, rng.randint(65, 85), rng.randint(40, 65), 0
                vel_sens = rng.randint(2, 4)
            else:
                # Tine / metallic modulator
                coarse = rng.choice([1, 3, 5, 7, 14])
                fine = rng.randint(0, 10)
                base_mod = int(opts.brightness * 82)
                out_lvl = clamp(base_mod + rng.randint(-10, 8), 45, 95)
                # Fast decay for hammer / tine transient
                r1, r2, r3, r4 = 99, rng.randint(50, 75), rng.randint(30, 50), 50
                l1, l2, l3, l4 = rng.randint(85, 99), rng.randint(20, 55), 0, 0
                vel_sens = rng.randint(4, 7)  # high velocity sensitivity for punchy attack!

            operators.append(
                Operator(
                    eg_rate_1=r1, eg_rate_2=r2, eg_rate_3=r3, eg_rate_4=r4,
                    eg_level_1=l1, eg_level_2=l2, eg_level_3=l3, eg_level_4=l4,
                    rate_scaling=rng.choice([1, 2, 3]),
                    key_vel_sens=vel_sens,
                    output_level=out_lvl,
                    freq_coarse=coarse,
                    freq_fine=fine,
                    detune=clamp(7 + rng.randint(-2, 2), 0, 14),
                )
            )

        name = opts.name or PatchNamer.generate("keys", rng=rng, style=opts.name_style)
        patch = DX7Patch(name=name, operators=operators, algorithm=alg, feedback=rng.randint(2, 5), transpose=24)
        return _apply_profile_if_specified(patch, opts, rng)


class BassGenerator(PatchGenerator):
    """Generates punchy FM basses, slap bass, solid sub bass, and acid lines."""

    @property
    def name(self) -> str:
        return "bass"

    @property
    def description(self) -> str:
        return "Punchy FM slap bass, solid sub bass, funk, and acid basslines"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="bass")
        rng = self.get_rng(opts)

        # Alg 1, 2, 8, 16, 21 work great for basses
        alg = opts.algorithm if opts.algorithm is not None else rng.choice([1, 2, 8, 16, 21, 5])
        carriers = set(get_algorithm(alg).carriers)

        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carriers
            if is_carr:
                coarse = rng.choice([0, 1, 1])  # 0.5 or 1.0 ratio
                out_lvl = rng.randint(92, 99)
                r1, r2, r3, r4 = 99, rng.randint(40, 70), rng.randint(20, 50), 55
                l1, l2, l3, l4 = 99, rng.randint(50, 80), 0, 0
                vel_sens = rng.randint(2, 4)
            else:
                coarse = rng.choice([1, 2, 3, 4, 6])
                base_mod = int(opts.brightness * 88)
                out_lvl = clamp(base_mod + rng.randint(-8, 8), 50, 98)
                # Quick pop/thump envelope
                r1, r2, r3, r4 = 99, rng.randint(55, 85), rng.randint(35, 60), 60
                l1, l2, l3, l4 = rng.randint(85, 99), rng.randint(10, 45), 0, 0
                vel_sens = rng.randint(3, 7)

            operators.append(
                Operator(
                    eg_rate_1=r1, eg_rate_2=r2, eg_rate_3=r3, eg_rate_4=r4,
                    eg_level_1=l1, eg_level_2=l2, eg_level_3=l3, eg_level_4=l4,
                    rate_scaling=rng.choice([1, 2]),
                    key_vel_sens=vel_sens,
                    output_level=out_lvl,
                    freq_coarse=coarse,
                    freq_fine=rng.randint(0, 4),
                    detune=clamp(7 + rng.randint(-1, 1), 0, 14),
                )
            )

        name = opts.name or PatchNamer.generate("bass", rng=rng, style=opts.name_style)
        patch = DX7Patch(name=name, operators=operators, algorithm=alg, feedback=rng.randint(3, 6), transpose=12)  # C2
        return _apply_profile_if_specified(patch, opts, rng)


class PadGenerator(PatchGenerator):
    """Generates lush analog-style FM pads, glass textures, and ambient strings."""

    @property
    def name(self) -> str:
        return "pad"

    @property
    def description(self) -> str:
        return "Lush ambient pads, warm string textures, glass choirs, and slow sweeps"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="pad")
        rng = self.get_rng(opts)

        # Alg 5 is particularly lush for Warm Pads (three detuned 2-op pairs)
        if opts.profile == "warm":
            alg = opts.algorithm if opts.algorithm is not None else 5
        else:
            alg = opts.algorithm if opts.algorithm is not None else rng.choice([5, 6, 21, 22, 12, 32])
        carriers = set(get_algorithm(alg).carriers)

        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carriers
            coarse = rng.choice([1, 2, 2, 3, 4])
            fine = rng.randint(0, 15)
            # Rich detuning between operators
            detune = clamp(7 + rng.choice([-4, -3, -2, -1, 1, 2, 3, 4]), 0, 14)

            # Slow attack and long release
            r1 = rng.randint(25, 45)  # slow attack
            r2 = rng.randint(20, 40)
            r3 = rng.randint(15, 35)
            r4 = rng.randint(20, 40)  # slow release
            l1, l2, l3, l4 = 99, rng.randint(80, 95), rng.randint(75, 90), 0

            out_lvl = rng.randint(85, 99) if is_carr else clamp(int(opts.brightness * 75) + rng.randint(-10, 10), 30, 85)

            operators.append(
                Operator(
                    eg_rate_1=r1, eg_rate_2=r2, eg_rate_3=r3, eg_rate_4=r4,
                    eg_level_1=l1, eg_level_2=l2, eg_level_3=l3, eg_level_4=l4,
                    rate_scaling=rng.choice([0, 1]),
                    key_vel_sens=rng.randint(1, 3),
                    output_level=out_lvl,
                    freq_coarse=coarse,
                    freq_fine=fine,
                    detune=detune,
                )
            )

        # Lush slow LFO chorus
        lfo = LFO(speed=rng.randint(28, 42), delay=rng.randint(15, 35), pitch_mod_depth=rng.randint(12, 30), pitch_mod_sens=2)
        name = opts.name or PatchNamer.generate("pad", rng=rng, style=opts.name_style)
        patch = DX7Patch(name=name, operators=operators, lfo=lfo, algorithm=alg, feedback=rng.randint(1, 4), transpose=24)
        return _apply_profile_if_specified(patch, opts, rng)


class PercussiveGenerator(PatchGenerator):
    """Generates acoustic-style and electronic FM drums, kicks, snares, toms, clangs, and cymbals."""

    @property
    def name(self) -> str:
        return "percussive"

    @property
    def description(self) -> str:
        return "FM drums, punchy kicks, metallic snares, toms, cymbals, and percussive hits"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="percussive")
        rng = self.get_rng(opts)

        # Alg 1, 2, 4, 16, 21, 27 are great for complex impact + noise percussion
        alg = opts.algorithm if opts.algorithm is not None else rng.choice([1, 2, 4, 11, 16, 21, 27])
        carriers = set(get_algorithm(alg).carriers)

        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carriers

            if is_carr:
                coarse = rng.choice([0, 1, 2])
                out_lvl = rng.randint(90, 99)
                # Instant attack, fast decay to zero sustain
                r1, r2, r3, r4 = 99, rng.randint(60, 88), rng.randint(45, 75), rng.randint(60, 90)
                l1, l2, l3, l4 = 99, rng.randint(10, 40), 0, 0
                vel_sens = rng.randint(3, 6)
            else:
                coarse = rng.choice([1, 2, 3, 5, 7, 11, 17, 23])
                out_lvl = clamp(int(opts.brightness * 90) + rng.randint(-8, 8), 50, 99)
                r1, r2, r3, r4 = 99, rng.randint(70, 95), rng.randint(50, 80), 75
                l1, l2, l3, l4 = rng.randint(85, 99), rng.randint(0, 25), 0, 0
                vel_sens = rng.randint(4, 7)

            operators.append(
                Operator(
                    eg_rate_1=r1, eg_rate_2=r2, eg_rate_3=r3, eg_rate_4=r4,
                    eg_level_1=l1, eg_level_2=l2, eg_level_3=l3, eg_level_4=l4,
                    rate_scaling=rng.choice([1, 2, 3]),
                    key_vel_sens=vel_sens,
                    output_level=out_lvl,
                    freq_coarse=coarse,
                    freq_fine=rng.randint(0, 30),
                    detune=clamp(7 + rng.randint(-2, 2), 0, 14),
                )
            )

        # Dynamic Pitch Dive for impact
        pitch_eg = PitchEG(
            rate_1=rng.randint(85, 99),
            rate_2=rng.randint(60, 90),
            rate_3=90,
            rate_4=90,
            level_1=rng.choice([85, 92, 98, 15, 25]),  # pitch drop
            level_2=50,
            level_3=50,
            level_4=50,
        )

        name = opts.name or PatchNamer.generate("percussive", rng=rng, style=opts.name_style)
        patch = DX7Patch(
            name=name,
            operators=operators,
            pitch_eg=pitch_eg,
            algorithm=alg,
            feedback=rng.randint(4, 7),
            transpose=12,  # C2
        )
        return _apply_profile_if_specified(patch, opts, rng)


class BellGenerator(PatchGenerator):
    """Generates crystal bells, tubular chimes, vibraphones, and metallic gamelan."""

    @property
    def name(self) -> str:
        return "bell"

    @property
    def description(self) -> str:
        return "Crystal bells, tubular chimes, vibraphones, celestes, and metallic gamelan"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="bell")
        rng = self.get_rng(opts)

        alg = opts.algorithm if opts.algorithm is not None else rng.choice([1, 2, 4, 11, 14, 5])
        carriers = set(get_algorithm(alg).carriers)

        bell_ratios = [(1, 0), (2, 76), (3, 41), (5, 40), (7, 0), (1, 41)]

        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carriers
            coarse, fine = bell_ratios[op_num - 1]

            if is_carr:
                out_lvl = rng.randint(90, 99)
                r1, r2, r3, r4 = 99, rng.randint(20, 40), rng.randint(10, 25), 35
                l1, l2, l3, l4 = 99, rng.randint(40, 70), 0, 0
            else:
                out_lvl = clamp(int(opts.brightness * 88) + rng.randint(-10, 8), 45, 95)
                r1, r2, r3, r4 = 99, rng.randint(35, 60), rng.randint(15, 35), 40
                l1, l2, l3, l4 = rng.randint(85, 99), rng.randint(15, 40), 0, 0

            operators.append(
                Operator(
                    eg_rate_1=r1, eg_rate_2=r2, eg_rate_3=r3, eg_rate_4=r4,
                    eg_level_1=l1, eg_level_2=l2, eg_level_3=l3, eg_level_4=l4,
                    rate_scaling=rng.choice([2, 3, 4]),
                    key_vel_sens=rng.randint(3, 7),
                    output_level=out_lvl,
                    freq_coarse=coarse,
                    freq_fine=fine,
                    detune=clamp(7 + rng.randint(-2, 2), 0, 14),
                )
            )

        name = opts.name or PatchNamer.generate("bell", rng=rng, style=opts.name_style)
        patch = DX7Patch(name=name, operators=operators, algorithm=alg, feedback=rng.randint(0, 3), transpose=36)  # C4
        return _apply_profile_if_specified(patch, opts, rng)


class LeadGenerator(PatchGenerator):
    """Generates cutting FM synth leads, sync solos, and bitey digital leads."""

    @property
    def name(self) -> str:
        return "lead"

    @property
    def description(self) -> str:
        return "Cutting FM synth leads, sync leads, and 80s pitch solos"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="lead")
        rng = self.get_rng(opts)

        alg = opts.algorithm if opts.algorithm is not None else rng.choice([1, 2, 16, 17, 18, 20])
        carriers = set(get_algorithm(alg).carriers)

        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carriers
            coarse = rng.choice([1, 2, 3, 4])
            fine = rng.randint(0, 8)
            detune = clamp(7 + rng.randint(-3, 3), 0, 14)

            if is_carr:
                out_lvl = rng.randint(95, 99)
                r1, r2, r3, r4 = 99, 85, 70, 60
                l1, l2, l3, l4 = 99, 92, 85, 0
            else:
                out_lvl = clamp(int(opts.brightness * 92) + rng.randint(-5, 6), 55, 99)
                r1, r2, r3, r4 = 99, rng.randint(45, 75), 60, 60
                l1, l2, l3, l4 = 99, rng.randint(60, 88), rng.randint(50, 80), 0

            operators.append(
                Operator(
                    eg_rate_1=r1, eg_rate_2=r2, eg_rate_3=r3, eg_rate_4=r4,
                    eg_level_1=l1, eg_level_2=l2, eg_level_3=l3, eg_level_4=l4,
                    rate_scaling=rng.choice([1, 2]),
                    key_vel_sens=rng.randint(2, 5),
                    output_level=out_lvl,
                    freq_coarse=coarse,
                    freq_fine=fine,
                    detune=detune,
                )
            )

        lfo = LFO(speed=rng.randint(40, 55), delay=rng.randint(10, 25), pitch_mod_depth=rng.randint(10, 25), pitch_mod_sens=2)
        name = opts.name or PatchNamer.generate("lead", rng=rng, style=opts.name_style)
        patch = DX7Patch(name=name, operators=operators, lfo=lfo, algorithm=alg, feedback=rng.randint(4, 7), transpose=24)
        return _apply_profile_if_specified(patch, opts, rng)


class FXGenerator(PatchGenerator):
    """Generates sci-fi effects, lasers, risers, drones, and alien soundscapes."""

    @property
    def name(self) -> str:
        return "fx"

    @property
    def description(self) -> str:
        return "Sci-fi sound effects, space lasers, sweeps, drones, and alien noise"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions(category="fx")
        rng = self.get_rng(opts)

        alg = opts.algorithm if opts.algorithm is not None else rng.choice([16, 17, 18, 19, 27, 28])
        operators: List[Operator] = []
        for _ in range(6):
            coarse = rng.randint(0, 31)
            fine = rng.randint(0, 99)
            mode = rng.choice([0, 1])

            operators.append(
                Operator(
                    eg_rate_1=rng.randint(20, 99),
                    eg_rate_2=rng.randint(20, 99),
                    eg_rate_3=rng.randint(20, 99),
                    eg_rate_4=rng.randint(20, 99),
                    eg_level_1=rng.randint(40, 99),
                    eg_level_2=rng.randint(20, 99),
                    eg_level_3=rng.randint(0, 99),
                    eg_level_4=0,
                    output_level=rng.randint(65, 99),
                    osc_mode=mode,
                    freq_coarse=coarse,
                    freq_fine=fine,
                    detune=rng.randint(0, 14),
                )
            )

        pitch_eg = PitchEG(
            rate_1=rng.randint(30, 99),
            rate_2=rng.randint(30, 99),
            rate_3=rng.randint(30, 99),
            rate_4=rng.randint(30, 99),
            level_1=rng.choice([10, 20, 80, 90]),
            level_2=rng.randint(30, 70),
            level_3=50,
            level_4=50,
        )

        lfo = LFO(
            speed=rng.randint(30, 99),
            pitch_mod_depth=rng.randint(20, 80),
            amp_mod_depth=rng.randint(0, 60),
            waveform=rng.randint(0, 5),
            pitch_mod_sens=rng.randint(3, 7),
        )

        name = opts.name or PatchNamer.generate("fx", rng=rng, style=opts.name_style)
        patch = DX7Patch(
            name=name,
            operators=operators,
            pitch_eg=pitch_eg,
            lfo=lfo,
            algorithm=alg,
            feedback=rng.randint(4, 7),
            transpose=24,
        )
        return _apply_profile_if_specified(patch, opts, rng)


# Registry of available generator strategies
GENERATOR_REGISTRY: Dict[str, Type[PatchGenerator]] = {
    "random": RandomPatchGenerator,
    "constrained": ConstrainedRandomGenerator,
    "keys": KeysGenerator,
    "bass": BassGenerator,
    "pad": PadGenerator,
    "percussive": PercussiveGenerator,
    "drum": PercussiveGenerator,
    "bell": BellGenerator,
    "lead": LeadGenerator,
    "fx": FXGenerator,
}


def get_generator(category: str = "constrained") -> PatchGenerator:
    """Retrieve generator instance for category."""
    cat = category.lower().strip()
    cls = GENERATOR_REGISTRY.get(cat, ConstrainedRandomGenerator)
    return cls()
