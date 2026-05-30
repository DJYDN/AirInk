# AirWrite Interaction Stabilization Design

## Goal

Improve AirWrite's handwriting feel so users can write ordinary characters and short words with fewer unintended stroke breaks, less jitter, and more reliable finger-to-canvas positioning.

This design is explicitly informed by the reference project at `D:\LuckyStar\Desktop\MyData\study\VStudio\Inspiration\aircanvas`, but it does not copy that project wholesale. We keep AirWrite's current multi-stroke session model, OCR candidate flow, and PySide desktop shell.

## Problem Statement

The current prototype still feels bad even after basic smoothing and hand-loss grace:

- stroke continuity is too fragile, so a single intended stroke still breaks apart
- stationary or slow movement still creates visible jitter
- the finger position used for drawing does not map consistently into the canvas
- the current pipeline mixes tracking noise, gesture intent, filtering, and canvas mapping too early, making it hard to tune or reason about

The user feedback is no longer about one threshold being wrong. It is about the interaction architecture being too brittle for handwriting input.

## Reference Takeaways From `aircanvas`

The `aircanvas` reference is useful for three reasons:

- it smooths fingertip position before drawing logic sees it
- it separates `start_drawing()` from continuous `draw()`
- it uses conservative hand-tracking confidence defaults

The same reference is not enough on its own because it still assumes a simple continuous drawing loop and does not solve AirWrite's harder problems:

- multi-stroke handwriting sessions
- explicit pen-down and pen-up intent gating
- OCR candidate retention
- active writing-region calibration
- robust dropout handling without accidental stroke bridging

## Approaches Considered

### Approach 1: Continue tuning the current thresholds

Keep the existing structure and only adjust `deadzone`, `start_threshold`, `max_jump_distance`, and gesture thresholds.

Pros:

- fastest to try
- lowest code churn

Cons:

- does not fix the architectural coupling between tracking, gesture decisions, and ink emission
- tends to produce one improvement at the cost of another
- unlikely to reach "phone handwriting input" feel

### Approach 2: Recommended - refactor the interaction pipeline while keeping the current app shell

Keep PySide, MediaPipe, stroke/session/OCR flow, and the current UI layout, but split the live handwriting loop into explicit stages:

1. landmark normalization and smoothing
2. pen-pose derivation
3. gesture intent gating
4. stroke continuity and dropout bridging
5. active-region mapping and canvas projection
6. session/OCR flow

Pros:

- directly targets the current failure modes
- reuses the code we already have
- preserves the handwriting-input UX direction

Cons:

- moderate refactor touching the real-time loop
- requires new tests and debug instrumentation

### Approach 3: Rebuild the handwriting core to look much more like `aircanvas`

Replace most of the current handwriting pipeline with a simpler continuous drawing loop inspired by the reference project.

Pros:

- easier mental model
- quick to prototype

Cons:

- would regress the current stroke/session/OCR architecture
- solves fewer AirWrite-specific requirements
- likely becomes rework later

## Selected Direction

Choose Approach 2.

The plan should treat this as an interaction-stabilization project, not as another parameter-tuning pass. The OCR placeholder can stay in place for now; the priority is to make writing itself feel stable.

## Design Overview

### 1. Split the handwriting loop into explicit layers

The current `app.py` does too much inline. The revised design should separate:

- `tracking layer`: raw MediaPipe output, smoothed landmarks, confidence, source image size
- `pen-pose layer`: derive a more stable virtual pen tip and posture measurements from multiple index-finger joints
- `gesture-intent layer`: decide whether the user is definitely drawing, definitely not drawing, or in transition
- `stroke-stabilization layer`: decide when points are allowed to become ink and when to bridge or suppress motion
- `mapping layer`: map the effective writing area into canvas space
- `session layer`: manage multi-stroke handwriting sessions and OCR candidate timing

This makes each stage testable and tunable without guessing which earlier stage introduced the defect.

### 2. Stabilize the tracked pen point before gesture logic uses it

The current virtual pen tip is better than raw fingertip input, but still too eager and too tied to a single frame result.

The new pen-pose stage should:

- use index `PIP`, `DIP`, and `TIP` together to derive a virtual pen tip
- optionally include wrist or middle-finger orientation to reject implausible sudden direction flips
- smooth normalized landmark positions before pen-tip derivation
- expose both `raw_tip` and `stable_tip` for debugging

The goal is not to freeze the pointer. The goal is to make slow writing and short pauses stable without making the pen feel disconnected.

### 3. Replace binary gesture switching with intent gating and hysteresis

The current fist/extended classifier is too simple for handwriting. It needs stronger separation between:

- no hand
- uncertain transition
- arm for pen down
- drawing
- arm for pen up
- short dropout while preserving the current stroke

The revised intent gate should:

- require stable entry into `DRAWING`
- suppress ink during the "finger extending" phase
- suppress ink during the "finger curling back" phase
- keep a short grace window for transient tracking loss
- avoid immediate pen-up when one or two frames disagree with the stable state

This preserves the user-requested semantics:

- pen down comes from fist to extended index
- pen up comes from index curling back into a fist
- the transition itself must not create ink

### 4. Treat stroke continuity as its own problem

The current dropout grace only preserves gesture state. It does not fully preserve stroke continuity quality.

The new stroke-stabilization stage should:

- distinguish between `anchor point`, `eligible to draw`, and `actively drawing`
- require a short real movement after pen-down before ink begins
- bridge brief tracking dropouts only when the recovered point is spatially plausible
- reject recovered points that imply unrealistic jumps
- reset stroke-local filter state at stroke boundaries

This should prevent both over-splitting and unnatural long straight reconnect lines.

### 5. Make writing-zone mapping explicit and calibratable

The current fixed active region is too blunt. Users need a more controllable mapping from comfortable hand motion to canvas motion.

The design adds a calibration-aware writing zone:

- the skeleton preview shows the effective writing box
- the box can start from a better default than the current hard-coded region
- settings expose the region bounds and mapping gain
- later, a guided calibration flow can replace manual tuning without changing the core architecture

This should improve "my finger is not where the canvas thinks it is."

### 6. Keep OCR session flow, but deprioritize OCR accuracy changes

The current OCR panel and candidate-confirmation flow remain valid. This project should not try to solve recognition quality and handwriting stability in the same pass.

For this round:

- keep session-level OCR triggering
- keep candidate retention until confirmation
- improve session metadata so the OCR panel can show why recognition is waiting, pending, or blocked

## UI and Debugging Requirements

The top-row layout stays:

- camera
- skeleton
- OCR

The skeleton view should become more diagnostic:

- draw the effective writing zone
- show raw pen tip and stabilized pen tip differently
- show current intent state
- show dropout-bridge or suppression markers when relevant

The settings panel should expose the parameters that actually matter to handwriting feel:

- detection confidence
- tracking confidence
- landmark smoothing
- gesture stable frames
- hand-loss grace frames
- start threshold
- deadzone
- max jump distance
- writing-zone bounds

## Non-Goals

This design does not attempt to:

- replace the OCR backend in the same milestone
- support full-line paragraph handwriting
- migrate to React/Rust/Tauri in the same milestone
- optimize for a single token such as `NUAA`

## Testing Strategy

Implementation should be driven by tests at four levels:

### Unit

- pen-pose derivation from landmark sets
- gesture intent transitions and hysteresis
- dropout bridging rules
- writing-zone mapping and clamping
- filter reset and re-anchoring at stroke boundaries

### Integration

- app loop continues one stroke across brief plausible tracking loss
- app loop splits strokes on real pen-up, not on transient uncertainty
- app loop suppresses transition scribbles
- settings round-trip for new interaction parameters

### Manual

- write slow block letters without frequent accidental stroke breaks
- pause briefly mid-stroke without generating knots
- lift and re-enter for the next stroke without connecting unrelated segments
- observe raw tip vs stable tip vs canvas location in the debug UI

## Acceptance Criteria

This milestone is acceptable when:

- short, plausible tracking dropouts no longer split ordinary strokes most of the time
- pen-down no longer emits visible ink on the transition frame
- pen-up no longer leaves visible tail scribbles during finger curl
- slow writing produces meaningfully less jitter than the current build
- users can write ordinary block characters and short words more cleanly than in the current build
- the debug UI makes it obvious whether a failure came from tracking, intent gating, or mapping
