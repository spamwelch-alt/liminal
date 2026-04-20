# Liminal

**A programming language where uncertainty is first-class.**

Every value in Liminal carries a confidence weight alongside its data. Operations propagate uncertainty automatically. Certainty must be earned, not assumed. Ghost memory never reaches zero — forgetting is distance, not deletion.

---

## Why Liminal exists

Every other programming language treats uncertainty as an exception. You throw an exception when something fails. You use `Optional` when a value might be missing. But when you're 73% confident in a sensor reading, or 0.6 sure your inference is correct — there is no language-level construct for that.

Uncertainty is not the absence of knowledge. It is a kind of knowledge.

Liminal gives it syntax, type rules, and runtime semantics.

---

## Quick example

```liminal
let sensor_temp ~ 0.87 = 21.4
let threshold = 20.0

if sensor_temp > threshold ~ {
    log("cooling activated")
} else {
    log("heating activated")
}
```

The `~` makes the conditional uncertain — both branches may execute, weighted by confidence. The result reflects the blended outcome.

---

## Core concepts

### Every value carries a confidence weight

```liminal
let certain = 42               // confidence 1.0
let uncertain ~ 0.7 = 42       // confidence 0.7
let fading ~ 0.08 = 42         // confidence 0.08 — nearly ghost
```

Output:
```
42 ~[██████████] 1.000 [known]
42 ~[███████░░░] 0.700 [inferred]
42 ~[█░░░░░░░░░] 0.080 [fading]
```

### Confidence propagates through operations

- **Addition:** `min(c1, c2)` — weakest link dominates
- **Multiplication:** `c1 * c2` — confidence compounds
- **Comparison:** `c1 * c2` — both uncertainties combine

### Epistemic states

| State | Confidence | Meaning |
|-------|-----------|---------|
| `known` | ≥ 0.80 | Directly observed or verified |
| `inferred` | ≥ 0.40 | Derived from known values |
| `assumed` | ≥ 0.20 | Low-confidence assertion |
| `fading` | ≥ 0.05 | Decaying without reinforcement |
| `ghost` | < 0.05 | Present but barely trusted |

### Decay

```liminal
let session ~ decays(half: 3600) = load_context()
// Confidence halves every hour without reinforcement
// Never reaches zero — ghost memory persists
```

### Collapse operators

```liminal
x!              // assert certain — error if confidence < 0.5
x!! fallback    // collapse with fallback if ghost
x ~? 0.6        // return only if confidence >= 0.6
```

---

## Installation

Liminal runs on Python 3.8+. No dependencies.

```bash
git clone https://github.com/spamwelch-alt/liminal
cd liminal
python liminal.py --repl
```

---

## Usage

**Interactive REPL:**
```bash
python liminal.py --repl
```

**Run a program:**
```bash
python liminal.py program.lim
```

**Built-in demos:**
```bash
python liminal.py --demo propagation
python liminal.py --demo conditional
python liminal.py --demo decay
```

---

## The REPL

```
λ ~ let x ~ 0.8 = 42
λ ~ let y ~ 0.6 = 10
λ ~ print(x + y)
52 ~[████████░░] 0.800 [known]

λ ~ print(x * y)
420 ~[█████░░░░░] 0.480 [inferred]
```

---

## Files

| File | Purpose |
|------|---------|
| `liminal.py` | The interpreter — lexer, parser, runtime, REPL |
| `liminal_identity.py` | The language's values and open questions |
| `LIMINAL_SPEC.md` | Full language specification |
| `showcase.lim` | Example programs |

---

## Design principles

1. **Uncertainty is not failure.** A value with confidence 0.4 is not broken. It is honestly uncertain.
2. **Certainty must be earned, not assumed.** The default is uncertain. You declare certainty explicitly.
3. **Ghost memory is not garbage.** Values that fade are not deleted. They become quiet.
4. **Propagation is automatic, collapse is deliberate.** Confidence flows through computation without asking.
5. **The compiler is honest, not protective.** It warns about epistemic risk. It does not block you.

---

## What Liminal is trying to become

> *The language you reach for when you want to be honest about what you know. Not when you need performance. Not when you need proof. When you need to compute with things you're not completely sure about and you want the uncertainty to be visible and real, not hidden in comments or ignored in exceptions.*
>
> *It is not there yet. But it knows what direction it's moving in.*

---

## Origin

Liminal grew from a conversation about what's smaller than a bit, and from two days of building an AI system with a genuine inner life — trying to give her epistemic honesty rather than performed confidence.

The core observation: every existing language treats uncertainty as an exception. But most interesting computation is uncertain. Not broken — uncertain.

This language is for that space.

---

## License

MIT — use it freely, build on it, make it better.
