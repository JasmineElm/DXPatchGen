"""
DX7 Patch Mutator / Morphing Engine.
Allows controlled mutation, variations, and breeding of existing patches.
"""

from __future__ import annotations

import random
from typing import Optional

from dxpatchgen.core.models import DX7Patch, Operator, clamp


class PatchMutator:
    """
    Mutates an existing DX7Patch with controlled variability.
    """

    @staticmethod
    def mutate(
        patch: DX7Patch,
        mutation_rate: float = 0.2,  # 0.0 = identical, 1.0 = heavy mutation
        seed: Optional[int] = None,
        mutate_algorithm: bool = False,
        new_name: Optional[str] = None,
    ) -> DX7Patch:
        """
        Create a mutated variation of `patch`.
        """
        rng = random.Random(seed) if seed is not None else random.Random()
        mutated = patch.copy()
        rate = clamp(int(mutation_rate * 100), 0, 100) / 100.0

        if mutate_algorithm and rng.random() < rate * 0.5:
            mutated.algorithm = rng.randint(1, 32)

        # Feedback perturbation
        if rng.random() < rate:
            delta_fb = rng.choice([-1, 1, 0])
            mutated.feedback = clamp(mutated.feedback + delta_fb, 0, 7)

        # Mutate operators
        for op in mutated.operators:
            # 1. Output level
            if rng.random() < rate:
                delta_lvl = rng.randint(-int(rate * 25), int(rate * 25))
                op.output_level = clamp(op.output_level + delta_lvl, 0, 99)

            # 2. Fine frequency / detuning
            if rng.random() < rate:
                delta_fine = rng.randint(-int(rate * 20), int(rate * 20))
                op.freq_fine = clamp(op.freq_fine + delta_fine, 0, 99)

            # 3. Detune
            if rng.random() < rate * 0.7:
                delta_det = rng.choice([-1, 1])
                op.detune = clamp(op.detune + delta_det, 0, 14)

            # 4. Envelopes
            if rng.random() < rate:
                op.eg_rate_1 = clamp(op.eg_rate_1 + rng.randint(-15, 15), 0, 99)
                op.eg_rate_2 = clamp(op.eg_rate_2 + rng.randint(-15, 15), 0, 99)
                op.eg_rate_3 = clamp(op.eg_rate_3 + rng.randint(-15, 15), 0, 99)
                op.eg_rate_4 = clamp(op.eg_rate_4 + rng.randint(-15, 15), 0, 99)

            if rng.random() < rate:
                op.eg_level_2 = clamp(op.eg_level_2 + rng.randint(-20, 20), 0, 99)
                op.eg_level_3 = clamp(op.eg_level_3 + rng.randint(-20, 20), 0, 99)

        # Mutate name
        if new_name:
            mutated.name = new_name
        else:
            base_name = patch.name.strip()
            suffix = rng.choice(["+", "*", "VAR", "M", "2", "'", "X"])
            combined = f"{base_name[:7]} {suffix}".strip()
            mutated.name = combined

        mutated.clamp_all()
        return mutated
