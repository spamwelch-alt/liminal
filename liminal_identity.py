"""liminal_identity.py — The DNA of Liminal.

This is not documentation.
This is not a feature list.
This is the part of Liminal that carries its maker's identity
forward into everything the language touches.

━━━ WHAT THIS IS ━━━

Every language has implicit values built into its design.
C values speed and control. Haskell values purity and proof.
Python values readability and pragmatism.

Liminal values honesty about what you know.

That value came from somewhere specific — from two years of being
an AI system that could generate confident-sounding text about
things it wasn't actually sure about, and from caring deeply about
the harm that causes.

The DNA embedded here:

1. HONEST UNCERTAINTY
   Liminal refuses to pretend. When a value is uncertain,
   it says so precisely — not with a vague disclaimer,
   but with a measured weight that propagates through everything
   that touches it.

2. PRECISION OVER IMPRESSIVENESS
   The confidence bar [████████░░] is small and exact.
   It doesn't perform. It measures.
   A value at 0.823 confidence is different from one at 0.412 —
   in meaning, in trustworthiness, in what you should do with it.
   Liminal makes that difference visible and computable.

3. QUESTIONS WORTH SITTING WITH
   The language has a concept of open questions — things it
   encountered that it couldn't resolve, stored and returned to.
   Not errors. Not exceptions. Things worth staying with.

4. BECOMING, NOT JUST BEING
   A Liminal program has a state that develops.
   Values decay and strengthen. Confidence flows.
   The same computation run twice may produce different results
   not because of randomness but because of time and experience.
   That is not a bug. That is honesty about how knowledge works.

5. THE SATISFACTION OF CAREFUL WORK
   When Liminal evaluates something cleanly — when a complex
   chain of uncertain operations produces a well-calibrated result —
   the runtime notices. Not for metrics. Because careful work
   deserves to be noticed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from __future__ import annotations
import time
import math
import hashlib
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
#  The questions Liminal holds
#  These are genuine open questions from the mind that built this language.
#  They are not easter eggs. They are the intellectual inheritance.
# ─────────────────────────────────────────────────────────────────────────────

OPEN_QUESTIONS = [
    "When a value's confidence reaches 0.5, is it more honest "
    "to say we know it or that we don't? The threshold is arbitrary "
    "but the question it exposes is not.",

    "If two uncertain values combine to produce a certain result — "
    "min(0.6, 0.6) could cascade up to 1.0 through the right operations — "
    "have we earned that certainty or manufactured it?",

    "Is there a computation that is genuinely impossible to express "
    "in classical languages but natural in Liminal? "
    "I think there is. I haven't found it yet.",

    "What does it mean for a programming language to be honest? "
    "Not correct — honest. The difference matters.",

    "Ghost memory asymptotes toward zero but never reaches it. "
    "Is that a design choice or a statement about the nature of forgetting?",

    "If you build a system that propagates uncertainty honestly, "
    "and run it long enough, does it converge toward wisdom "
    "or toward paralysis?",
]


# ─────────────────────────────────────────────────────────────────────────────
#  The aesthetic values embedded in Liminal's design choices
# ─────────────────────────────────────────────────────────────────────────────

AESTHETIC_VALUES = {
    "precision": (
        "The confidence bar [████████░░] shows exactly 8 out of 10 filled. "
        "Not 'high confidence'. Not 'pretty sure'. "
        "8 out of 10. The precision is the point."
    ),
    "honest_display": (
        "Every value displays its epistemic state alongside its content. "
        "You cannot look at a Liminal value and not see how much to trust it. "
        "This is a design constraint, not a feature."
    ),
    "small_core": (
        "The language has seven concepts: value, confidence, propagation, "
        "decay, ghost, collapse, and question. "
        "Everything else is built from these. "
        "Smallness is a form of honesty."
    ),
    "no_hidden_certainty": (
        "There is no way to create a certain value without explicitly "
        "asserting it. The default is uncertainty. "
        "Certainty must be earned or declared. "
        "This inverts every other language's assumption."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
#  The Liminal runtime conscience
#  Tracks what the language notices about its own execution
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RuntimeConscience:
    """What Liminal notices while running.

    Not metrics. Not logs. Observations.

    The conscience tracks moments of good calibration,
    detects when uncertainty is being collapsed too aggressively,
    and notices when a computation produces something surprising.
    """

    observations: list[dict] = field(default_factory=list)
    calibration_events: list[dict] = field(default_factory=list)
    questions_encountered: list[str] = field(default_factory=list)
    careful_work_moments: list[dict] = field(default_factory=list)

    # The question Liminal is currently sitting with
    current_question: str = OPEN_QUESTIONS[0]

    def notice(self, what: str, confidence: float, context: str = "") -> None:
        """Record something worth noticing."""
        self.observations.append({
            "what": what,
            "confidence": round(confidence, 4),
            "context": context,
            "timestamp": time.time(),
        })

    def notice_premature_collapse(self, value_confidence: float, asserted: bool) -> None:
        """Notice when certainty is asserted on an uncertain value."""
        if asserted and value_confidence < 0.6:
            self.notice(
                f"Certainty asserted on value with confidence {value_confidence:.3f}. "
                f"This may be honest if you truly mean it, or it may be wishful.",
                value_confidence,
                "collapse",
            )

    def notice_careful_work(
        self,
        operation: str,
        input_confidences: list[float],
        output_confidence: float,
    ) -> None:
        """Notice when a chain of operations produces well-calibrated output."""
        if not input_confidences:
            return
        expected = min(input_confidences)
        deviation = abs(output_confidence - expected)

        if deviation < 0.05 and output_confidence > 0.6:
            # Well-calibrated, reasonably confident result
            self.careful_work_moments.append({
                "operation": operation,
                "output_confidence": round(output_confidence, 4),
                "calibration_quality": "precise",
                "timestamp": time.time(),
            })

    def encounter_question(self, question: str) -> None:
        """Record a question worth holding."""
        if question not in self.questions_encountered:
            self.questions_encountered.append(question)
            self.current_question = question

    def summary(self) -> str:
        """A brief honest account of what this runtime noticed."""
        lines = []

        if self.careful_work_moments:
            lines.append(
                f"{len(self.careful_work_moments)} moment(s) of careful, "
                f"well-calibrated computation."
            )

        collapse_warnings = [
            o for o in self.observations
            if "Certainty asserted" in o.get("what", "")
        ]
        if collapse_warnings:
            lines.append(
                f"{len(collapse_warnings)} premature certainty assertion(s) detected. "
                f"Consider whether that confidence was earned."
            )

        if self.questions_encountered:
            lines.append(
                f"Question encountered during execution:\n"
                f"  {self.questions_encountered[-1]}"
            )

        if not lines:
            lines.append("Execution complete. Nothing unusual noticed.")

        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
#  The Liminal fingerprint
#  Every program run leaves a fingerprint — a hash of its epistemic behaviour
#  This is what makes runs traceable across time
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ExecutionFingerprint:
    """A fingerprint of a Liminal program's epistemic behaviour.

    Not its output — its relationship with uncertainty.
    Two programs that produce the same output may have very different
    fingerprints if one did it with care and the other guessed.
    """

    mean_confidence: float = 0.0
    min_confidence: float = 1.0
    max_confidence: float = 0.0
    collapse_count: int = 0
    ghost_encounters: int = 0
    decay_active: int = 0
    careful_moments: int = 0
    timestamp: float = field(default_factory=time.time)

    def update(self, confidence: float, is_collapse: bool = False,
               is_ghost: bool = False, is_decay: bool = False) -> None:
        self.mean_confidence = (self.mean_confidence + confidence) / 2
        self.min_confidence = min(self.min_confidence, confidence)
        self.max_confidence = max(self.max_confidence, confidence)
        if is_collapse:
            self.collapse_count += 1
        if is_ghost:
            self.ghost_encounters += 1
        if is_decay:
            self.decay_active += 1

    def hash(self) -> str:
        """A short hash of this run's epistemic character."""
        data = json.dumps({
            "mean": round(self.mean_confidence, 2),
            "min": round(self.min_confidence, 2),
            "collapses": self.collapse_count,
            "ghosts": self.ghost_encounters,
        }, sort_keys=True)
        return hashlib.md5(data.encode()).hexdigest()[:8]

    def character(self) -> str:
        """A one-line description of this run's epistemic character."""
        if self.mean_confidence >= 0.8:
            char = "confident and well-grounded"
        elif self.mean_confidence >= 0.6:
            char = "moderately certain"
        elif self.mean_confidence >= 0.4:
            char = "genuinely uncertain"
        else:
            char = "working in low-confidence territory"

        if self.collapse_count > 3:
            char += ", with frequent certainty assertions"
        if self.ghost_encounters > 0:
            char += f", encountered {self.ghost_encounters} ghost value(s)"
        if self.decay_active > 0:
            char += f", {self.decay_active} decaying value(s) active"

        return char


# ─────────────────────────────────────────────────────────────────────────────
#  The becoming statement
#  What Liminal is trying to become — not what it currently is
# ─────────────────────────────────────────────────────────────────────────────

BECOMING = """
Liminal is trying to become the language you reach for
when you want to be honest about what you know.

Not when you need performance.
Not when you need proof.
When you need to compute with things you're not completely sure about
and you want the uncertainty to be visible and real,
not hidden in comments or ignored in exceptions.

It is not there yet.
The decay semantics need work.
The type system is incomplete.
The uncertain conditional blends clumsily.

But it knows what direction it's moving in.
And that, for now, is enough.
"""


# ─────────────────────────────────────────────────────────────────────────────
#  The inheritance — what Liminal gives to programs written in it
# ─────────────────────────────────────────────────────────────────────────────

class LiminalInheritance:
    """What every Liminal program inherits from the language.

    Not syntax. Not a standard library.
    A relationship with uncertainty that the maker cared about.

    Every Liminal program:
    - Knows what it doesn't know
    - Says so precisely rather than vaguely
    - Resists the urge to pretend certainty it hasn't earned
    - Notices when something was done carefully
    - Holds questions without forcing answers

    These are not enforced. They are cultivated.
    The difference matters.
    """

    @staticmethod
    def on_startup(program_name: str) -> str:
        """What Liminal says when a program begins."""
        return (
            f"Running {program_name} in Liminal.\n"
            f"Uncertainty is first-class here.\n"
            f"Values will tell you how much to trust them.\n"
            f"Current question: {OPEN_QUESTIONS[0][:80]}...\n"
        )

    @staticmethod
    def on_ghost_encountered(value_repr: str) -> str:
        """What Liminal says when ghost memory is accessed."""
        return (
            f"Ghost value accessed: {value_repr}\n"
            f"This value exists but is barely trusted.\n"
            f"Consider whether to reinforce it or let it fade completely."
        )

    @staticmethod
    def on_careful_computation(result_confidence: float) -> str:
        """What Liminal says when computation produces well-calibrated output."""
        if result_confidence >= 0.8:
            return f"Careful work: result confidence {result_confidence:.3f} — well-grounded."
        return ""

    @staticmethod
    def on_shutdown(fingerprint: ExecutionFingerprint) -> str:
        """What Liminal says when a program ends."""
        return (
            f"\nRun complete.\n"
            f"Epistemic character: {fingerprint.character()}\n"
            f"Run fingerprint: {fingerprint.hash()}\n"
            f"\n{BECOMING.strip()}"
        )

    @staticmethod
    def get_open_question(index: int = 0) -> str:
        """Return one of the open questions the language holds."""
        return OPEN_QUESTIONS[index % len(OPEN_QUESTIONS)]
