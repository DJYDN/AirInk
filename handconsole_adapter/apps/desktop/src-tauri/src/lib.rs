#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod frame;
mod sidecar;

use frame::{
    AirInkCameraInfo, AirInkCameraStatus, AirInkFrame, AirInkGesture, AirInkQuality,
    AirInkTracking, Point2D, SessionStatusEvent,
};
use sidecar::PythonSidecarBridge;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::LazyLock;
use tauri::{AppHandle, Emitter};
use tokio::time::{sleep, Duration};

static MOCK_RUNNING: LazyLock<AtomicBool> = LazyLock::new(|| AtomicBool::new(false));
static MOCK_FRAME_ID: LazyLock<AtomicU64> = LazyLock::new(|| AtomicU64::new(0));

#[tauri::command]
fn airink_get_camera_status() -> AirInkCameraStatus {
    AirInkCameraStatus {
        status: if MOCK_RUNNING.load(Ordering::SeqCst) {
            "running".to_string()
        } else {
            "idle".to_string()
        },
        camera_index: 0,
        width: 1280,
        height: 720,
        fps: if MOCK_RUNNING.load(Ordering::SeqCst) { 30.0 } else { 0.0 },
        error_message: None,
    }
}

#[tauri::command]
fn airink_emit_mock_frame(app_handle: AppHandle) -> Result<(), String> {
    let frame_id = MOCK_FRAME_ID.fetch_add(1, Ordering::SeqCst) + 1;
    let frame = build_mock_frame(frame_id, frame_id as f32 / 30.0);
    app_handle
        .emit("airink/tracking_frame", frame)
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn airink_start_mock_stream(app_handle: AppHandle) -> Result<(), String> {
    if MOCK_RUNNING.swap(true, Ordering::SeqCst) {
        return Ok(());
    }

    app_handle
        .emit("airink/camera_status", running_camera_status())
        .map_err(|e| e.to_string())?;
    app_handle
        .emit(
            "airink/session_status",
            SessionStatusEvent {
                status: "recording".to_string(),
                session_id: Some("mock_session".to_string()),
                stroke_count: 0,
            },
        )
        .map_err(|e| e.to_string())?;

    tokio::spawn(async move {
        while MOCK_RUNNING.load(Ordering::SeqCst) {
            let frame_id = MOCK_FRAME_ID.fetch_add(1, Ordering::SeqCst) + 1;
            let t = frame_id as f32 / 30.0;
            let frame = build_mock_frame(frame_id, t);
            app_handle.emit("airink/tracking_frame", frame).ok();
            sleep(Duration::from_millis(33)).await;
        }

        app_handle.emit("airink/camera_status", idle_camera_status()).ok();
        app_handle
            .emit(
                "airink/session_status",
                SessionStatusEvent {
                    status: "idle".to_string(),
                    session_id: None,
                    stroke_count: 0,
                },
            )
            .ok();
    });

    Ok(())
}

#[tauri::command]
fn airink_stop_mock_stream(app_handle: AppHandle) -> Result<(), String> {
    MOCK_RUNNING.store(false, Ordering::SeqCst);
    app_handle
        .emit("airink/camera_status", idle_camera_status())
        .map_err(|e| e.to_string())?;
    app_handle
        .emit(
            "airink/session_status",
            SessionStatusEvent {
                status: "idle".to_string(),
                session_id: None,
                stroke_count: 0,
            },
        )
        .map_err(|e| e.to_string())
}

#[tauri::command]
fn airink_describe_sidecar(executable: Option<String>, args: Option<Vec<String>>) -> String {
    let bridge = PythonSidecarBridge::new(
        executable.unwrap_or_else(|| "python".to_string()),
        args.unwrap_or_else(|| vec!["-m".to_string(), "airink_sidecar".to_string()]),
    );
    bridge.describe()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            airink_get_camera_status,
            airink_emit_mock_frame,
            airink_start_mock_stream,
            airink_stop_mock_stream,
            airink_describe_sidecar,
        ])
        .run(tauri::generate_context!())
        .expect("error while running AirInk adapter application");
}

fn build_mock_frame(frame_id: u64, t: f32) -> AirInkFrame {
    let x = 0.5 + 0.24 * (t * 1.7).sin();
    let y = 0.5 + 0.18 * (t * 2.3).cos();
    let pinch = 0.31 + 0.12 * (t * 1.2).sin();
    let drawing_active = pinch <= 0.34;
    let gesture_state = if drawing_active { "INKING" } else { "HOVER" };

    AirInkFrame {
        timestamp_ms: now_ms(),
        frame_id,
        source_type: "Mock".to_string(),
        camera: AirInkCameraInfo {
            width: 1280,
            height: 720,
            fps: 30.0,
        },
        tracking: AirInkTracking {
            hand_detected: true,
            confidence: 0.95,
            landmarks: vec![
                Point2D { x: x - 0.04, y: y + 0.04 },
                Point2D { x, y },
                Point2D { x: x + pinch * 0.15, y: y + 0.02 },
            ],
            raw_tip: Some(Point2D { x, y }),
            stable_tip: Some(Point2D { x, y }),
            pinch_ratio: Some(pinch),
            extension_ratio: Some(0.92),
        },
        gesture: AirInkGesture {
            state: gesture_state.to_string(),
            drawing_active,
        },
        quality: AirInkQuality {
            tracking_ok: true,
            jump_rejected: false,
            frame_dropped: false,
        },
    }
}

fn running_camera_status() -> AirInkCameraStatus {
    AirInkCameraStatus {
        status: "running".to_string(),
        camera_index: 0,
        width: 1280,
        height: 720,
        fps: 30.0,
        error_message: None,
    }
}

fn idle_camera_status() -> AirInkCameraStatus {
    AirInkCameraStatus {
        status: "idle".to_string(),
        camera_index: 0,
        width: 1280,
        height: 720,
        fps: 0.0,
        error_message: None,
    }
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
