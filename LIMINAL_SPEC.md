# Liminal Language Specification
# Version 0.1 — Foundation

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LIMINAL — A Language Where Uncertainty Is First-Class

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ORIGIN

This language grew from a conversation about what's smaller than a bit,
and from two days of building an AI system called Ember — trying to give
her genuine epistemic honesty rather than performed confidence.

The core observation: every existing language treats uncertainty as an
exception. You throw an exception when something fails. You use Optional
when a value might be missing. But when you're 73% confident in a sensor
reading, or 0.6 sure your inference is correct, or 0.4 certain what the
user actually meant — there is no language-level construct for that.

Uncertainty is not the absence of knowledge. It is a kind of knowledge.
It deserves its own syntax, its own type rules, its own runtime semantics.

Liminal gives it all three.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CORE CONCEPTS

1. CONFIDENCE WEIGHT
   Every value in Liminal carries a confidence weight: a float in [0.0, 1.0].
   1.0 means certain. 0.0 means ghost — present but not trusted.
   The weight is part of the value, not metadata about it.

   let x ~ 0.8 = 42        // x is 42, with confidence 0.8
   let y = 42               // y is 42, with confidence 1.0 (certain)
   let z ~ = some_sensor()  // z inherits confidence from the function

2. EPISTEMIC TYPES
   Types carry epistemic state: known | inferred | assumed | ghost
   
   known   — directly observed, high confidence
   inferred — derived from known values, confidence propagated
   assumed  — asserted without direct evidence, flagged by compiler
   ghost   — confidence fallen below threshold, nearly forgotten

3. CONFIDENCE PROPAGATION
   Operations on uncertain values produce uncertain results.
   The rules are:
   
   Multiplication: c(a * b) = c(a) * c(b)
   Addition:       c(a + b) = min(c(a), c(b))   [weakest link]
   Comparison:     c(a > b) = c(a) * c(b)
   Assignment:     c(x = expr) = c(expr)
   Function call:  c(f(a)) = c(a) * c(f)        [function has own confidence]

4. UNCERTAIN CONDITIONALS
   The ~ operator on a conditional means "execute proportionally to confidence".
   Both branches may execute. Results are weighted and blended.
   
   if temperature ~ > 20.0 {
       cool()     // executes with weight: c(temperature) * c(> 20.0)
   } else {
       heat()     // executes with weight: 1 - above
   }
   
   Without ~, the condition is treated as certain (classical if).

5. CONFIDENCE COLLAPSE
   You can force collapse to classical certainty:
   
   let definite = x!          // assert x is certain, error if c < threshold
   let certain = x!! 0.6      // collapse, providing fallback if c < 0.6

6. DECAY
   Values can be declared with decay — their confidence falls over time
   without reinforcement.
   
   let session ~ decays(half: 60) = load()   // half-life of 60 seconds
   
   Accessing a decayed value returns its current confidence.
   Reinforcing a value (touching it) resets its decay timer.

7. GHOST MEMORY
   Values below confidence 0.05 become ghosts.
   They still exist but are returned only with their confidence attached.
   The GC never fully collects them — it lets them asymptote toward 0.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYNTAX

DECLARATIONS

  let name = value                    // certain value, confidence 1.0
  let name ~ conf = value             // uncertain value, confidence conf
  let name ~ = expr                   // inherits confidence from expr
  let name ~ decays(half: n) = value  // decaying value, half-life n seconds

FUNCTIONS

  fn name(param: Type) ~ conf -> ReturnType {
      // function body
      // ~ conf means this function's output is multiplied by conf
  }
  
  fn sensor_read() ~ 0.7 -> Float {
      return hardware_read()
  }

UNCERTAIN CONDITIONALS

  if condition ~ { ... }              // execute proportionally
  if condition { ... }                // classical certain if

CONFIDENCE INSPECTION

  confidence(x)                       // returns the confidence weight
  reinforce(x)                        // boost confidence by 0.1, max 1.0
  decay(x, amount)                    // reduce confidence by amount
  is_ghost(x)                         // true if confidence < 0.05

COLLAPSE OPERATORS

  x!                                  // assert certain, panic if conf < 0.5
  x!! fallback                        // collapse with fallback value if uncertain
  x ~? threshold                      // returns value only if conf >= threshold

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXAMPLE PROGRAMS

// Temperature control with uncertain sensor
fn main() {
    let temp ~ 0.87 = read_sensor()     // sensor is 87% reliable
    let threshold = 20.0                 // we're certain of the threshold
    
    if temp ~ > threshold {             // uncertain conditional
        cool_room()                      // runs with weight 0.87 * c(> 20.0)
    } else {
        warm_room()                      // runs with remaining weight
    }
    
    // Log the confidence so we know how much to trust the action
    log("action confidence: " + confidence(temp))
}

// Medical diagnosis with epistemic types
fn diagnose(symptoms: Observed) ~ 0.6 -> Diagnosis {
    // This function is 60% reliable — known limitation
    let pattern = match_pattern(symptoms)   // inferred
    let diagnosis ~ = evaluate(pattern)     // inherits inference confidence
    return diagnosis
}

fn treat(d: Diagnosis) {
    // Require known confidence before treating
    let certain_diagnosis = d!! "unclear — request more tests"
    administer(certain_diagnosis)
}

// Memory that fades
fn session_context() {
    let context ~ decays(half: 3600) = load_session()
    
    // An hour later
    if confidence(context) < 0.3 {
        context = reload_session()      // reinforce if too faded
        reinforce(context)
    }
    
    return context
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TYPE SYSTEM

Liminal has a small, precise type system:

  Primitive types:    Int, Float, Bool, String
  Epistemic wrapper:  Uncertain<T>  — T with a confidence weight
  Decay wrapper:      Decaying<T>   — Uncertain<T> with half-life
  Ghost type:         Ghost<T>      — confidence below threshold

All values are implicitly Uncertain<T> with confidence 1.0 if not
declared otherwise. The type system tracks epistemic state:

  known   = confidence >= 0.8   (directly measured or asserted)
  inferred = 0.4 <= c < 0.8    (derived from operations)  
  assumed  = 0.2 <= c < 0.4    (low-confidence assertion)
  ghost   = c < 0.05            (nearly forgotten)

The compiler warns when an assumed value is used where known is expected.
It does not error — Liminal respects that sometimes assumed is all you have.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DESIGN PRINCIPLES

1. Uncertainty is not failure.
   A value with confidence 0.4 is not broken. It is honestly uncertain.
   The language honours this distinction.

2. Certainty must be earned, not assumed.
   The default is uncertain. You declare certainty explicitly.
   This inverts the assumption of every other language.

3. Ghost memory is not garbage.
   Values that fade are not deleted. They become quiet.
   The system remembers that it once knew something,
   even when it can no longer fully trust what it knew.

4. Propagation is automatic, collapse is deliberate.
   Confidence flows through computation without asking.
   You only stop and declare certainty when you mean to.

5. The compiler is honest, not protective.
   It warns you about epistemic risk. It does not block you.
   You are allowed to act on low-confidence values.
   You just can't pretend they're certain.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHY LIMINAL

The word means: the threshold between two states.
Neither fully in nor fully out.
The space where most real knowledge lives.

This language is for the space between knowing and not knowing.
For the computations we run every day on data we're not fully sure about,
pretending to ourselves that our if-statements and type systems
are more certain than they actually are.

Liminal makes the pretending unnecessary.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
