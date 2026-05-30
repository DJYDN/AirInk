//! Python sidecar bridge scaffold.
//!
//! This module is intentionally a skeleton. The adapter will initially reuse the
//! current AirInk Python tracking pipeline through a sidecar process rather than
//! rewriting camera and MediaPipe tracking in Rust.
//!
//! Expected sidecar transport options:
//!
//! 1. JSON Lines over stdout
//! 2. Local WebSocket
//! 3. Local TCP socket
//!
//! The first MVP should use JSON Lines because it is simple to debug and does
//! not require changing the existing AirInk runtime code.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarTrackingFrame {
    pub timestamp_ms: u64,
    pub frame_id: u64,
    pub hand_detected: bool,
    pub raw_tip: Option<SidecarPoint2D>,
    pub stable_tip: Option<SidecarPoint2D>,
    pub pinch_ratio: Option<f32>,
    pub extension_ratio: Option<f32>,
    pub confidence: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SidecarPoint2D {
    pub x: f32,
    pub y: f32,
}

pub struct PythonSidecarBridge {
    pub executable: String,
    pub args: Vec<String>,
}

impl PythonSidecarBridge {
    pub fn new(executable: impl Into<String>, args: Vec<String>) -> Self {
        Self {
            executable: executable.into(),
            args,
        }
    }

    pub fn describe(&self) -> String {
        format!("{} {}", self.executable, self.args.join(" "))
    }
}
