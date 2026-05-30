use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Point2D {
    pub x: f32,
    pub y: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AirInkCameraStatus {
    pub status: String,
    pub camera_index: u32,
    pub width: u32,
    pub height: u32,
    pub fps: f32,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AirInkCameraInfo {
    pub width: u32,
    pub height: u32,
    pub fps: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AirInkTracking {
    pub hand_detected: bool,
    pub confidence: f32,
    pub landmarks: Vec<Point2D>,
    pub raw_tip: Option<Point2D>,
    pub stable_tip: Option<Point2D>,
    pub pinch_ratio: Option<f32>,
    pub extension_ratio: Option<f32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AirInkGesture {
    pub state: String,
    pub drawing_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AirInkQuality {
    pub tracking_ok: bool,
    pub jump_rejected: bool,
    pub frame_dropped: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AirInkFrame {
    pub timestamp_ms: u64,
    pub frame_id: u64,
    pub source_type: String,
    pub camera: AirInkCameraInfo,
    pub tracking: AirInkTracking,
    pub gesture: AirInkGesture,
    pub quality: AirInkQuality,
}
