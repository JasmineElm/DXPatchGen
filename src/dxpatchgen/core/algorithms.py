"""
Yamaha DX7 32 Algorithms specification, topology, and visual diagrams.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple


@dataclass(frozen=True)
class AlgorithmInfo:
    """
    Metadata and connection matrix for one of the 32 DX7 algorithms.
    """

    id: int  # 1 to 32
    carriers: Tuple[int, ...]  # Operator numbers (1..6) that output audio
    feedback_op: int  # Operator with self-feedback loop (1..6)
    description: str  # High-level sonic / structural role
    ascii_diagram: str  # ASCII visual representation
    # Direct modulation connections: dict of {modulating_op: [modulated_ops]}
    connections: Dict[int, List[int]]

    @property
    def modulators(self) -> Tuple[int, ...]:
        """Operators that act as modulators (not carriers)."""
        carrier_set = set(self.carriers)
        return tuple(op for op in range(1, 7) if op not in carrier_set)

    def is_carrier(self, op: int) -> bool:
        """Check if an operator is a carrier in this algorithm."""
        return op in self.carriers

    def is_modulator(self, op: int) -> bool:
        """Check if an operator is a modulator in this algorithm."""
        return op not in self.carriers

    def modulates(self, op: int) -> List[int]:
        """Return list of operators modulated directly by `op`."""
        return self.connections.get(op, [])


# Definitions of all 32 DX7 algorithms
ALGORITHMS: Dict[int, AlgorithmInfo] = {
    1: AlgorithmInfo(
        id=1,
        carriers=(1, 3),
        feedback_op=6,
        description="Dual Stacks: 4-op complex stack [6->5->4->3] + 2-op stack [2->1]",
        ascii_diagram=(
            "  [6]⮌\n"
            "   ↓\n"
            "  [5]     [2]\n"
            "   ↓       ↓\n"
            "  [4]     [1]🔊\n"
            "   ↓\n"
            "  [3]🔊\n"
            "─────────────"
        ),
        connections={6: [5], 5: [4], 4: [3], 2: [1]},
    ),
    2: AlgorithmInfo(
        id=2,
        carriers=(1, 3),
        feedback_op=2,
        description="Dual Stacks: 4-op stack [6->5->4->3] + 2-op stack [2->1] (FB on OP2)",
        ascii_diagram=(
            "  [6]     [2]⮌\n"
            "   ↓       ↓\n"
            "  [5]     [1]🔊\n"
            "   ↓\n"
            "  [4]\n"
            "   ↓\n"
            "  [3]🔊\n"
            "─────────────"
        ),
        connections={6: [5], 5: [4], 4: [3], 2: [1]},
    ),
    3: AlgorithmInfo(
        id=3,
        carriers=(1, 4),
        feedback_op=6,
        description="Dual 3-op Stacks: [6->5->4] + [3->2->1]",
        ascii_diagram=(
            "  [6]⮌    [3]\n"
            "   ↓       ↓\n"
            "  [5]     [2]\n"
            "   ↓       ↓\n"
            "  [4]🔊   [1]🔊\n"
            "─────────────"
        ),
        connections={6: [5], 5: [4], 3: [2], 2: [1]},
    ),
    4: AlgorithmInfo(
        id=4,
        carriers=(1, 4),
        feedback_op=6,
        description="Branching 3-op Stacks: [6,5 -> 4] + [3->2->1]",
        ascii_diagram=(
            " [6]⮌ [5] [3]\n"
            "   ↘   ↙    ↓\n"
            "    [4]🔊  [2]\n"
            "            ↓\n"
            "           [1]🔊\n"
            "─────────────"
        ),
        connections={6: [4], 5: [4], 3: [2], 2: [1]},
    ),
    5: AlgorithmInfo(
        id=5,
        carriers=(1, 3, 5),
        feedback_op=6,
        description="Three 2-op Stacks: [6->5], [4->3], [2->1]",
        ascii_diagram=(
            "  [6]⮌  [4]   [2]\n"
            "   ↓     ↓     ↓\n"
            "  [5]🔊 [3]🔊 [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5], 4: [3], 2: [1]},
    ),
    6: AlgorithmInfo(
        id=6,
        carriers=(1, 3, 5),
        feedback_op=6,
        description="Three 2-op Stacks with shared/feedback modulation",
        ascii_diagram=(
            "  [6]⮌  [4]   [2]\n"
            "  ↙ ↘    ↓     ↓\n"
            " [5]🔊[3]🔊   [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5, 3], 4: [3], 2: [1]},
    ),
    7: AlgorithmInfo(
        id=7,
        carriers=(1, 3, 5),
        feedback_op=6,
        description="Three Carriers: [6->5], [4->3], [2->1] (FB on 6)",
        ascii_diagram=(
            "  [6]⮌  [4]   [2]\n"
            "   ↓     ↓     ↓\n"
            "  [5]🔊 [3]🔊 [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5], 4: [3], 2: [1]},
    ),
    8: AlgorithmInfo(
        id=8,
        carriers=(1, 3, 5),
        feedback_op=4,
        description="Three 2-op Stacks: [6->5], [4->3] (FB on 4), [2->1]",
        ascii_diagram=(
            "  [6]   [4]⮌  [2]\n"
            "   ↓     ↓     ↓\n"
            "  [5]🔊 [3]🔊 [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5], 4: [3], 2: [1]},
    ),
    9: AlgorithmInfo(
        id=9,
        carriers=(1, 3, 5),
        feedback_op=2,
        description="Three 2-op Stacks: [6->5], [4->3], [2->1] (FB on 2)",
        ascii_diagram=(
            "  [6]   [4]   [2]⮌\n"
            "   ↓     ↓     ↓\n"
            "  [5]🔊 [3]🔊 [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5], 4: [3], 2: [1]},
    ),
    10: AlgorithmInfo(
        id=10,
        carriers=(1, 4),
        feedback_op=3,
        description="Dual 3-op Stacks: [6->5->4] + [3(FB)->2->1]",
        ascii_diagram=(
            "  [6]     [3]⮌\n"
            "   ↓       ↓\n"
            "  [5]     [2]\n"
            "   ↓       ↓\n"
            "  [4]🔊   [1]🔊\n"
            "─────────────"
        ),
        connections={6: [5], 5: [4], 3: [2], 2: [1]},
    ),
    11: AlgorithmInfo(
        id=11,
        carriers=(1, 4),
        feedback_op=6,
        description="Dual Stacks: [6->4, 5->4] + [3->2->1] (FB on 6)",
        ascii_diagram=(
            " [6]⮌ [5]   [3]\n"
            "   ↘   ↙     ↓\n"
            "    [4]🔊   [2]\n"
            "             ↓\n"
            "            [1]🔊\n"
            "─────────────"
        ),
        connections={6: [4], 5: [4], 3: [2], 2: [1]},
    ),
    12: AlgorithmInfo(
        id=12,
        carriers=(1, 3, 4, 5),
        feedback_op=6,
        description="One Master Modulator [6] feeding [5, 4, 3] + [2->1]",
        ascii_diagram=(
            "     [6]⮌     [2]\n"
            "    ↙  ↓  ↘    ↓\n"
            "  [5]🔊[4]🔊[3]🔊[1]🔊\n"
            "───────────────────"
        ),
        connections={6: [5, 4, 3], 2: [1]},
    ),
    13: AlgorithmInfo(
        id=13,
        carriers=(1, 4, 5),
        feedback_op=6,
        description="Modulator [6] feeding [5, 4] + 3-op stack [3->2->1]",
        ascii_diagram=(
            "   [6]⮌     [3]\n"
            "   ↙  ↘      ↓\n"
            " [5]🔊 [4]🔊 [2]\n"
            "             ↓\n"
            "            [1]🔊\n"
            "─────────────"
        ),
        connections={6: [5, 4], 3: [2], 2: [1]},
    ),
    14: AlgorithmInfo(
        id=14,
        carriers=(1, 3, 5),
        feedback_op=6,
        description="Modulator [6] feeding [5, 4->3] + [2->1]",
        ascii_diagram=(
            "   [6]⮌\n"
            "   ↙  ↘\n"
            " [5]🔊 [4]   [2]\n"
            "        ↓     ↓\n"
            "       [3]🔊 [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5, 4], 4: [3], 2: [1]},
    ),
    15: AlgorithmInfo(
        id=15,
        carriers=(1, 3, 5),
        feedback_op=2,
        description="Modulator [6] feeding [5, 4->3] + [2(FB)->1]",
        ascii_diagram=(
            "   [6]\n"
            "   ↙  ↘\n"
            " [5]🔊 [4]   [2]⮌\n"
            "        ↓     ↓\n"
            "       [3]🔊 [1]🔊\n"
            "─────────────────"
        ),
        connections={6: [5, 4], 4: [3], 2: [1]},
    ),
    16: AlgorithmInfo(
        id=16,
        carriers=(1,),
        feedback_op=6,
        description="Single Tower: 6-operator deep FM stack [6->5->4->3->2->1]",
        ascii_diagram=(
            "  [6]⮌\n"
            "   ↓\n"
            "  [5]\n"
            "   ↓\n"
            "  [4]\n"
            "   ↓\n"
            "  [3]\n"
            "   ↓\n"
            "  [2]\n"
            "   ↓\n"
            "  [1]🔊\n"
            "───────"
        ),
        connections={6: [5], 5: [4], 4: [3], 3: [2], 2: [1]},
    ),
    17: AlgorithmInfo(
        id=17,
        carriers=(1,),
        feedback_op=2,
        description="Single Tower: 6-operator deep FM stack (FB on OP2)",
        ascii_diagram=(
            "  [6]\n"
            "   ↓\n"
            "  [5]\n"
            "   ↓\n"
            "  [4]\n"
            "   ↓\n"
            "  [3]\n"
            "   ↓\n"
            "  [2]⮌\n"
            "   ↓\n"
            "  [1]🔊\n"
            "───────"
        ),
        connections={6: [5], 5: [4], 4: [3], 3: [2], 2: [1]},
    ),
    18: AlgorithmInfo(
        id=18,
        carriers=(1,),
        feedback_op=3,
        description="Single Carrier: Parallel modulator branches into [1]",
        ascii_diagram=(
            "  [6]\n"
            "   ↓\n"
            "  [5]   [3]⮌\n"
            "   ↓     ↓\n"
            "  [4]   [2]\n"
            "   ↘   ↙\n"
            "    [1]🔊\n"
            "─────────"
        ),
        connections={6: [5], 5: [4], 4: [1], 3: [2], 2: [1]},
    ),
    19: AlgorithmInfo(
        id=19,
        carriers=(1,),
        feedback_op=6,
        description="Single Carrier: [6->5->4, 6->3, 2->1]",
        ascii_diagram=(
            "   [6]⮌\n"
            "  ↙  ↘\n"
            " [5]  [3]  [2]\n"
            "  ↓    ↘  ↙\n"
            " [4]    [1]🔊\n"
            "  ↓\n"
            " [1]🔊\n"
            "─────────────"
        ),
        connections={6: [5, 3], 5: [4], 4: [1], 3: [1], 2: [1]},
    ),
    20: AlgorithmInfo(
        id=20,
        carriers=(1, 2, 3),
        feedback_op=3,
        description="Three Carriers: [3(FB)], [6->2], [5->1, 4->1]",
        ascii_diagram=(
            "  [3]⮌   [6]   [5] [4]\n"
            "   ↓      ↓      ↘ ↙\n"
            "  [3]🔊  [2]🔊   [1]🔊\n"
            "─────────────────────"
        ),
        connections={6: [2], 5: [1], 4: [1]},
    ),
    21: AlgorithmInfo(
        id=21,
        carriers=(1, 2, 3),
        feedback_op=6,
        description="Three Carriers: [6->3], [5->2], [4->1]",
        ascii_diagram=(
            "  [6]⮌   [5]    [4]\n"
            "   ↓      ↓      ↓\n"
            "  [3]🔊  [2]🔊  [1]🔊\n"
            "─────────────────────"
        ),
        connections={6: [3], 5: [2], 4: [1]},
    ),
    22: AlgorithmInfo(
        id=22,
        carriers=(1, 2, 3, 4),
        feedback_op=6,
        description="Four Carriers: [6->5->4], [3], [2], [1]",
        ascii_diagram=(
            "   [6]⮌\n"
            "    ↓\n"
            "   [5]\n"
            "    ↓\n"
            "  [4]🔊 [3]🔊 [2]🔊 [1]🔊\n"
            "─────────────────────────"
        ),
        connections={6: [5], 5: [4]},
    ),
    23: AlgorithmInfo(
        id=23,
        carriers=(1, 2, 3, 4),
        feedback_op=6,
        description="Four Carriers: [6->5->4], [3], [2], [1] (FB on 6)",
        ascii_diagram=(
            "  [6]⮌\n"
            "   ↓\n"
            "  [5]\n"
            "  ↙ ↘\n"
            " [4]🔊[3]🔊 [2]🔊 [1]🔊\n"
            "─────────────────────────"
        ),
        connections={6: [5], 5: [4, 3]},
    ),
    24: AlgorithmInfo(
        id=24,
        carriers=(1, 2, 3, 4),
        feedback_op=6,
        description="Four Carriers: [6->5, 6->4], [3], [2], [1]",
        ascii_diagram=(
            "    [6]⮌\n"
            "   ↙    ↘\n"
            " [5]🔊  [4]🔊 [3]🔊 [2]🔊 [1]🔊\n"
            "───────────────────────────────"
        ),
        connections={6: [5, 4]},
    ),
    25: AlgorithmInfo(
        id=25,
        carriers=(1, 2, 3, 4, 5),
        feedback_op=6,
        description="Five Carriers: Single Modulator [6] feeding [5], plus [4,3,2,1]",
        ascii_diagram=(
            "   [6]⮌\n"
            "    ↓\n"
            "  [5]🔊 [4]🔊 [3]🔊 [2]🔊 [1]🔊\n"
            "───────────────────────────────"
        ),
        connections={6: [5]},
    ),
    26: AlgorithmInfo(
        id=26,
        carriers=(1, 2, 3),
        feedback_op=6,
        description="Three Carriers: [6->5], [4->3], [2], [1]",
        ascii_diagram=(
            "  [6]⮌   [4]\n"
            "   ↓      ↓\n"
            "  [5]    [3]🔊  [2]🔊  [1]🔊\n"
            "   ↓\n"
            "  [3]🔊\n"
            "─────────────────────────────"
        ),
        connections={6: [5], 5: [3], 4: [3]},
    ),
    27: AlgorithmInfo(
        id=27,
        carriers=(1, 2, 3),
        feedback_op=3,
        description="Three Carriers: [6->5->4->2], [3(FB)], [1]",
        ascii_diagram=(
            "  [6]     [3]⮌\n"
            "   ↓       ↓\n"
            "  [5]     [3]🔊\n"
            "   ↓\n"
            "  [4]\n"
            "   ↓\n"
            "  [2]🔊         [1]🔊\n"
            "─────────────────────"
        ),
        connections={6: [5], 5: [4], 4: [2]},
    ),
    28: AlgorithmInfo(
        id=28,
        carriers=(1, 3, 5),
        feedback_op=2,
        description="Three Carriers: [6->5], [4->3], [2(FB)->1] with cross-modulation",
        ascii_diagram=(
            "  [6]    [4]   [2]⮌\n"
            "   ↓      ↓     ↓\n"
            "  [5]🔊  [3]🔊 [1]🔊\n"
            "─────────────────────"
        ),
        connections={6: [5], 4: [3], 2: [1]},
    ),
    29: AlgorithmInfo(
        id=29,
        carriers=(1, 2, 3, 4, 5),
        feedback_op=6,
        description="Five Carriers: [6->5], [4], [3], [2], [1]",
        ascii_diagram=(
            "   [6]⮌\n"
            "    ↓\n"
            "  [5]🔊 [4]🔊 [3]🔊 [2]🔊 [1]🔊\n"
            "───────────────────────────────"
        ),
        connections={6: [5]},
    ),
    30: AlgorithmInfo(
        id=30,
        carriers=(1, 2, 3, 4, 5),
        feedback_op=5,
        description="Five Carriers: [5(FB)->4], [3], [2], [1], [6]",
        ascii_diagram=(
            "   [5]⮌\n"
            "    ↓\n"
            "  [4]🔊 [3]🔊 [2]🔊 [1]🔊 [6]🔊\n"
            "───────────────────────────────"
        ),
        connections={5: [4]},
    ),
    31: AlgorithmInfo(
        id=31,
        carriers=(1, 2, 3, 4, 5, 6),
        feedback_op=6,
        description="All 6 Carriers: Additive synthesis with [6] self-feedback",
        ascii_diagram=(
            "  [6]⮌\n"
            "   ↓\n"
            "  [6]🔊 [5]🔊 [4]🔊 [3]🔊 [2]🔊 [1]🔊\n"
            "─────────────────────────────────────"
        ),
        connections={},
    ),
    32: AlgorithmInfo(
        id=32,
        carriers=(1, 2, 3, 4, 5, 6),
        feedback_op=6,
        description="Pure Additive Synthesis: 6 independent carrier sinewaves",
        ascii_diagram=(
            "  [6]⮌\n"
            "  [6]🔊 [5]🔊 [4]🔊 [3]🔊 [2]🔊 [1]🔊\n"
            "─────────────────────────────────────"
        ),
        connections={},
    ),
}


def get_algorithm(alg_id: int) -> AlgorithmInfo:
    """Retrieve algorithm metadata by 1-based ID (1..32)."""
    if not 1 <= alg_id <= 32:
        raise ValueError(f"Algorithm ID must be 1-32, got {alg_id}")
    return ALGORITHMS[alg_id]


def is_carrier(alg_id: int, op_num: int) -> bool:
    """Check if operator `op_num` is a carrier in algorithm `alg_id`."""
    return get_algorithm(alg_id).is_carrier(op_num)


def get_carrier_ops(alg_id: int) -> Tuple[int, ...]:
    """Get list of carrier operator numbers for algorithm `alg_id`."""
    return get_algorithm(alg_id).carriers


def get_modulator_ops(alg_id: int) -> Tuple[int, ...]:
    """Get list of modulator operator numbers for algorithm `alg_id`."""
    return get_algorithm(alg_id).modulators
