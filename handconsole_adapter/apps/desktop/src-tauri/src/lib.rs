#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod frame;

use frame::{AirInkCameraInfo, AirInkCameraStatus, AirInkFrame, AirInkGesture, AirInkQuality, AirInkTracking};
use tauri::{AppHandle, Emitter};

#[tauri::command]
fn airink_get_camera_status() -> AirInkCameraStatus {
    AirInkCameraStatus {
        status: "idle".to_string(),
        camera_index: 0,
        width: 0,
        height: 0,
        fps: 0.0,
        error_message: None,
    }
}

#[tauri::command]
fn airink_emit_mock_frame(app_handle: AppHandle) -> Result<(), String> {
    let frame = AirInkFrame {
        timestamp_ms: now_ms(),
        frame_id: 1,
        source_type: "Mock".to_string(),
        camera: AirInkCameraInfo {
            width: 1280,
            height: 720,
            fps: 30.0,
        },
        tracking: AirInkTracking {
            hand_detected: true,
            confidence: 0.95,
            landmarks: vec![],
            raw_tip: None,
            stable_tip: None,
            pinch_ratio: Some(0.28),
            extension_ratio: Some(0.92),
        },
        gesture: AirInkGesture {
            state: "INKING".to_string(),
            drawing_active: true,
        },
        quality: AirInkQuality {
            tracking_ok: true,
            jump_rejected: false,
            frame_dropped: false,
        },
    };
    app_handle.emit("airink/tracking_frame", frame).map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            airink_get_camera_status,
            airink_emit_mock_frame,
        ])
        .run(tauri::generate_context!())
        .expect("error while running AirInk adapter application");
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}
