export interface Point2D {
  x: number;
  y: number;
}

export type AirInkSourceType = "Camera" | "Mock" | "Playback";

export type AirInkGestureState =
  | "HOVER"
  | "ARMING_DOWN"
  | "INKING"
  | "ARMING_UP"
  | "HAND_LOST";

export interface AirInkFrame {
  timestamp_ms: number;
  frame_id: number;
  source_type: AirInkSourceType;
  camera: {
    width: number;
    height: number;
    fps: number;
  };
  tracking: {
    hand_detected: boolean;
    confidence: number;
    landmarks: Point2D[];
    raw_tip: Point2D | null;
    stable_tip: Point2D | null;
    pinch_ratio: number | null;
    extension_ratio: number | null;
  };
  gesture: {
    state: AirInkGestureState;
    drawing_active: boolean;
  };
  quality: {
    tracking_ok: boolean;
    jump_rejected: boolean;
    frame_dropped: boolean;
  };
}
