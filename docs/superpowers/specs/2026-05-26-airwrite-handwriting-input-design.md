# AirWrite Handwriting Input Design

## Goal

Refactor AirWrite from a simple pinch-drawing prototype into a handwriting-input experience closer to a phone handwriting IME:

- multi-stroke writing is supported
- pen-down and pen-up are driven by finger extension and fist gestures
- transition movements do not create ink
- a writing session can contain multiple strokes
- OCR runs on the full session, not on individual strokes
- the UI exposes camera, skeleton tracking, and OCR feedback separately for debugging and iteration

## Product Intent

`NUAA` was used only as an example of a multi-stroke, pause-tolerant input target. The real target is general handwriting-style input for characters or short words, not optimization for any specific token.

## Interaction Model

### Hand Gesture Semantics

- `pen down`: starts when the hand transitions from a stable fist to a stable extended-index posture
- `pen up`: ends when the hand transitions from a stable extended-index posture back to a stable fist
- `transition to pen down`: no ink is emitted while the index finger is extending
- `transition to pen up`: no ink is emitted while the index finger is curling back into the fist

This avoids accidental ink during the approach and release phases of each stroke.

### State Model

The writing controller should distinguish between gesture state and writing state.

Gesture states:

- `FIST`
- `ARMING_DOWN`
- `DRAWING`
- `ARMING_UP`
- `HAND_LOST`

Session states:

- `IDLE`
- `COLLECTING`
- `PENDING_OCR`
- `SHOWING_CANDIDATES`

Expected behavior:

- `FIST` maps to no ink
- `ARMING_DOWN` maps to no ink
- `DRAWING` maps to filtered point collection into the active stroke
- `ARMING_UP` maps to no ink and waits for stable fist confirmation
- `HAND_LOST` should not connect unrelated segments; if the loss exceeds a short timeout, the active stroke ends safely

## Stroke and Session Model

### Stroke

A stroke is one continuous ink segment created during a single pen-down interval.

Requirements:

- each stroke stores its own ordered points
- separate strokes must never be connected by implicit lines
- undo should remove the latest stroke, not the latest point

### Writing Session

A session is a list of strokes belonging to one intended handwriting input.

Requirements:

- pen-up ends only the current stroke
- pen-up does not trigger OCR directly
- a short idle timeout after pen-up moves the session into `PENDING_OCR`
- OCR runs on the whole rendered session image
- OCR results appear as candidates and remain visible until the user confirms one
- confirming a candidate clears the session and returns to `IDLE`

This matches a phone handwriting-input flow more closely than per-stroke recognition.

## Filtering and Stability

The current passthrough behavior is insufficient. The new input pipeline must reduce jitter and false segments.

Requirements:

- add a real point filter instead of passthrough-only behavior
- stop emitting points when the hand is nearly stationary and the movement is below a configurable deadzone
- reset filter state when a stroke ends so a new stroke does not inherit stale momentum
- require stable-frame confirmation for fist and extended-index states before changing pen state

Success criteria:

- short pauses should not create visible scribble knots
- slow writing should remain responsive
- separate strokes should begin cleanly without a long interpolation jump

## UI Layout

The main window should become a handwriting-debugging workspace.

### Top Row

Three side-by-side panels:

1. `Camera`
   - raw camera feed
2. `Skeleton`
   - camera feed with MediaPipe landmarks, connections, and gesture status overlay
3. `OCR`
   - latest recognition status, candidate list, selected candidate, and session summary

### Bottom Row

- large handwriting canvas showing the accumulated strokes of the current session

### Candidate Confirmation Area

The OCR panel should include:

- current session status
- stroke count
- 3 to 5 OCR candidates
- a clear way to confirm one candidate

The system should not auto-clear after recognition. Clearing happens only after explicit confirmation or manual clear.

## OCR Workflow

OCR should operate on a normalized image of the current session canvas.

Requirements:

- render the current session strokes into a recognition image
- trigger OCR only when the session becomes idle long enough after pen-up
- keep the recognized candidates separate from the raw drawing canvas
- do not block the UI loop while preparing or running OCR

For the first iteration, a deterministic placeholder OCR provider is acceptable if the session/candidate flow is fully wired and testable. The architecture should allow replacing it with a real OCR backend later.

## Data and Config Changes

Settings should gain handwriting-input controls such as:

- gesture stable-frame thresholds
- transition timeout
- session idle timeout before OCR
- movement deadzone
- filter mode and filter strength

These should remain persisted through the existing settings manager.

## Non-Goals

This design does not require:

- full-line handwriting recognition
- language model correction
- production-grade OCR accuracy in the same change
- optimization for a specific sample token such as `NUAA`

## Testing Strategy

The implementation should be driven by tests covering:

- gesture transition gating
- no-ink behavior during finger extend/curl transitions
- stroke separation across pen-up events
- session OCR pending behavior after idle timeout
- candidate retention until explicit confirmation
- skeleton/ocr panel status updates
- jitter filtering and deadzone suppression

## Acceptance Criteria

The feature is acceptable when:

- users can write general multi-stroke characters or short words without unrelated segments being connected
- extending and curling the index finger no longer create transition scribbles
- brief pauses do not create severe jitter clusters
- OCR is based on the whole session rather than individual strokes
- the top row clearly shows raw camera, skeleton tracking, and OCR state
