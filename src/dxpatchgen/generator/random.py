"""
Random and Constrained Random DX7 Patch Generators.
"""

from __future__ import annotations

import random
from typing import List, Optional, Sequence

from dxpatchgen.core.algorithms import ALGORITHMS, get_algorithm, get_carrier_ops, get_modulator_ops
from dxpatchgen.core.models import DX7Patch, Operator, PitchEG, LFO, clamp
from dxpatchgen.generator.base import GenerationOptions, PatchGenerator
from dxpatchgen.generator.namer import PatchNamer


# Musically common harmonic coarse ratios in FM synthesis
HARMONIC_COARSE_RATIOS = [0, 1, 1, 1, 2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16]
INHARMONIC_COARSE_RATIOS = [0, 1, 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]


class RandomPatchGenerator(PatchGenerator):
    """
    Pure unconstrained random patch generator.
    Produces raw, experimental, and unexpected FM sounds.
    """

    @property
    def name(self) -> str:
        return "pure_random"

    @property
    def description(self) -> str:
        return "Generates completely random DX7 voice parameters across all 155 settings"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions()
        rng = self.get_rng(opts)

        algorithm = opts.algorithm if opts.algorithm is not None else rng.randint(1, 32)
        feedback = opts.feedback if opts.feedback is not None else rng.randint(0, 7)

        operators: List[Operator] = []
        for _ in range(6):
            op = Operator(
                eg_rate_1=rng.randint(0, 99),
                eg_rate_2=rng.randint(0, 99),
                eg_rate_3=rng.randint(0, 99),
                eg_rate_4=rng.randint(0, 99),
                eg_level_1=rng.randint(0, 99),
                eg_level_2=rng.randint(0, 99),
                eg_level_3=rng.randint(0, 99),
                eg_level_4=rng.randint(0, 99),
                break_point=rng.randint(0, 99),
                left_depth=rng.randint(0, 99),
                right_depth=rng.randint(0, 99),
                left_curve=rng.randint(0, 3),
                right_curve=rng.randint(0, 3),
                rate_scaling=rng.randint(0, 7),
                amp_mod_sens=rng.randint(0, 3),
                key_vel_sens=rng.randint(0, 7),
                output_level=rng.randint(0, 99),
                osc_mode=rng.choice([0, 0, 0, 1]),  # mostly ratio
                freq_coarse=rng.randint(0, 31),
                freq_fine=rng.randint(0, 99),
                detune=rng.randint(0, 14),
            )
            operators.append(op)

        pitch_eg = PitchEG(
            rate_1=rng.randint(50, 99),
            rate_2=rng.randint(50, 99),
            rate_3=rng.randint(50, 99),
            rate_4=rng.randint(50, 99),
            level_1=rng.randint(40, 60),
            level_2=rng.randint(40, 60),
            level_3=rng.randint(40, 60),
            level_4=50,
        )

        lfo = LFO(
            speed=rng.randint(10, 80),
            delay=rng.randint(0, 50),
            pitch_mod_depth=rng.randint(0, 40),
            amp_mod_depth=rng.randint(0, 30),
            key_sync=rng.randint(0, 1),
            waveform=rng.randint(0, 5),
            pitch_mod_sens=rng.randint(0, 4),
        )

        name = opts.name or PatchNamer.generate(category="random", rng=rng)

        return DX7Patch(
            name=name,
            operators=operators,
            pitch_eg=pitch_eg,
            lfo=lfo,
            algorithm=algorithm,
            feedback=feedback,
            key_sync=rng.randint(0, 1),
            transpose=24,
        )


class ConstrainedRandomGenerator(PatchGenerator):
    """
    Musically constrained random patch generator.
    Applies FM synthesis acoustics principles:
    - Carrier / Modulator balance
    - Harmonic frequency ratios
    - Controlled envelope shaping (audible attack, release)
    - Dynamic velocity and rate scaling
    - Musical detuning and feedback saturation
    """

    @property
    def name(self) -> str:
        return "constrained_random"

    @property
    def description(self) -> str:
        return "Generates musically playable, harmonically balanced DX7 patches with sound design heuristics"

    def generate(self, options: Optional[GenerationOptions] = None) -> DX7Patch:
        opts = options or GenerationOptions()
        rng = self.get_rng(opts)

        # 1. Algorithm Selection
        algorithm = opts.algorithm if opts.algorithm is not None else rng.randint(1, 32)
        alg_info = get_algorithm(algorithm)
        carrier_ops = set(alg_info.carriers)

        # 2. Feedback
        if opts.feedback is not None:
            feedback = clamp(opts.feedback, 0, 7)
        else:
            # Subtle feedback (0 to 5) sounds warmer, 6-7 is noise/sawtooth
            feedback = rng.choice([0, 1, 2, 3, 4, 5, 6])

        # 3. Operators
        operators: List[Operator] = []
        for op_num in range(1, 7):
            is_carr = op_num in carrier_ops
            op = self._generate_operator(
                op_num=op_num,
                is_carrier=is_carr,
                options=opts,
                rng=rng,
            )
            operators.append(op)

        # 4. Pitch EG
        pitch_eg = self._generate_pitch_eg(options=opts, rng=rng)

        # 5. LFO
        lfo = self._generate_lfo(options=opts, rng=rng)

        # 6. Name
        name = opts.name or PatchNamer.generate(
            category=opts.category,
            rng=rng,
            style=opts.name_style,
        )

        patch = DX7Patch(
            name=name,
            operators=operators,
            pitch_eg=pitch_eg,
            lfo=lfo,
            algorithm=algorithm,
            feedback=feedback,
            key_sync=1,
            transpose=24,  # C3
        )

        if opts.profile:
            from dxpatchgen.generator.profiles import get_profile
            prof = get_profile(opts.profile)
            if prof:
                patch = prof.apply(patch, opts, rng)

        return patch

    def _generate_operator(
        self,
        op_num: int,
        is_carrier: bool,
        options: GenerationOptions,
        rng: random.Random,
    ) -> Operator:
        """Generate a single operator with musical heuristics."""
        # Frequency selection
        if options.dissonance < 0.2:
            coarse = rng.choice(HARMONIC_COARSE_RATIOS)
            fine = rng.randint(0, int(options.dissonance * 50))
        elif options.dissonance < 0.6:
            coarse = rng.choice(HARMONIC_COARSE_RATIOS + [0, 1, 3, 7, 11])
            fine = rng.randint(0, int(options.dissonance * 80))
        else:
            coarse = rng.choice(INHARMONIC_COARSE_RATIOS)
            fine = rng.randint(0, 99)

        # Detune (-7 to +7, mapped to 0..14 where 7 is center)
        detune_range = int(options.detune_amount * 6)
        if detune_range > 0:
            detune_offset = rng.randint(-detune_range, detune_range)
            detune = clamp(7 + detune_offset, 0, 14)
        else:
            detune = 7

        # Output Level
        if is_carrier:
            # Carriers must be audible
            output_level = rng.randint(82, 99)
            key_vel = int(options.velocity_sensitivity * rng.randint(1, 4))
        else:
            # Modulators scaled by brightness
            base_mod = int(options.brightness * 85)
            output_level = clamp(base_mod + rng.randint(-15, 12), 20, 99)
            key_vel = int(options.velocity_sensitivity * rng.randint(2, 6))

        # Envelopes
        env_speed = options.envelope_speed
        if is_carrier:
            # Attack fast or moderate
            r1 = clamp(int(60 + env_speed * 38) + rng.randint(-5, 5), 30, 99)
            l1 = 99
            # Decay to sustain
            r2 = clamp(int(40 + env_speed * 45) + rng.randint(-10, 10), 10, 99)
            l2 = clamp(rng.randint(75, 95), 40, 99)
            # Sustain phase
            r3 = clamp(rng.randint(20, 60), 5, 80)
            l3 = l2 if env_speed < 0.7 else clamp(l2 - rng.randint(10, 40), 0, 99)
            # Release
            r4 = clamp(int(35 + env_speed * 45) + rng.randint(-10, 10), 15, 99)
            l4 = 0
        else:
            # Modulator envelope shapes harmonic evolution
            r1 = clamp(int(70 + env_speed * 28) + rng.randint(-5, 5), 40, 99)
            l1 = rng.randint(80, 99)
            # Modulator decay determines timbral decay
            r2 = clamp(int(30 + env_speed * 55) + rng.randint(-10, 10), 10, 99)
            # Lower sustain level for modulators gives natural acoustic pluck/bite
            l2 = clamp(rng.randint(20, 75), 0, 95)
            r3 = clamp(rng.randint(20, 60), 5, 80)
            l3 = clamp(l2 - rng.randint(0, 30), 0, 90)
            r4 = clamp(int(30 + env_speed * 45) + rng.randint(-10, 10), 15, 99)
            l4 = 0

        # Keyboard rate scaling (higher notes decay faster, like real instruments)
        rate_scaling = rng.choice([0, 1, 2, 3])

        return Operator(
            eg_rate_1=r1,
            eg_rate_2=r2,
            eg_rate_3=r3,
            eg_rate_4=r4,
            eg_level_1=l1,
            eg_level_2=l2,
            eg_level_3=l3,
            eg_level_4=l4,
            break_point=39,  # C3
            left_depth=rng.randint(0, 20),
            right_depth=rng.randint(0, 20),
            left_curve=0,
            right_curve=0,
            rate_scaling=rate_scaling,
            amp_mod_sens=0,
            key_vel_sens=key_vel,
            output_level=output_level,
            osc_mode=0,
            freq_coarse=coarse,
            freq_fine=fine,
            detune=detune,
        )

    def _generate_pitch_eg(self, options: GenerationOptions, rng: random.Random) -> PitchEG:
        """Generate subtle or neutral pitch envelope."""
        # Mostly neutral (50 = no pitch change) for standard instruments
        if rng.random() < 0.15:
            # Transient pitch dive or blip
            return PitchEG(
                rate_1=rng.randint(70, 99),
                rate_2=rng.randint(50, 99),
                rate_3=rng.randint(50, 99),
                rate_4=rng.randint(50, 99),
                level_1=rng.randint(48, 56),
                level_2=50,
                level_3=50,
                level_4=50,
            )
        return PitchEG(
            rate_1=99, rate_2=99, rate_3=99, rate_4=99,
            level_1=50, level_2=50, level_3=50, level_4=50,
        )

    def _generate_lfo(self, options: GenerationOptions, rng: random.Random) -> LFO:
        """Generate LFO vibrato or movement."""
        if not options.enable_lfo or rng.random() < 0.3:
            return LFO(speed=35, delay=0, pitch_mod_depth=0, amp_mod_depth=0, pitch_mod_sens=0)

        # Subtle musical vibrato
        speed = rng.randint(25, 45)
        delay = rng.randint(10, 40)
        pmd = rng.randint(5, 30)
        pms = rng.choice([1, 2, 3])

        return LFO(
            speed=speed,
            delay=delay,
            pitch_mod_depth=pmd,
            amp_mod_depth=0,
            key_sync=1,
            waveform=0,  # Triangle
            pitch_mod_sens=pms,
        )
