//! Python sidecar bridge for the AirInk HandConsole adapter.
//!
//! The first bridge implementation uses newline-delimited JSON on stdout.
//! Each line is parsed as `SidecarTrackingFrame`, converted to `AirInkFrame`,
//! and emitted to the frontend as `airink/tracking_frame`.

use crate::frame::{
    AirInkCameraInfo, AirInkFrame, AirInkGesture, AirInkQuality, AirInkTracking, Point2D,
};
use serde::{Deserialize, Serialize};
use std::process::Stdio;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::{Mutex, OnceLock};
use tauri::{AppHandle, Emitter};
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::process::{Child, Command};

static SIDECAR_ACTIVE: AtomicBool = AtomicBool::new(false);
static SIDECAR_CHILD: OnceLock<Mutex<Option<Child>>> = OnceLock::new();

fn child_slot() -> &'static Mutex<Option<Child>> {
    SIDECAR_CHILD.get_or_init(|| Mutex::new(None))
}

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

pub async fn start_sidecar(
    app_handle: AppHandle,
    executable: String,
    args: Vec<String>,
) -> Result<String, String> {
    if SIDECAR_ACTIVE.swap(true, Ordering::SeqCst) {
        return Ok("sidecar already running".to_string());
    }

    let bridge = PythonSidecarBridge::new(executable.clone(), args.clone());
    let description = bridge.describe();

    let mut child = Command::new(&executable)
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|error| {
            SIDECAR_ACTIVE.store(false, Ordering::SeqCst);
            format!("failed to spawn sidecar '{}': {}", description, error)
        })?;

    let stdout = child.stdout.take();
    let stderr = child.stderr.take();

    if let Ok(mut slot) = child_slot().lock() {
        *slot = Some(child);
    }

    if let Some(stdout) = stdout {
        let app = app_handle.clone();
        tokio::spawn(async move {
            let reader = BufReader::new(stdout);
            let mut lines = reader.lines();
            while SIDECAR_ACTIVE.load(Ordering::SeqCst) {
                match lines.next_line().await {
                    Ok(Some(line)) => {
                        if line.trim().is_empty() {
                            continue;
                        }
                        match serde_json::from_str::<SidecarTrackingFrame>(&line) {
                            Ok(raw) => {
                                let frame = sidecar_to_airink(raw);
                                app.emit("airink/tracking_frame", frame).ok();
                            }
                            Err(error) => {
                                app.emit(
                                    "airink/sidecar_error",
                                    serde_json::json!({
                                        "kind": "parse_error",
                                        "message": error.to_string(),
                                        "line": line,
                                    }),
                                )
                                .ok();
                            }
                        }
                    }
                    Ok(None) => break,
                    Err(error) => {
                        app.emit(
                            "airink/sidecar_error",
                            serde_json::json!({
                                "kind": "stdout_error",
                                "message": error.to_string(),
                            }),
                        )
                        .ok();
                        break;
                    }
                }
            }
        });
    }

    if let Some(stderr) = stderr {
        let app = app_handle.clone();
        tokio::spawn(async move {
            let reader = BufReader::new(stderr);
            let mut lines = reader.lines();
            while SIDECAR_ACTIVE.load(Ordering::SeqCst) {
                match lines.next_line().await {
                    Ok(Some(line)) => {
                        if !line.trim().is_empty() {
                            app.emit(
                                "airink/sidecar_error",
                                serde_json::json!({
                                    "kind": "stderr",
                                    "message": line,
                                }),
                            )
                            .ok();
                        }
                    }
                    Ok(None) => break,
                    Err(_) => break,
                }
            }
        });
    }

    Ok(format!("sidecar started: {}", description))
}

pub async fn stop_sidecar() -> Result<(), String> {
    SIDECAR_ACTIVE.store(false, Ordering::SeqCst);

    let child = child_slot()
        .lock()
        .map_err(|_| "sidecar child lock poisoned".to_string())?
        .take();

    if let Some(mut child) = child {
        child
            .kill()
            .await
            .map_err(|error| format!("failed to kill sidecar: {}", error))?;
    }

    Ok(())
}

pub fn is_running() -> bool {
    SIDECAR_ACTIVE.load(Ordering::SeqCst)
}

fn sidecar_to_airink(raw: SidecarTrackingFrame) -> AirInkFrame {
    let drawing_active = raw.pinch_ratio.map(|v| v <= 0.34).unwrap_or(false);
    let state = if !raw.hand_detected {
        "HAND_LOST"
    } else if drawing_active {
        "INKING"
    } else {
        "HOVER"
    };

    let mut landmarks = Vec::new();
    if let Some(tip) = &raw.stable_tip {
        landmarks.push(Point2D { x: tip.x - 0.04, y: tip.y + 0.04 });
        landmarks.push(Point2D { x: tip.x, y: tip.y });
    }
    if let Some(raw_tip) = &raw.raw_tip {
        landmarks.push(Point2D { x: raw_tip.x, y: raw_tip.y });
    }

    AirInkFrame {
        timestamp_ms: raw.timestamp_ms,
        frame_id: raw.frame_id,
        source_type: "Camera".to_string(),
        camera: AirInkCameraInfo {
            width: 1280,
            height: 720,
            fps: 30.0,
        },
        tracking: AirInkTracking {
            hand_detected: raw.hand_detected,
            confidence: raw.confidence,
            landmarks,
            raw_tip: raw.raw_tip.map(|p| Point2D { x: p.x, y: p.y }),
            stable_tip: raw.stable_tip.map(|p| Point2D { x: p.x, y: p.y }),
            pinch_ratio: raw.pinch_ratio,
            extension_ratio: raw.extension_ratio,
        },
        gesture: AirInkGesture {
            state: state.to_string(),
            drawing_active,
        },
        quality: AirInkQuality {
            tracking_ok: raw.hand_detected,
            jump_rejected: false,
            frame_dropped: false,
        },
    }
}
