# Active Region Calibration Design

## Purpose

The application already supports mapping a normalized camera sub-region to the full drawing canvas. The missing part is a user-facing calibration flow that lets the user define that region without editing configuration files manually.

## User problem

A full camera frame is usually much larger than the natural writing motion range. Mapping the full frame to the canvas can make strokes feel too small, too large, or poorly positioned. Calibration lets the user define the area where writing gestures should be interpreted as the canvas.

## MVP calibration flow

1. User clicks a `Calibrate` button.
2. The app enters calibration mode and pauses stroke collection.
3. The app asks the user to point to the top-left corner of the intended writing area.
4. User confirms the point.
5. The app asks the user to point to the bottom-right corner.
6. User confirms the point.
7. The app validates the region.
8. The app saves the active region and resumes normal tracking.

## Data model

Store the region as normalized coordinates:

```json
{
  "tracking": {
    "active_region": {
      "left": 0.20,
      "right": 0.80,
      "top": 0.20,
      "bottom": 0.80
    }
  }
}
```

The runtime representation should remain compatible with the existing mapping function:

```python
active_region = (left, right, top, bottom)
```

## Validation rules

- `0.0 <= left < right <= 1.0`
- `0.0 <= top < bottom <= 1.0`
- Region width should be at least `0.05`.
- Region height should be at least `0.05`.
- Invalid calibration should not overwrite the previous valid region.

## UI changes

Recommended additions:

- Add a `Calibrate` button to the settings panel.
- Add a `Reset calibration` button.
- Show the active region rectangle in the skeleton preview.
- Show calibration instructions in the status bar.

## Implementation plan

1. Extend `TrackingSettings` with optional active-region fields.
2. Add parsing and validation in `AppSettings.from_dict`.
3. Add calibration state to `AirWriteApp`.
4. During calibration, read the current stable pen pose but do not add stroke points.
5. Save the region through `SettingsManager.save`.
6. Reuse `map_image_to_canvas(..., active_region=...)` during drawing.
7. Add unit tests for region validation and mapping behavior.

## Acceptance criteria

- User can calibrate the writing region without manually editing JSON.
- The skeleton preview shows the selected region.
- Drawing maps the calibrated region to the full canvas.
- Reset returns to full-frame mapping.
- Invalid calibration attempts are rejected and reported in the status bar.
