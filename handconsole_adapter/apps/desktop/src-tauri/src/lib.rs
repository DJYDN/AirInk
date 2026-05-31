#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod config;
mod frame;
mod session;
mod sidecar;

use config::{CalibrationProfile, CalibrationProfileList};
use frame::{
    AirInkCameraInfo, AirInkCameraStatus, AirInkFrame, AirInkGesture, AirInkQuality,
    AirInkTracking, Point2D, SessionStatusEvent,
};
use session::SessionMeta;
use sidecar::PythonSidecarBridge;
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Mutex, OnceLock};
use tauri::{AppHandle, Emitter};
use tokio::time::{sleep, Duration};

static MOCK_RUNNING: AtomicBool = AtomicBool::new(false);
static MOCK_FRAME_ID: AtomicU64 = AtomicU64::new(0);
static ACTIVE_MOCK_SESSION: OnceLock<Mutex<Option<String>>> = OnceLock::new();

fn active_mock_session() -> &'static Mutex<Option<String>> {
    ACTIVE_MOCK_SESSION.get_or_init(|| Mutex::new(None))
}

#[tauri::command]
fn airink_get_camera_status() -> AirInkCameraStatus {
    let active = MOCK_RUNNING.load(Ordering::SeqCst) || sidecar::is_running();
    AirInkCameraStatus {
        status: if active { "running".to_string() } else { "idle".to_string() },
        camera_index: 0,
        width: 1280,
        height: 720,
        fps: if active { 30.0 } else { 0.0 },
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

    let session_id = format!("mock_session_{}", now_secs());
    if let Ok(mut active) = active_mock_session().lock() {
        *active = Some(session_id.clone());
    }

    app_handle
        .emit("airink/camera_status", running_camera_status())
        .map_err(|e| e.to_string())?;
    app_handle
        .emit(
            "airink/session_status",
            SessionStatusEvent {
                status: "recording".to_string(),
                session_id: Some(session_id),
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

        let session_id = active_mock_session()
            .lock()
            .ok()
            .and_then(|mut active| active.take());
        if let Some(id) = session_id {
            session::upsert_mock_session(&id, MOCK_FRAME_ID.load(Ordering::SeqCst), 0);
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
    let session_id = active_mock_session()
        .lock()
        .ok()
        .and_then(|mut active| active.take());
    if let Some(id) = session_id {
        session::upsert_mock_session(&id, MOCK_FRAME_ID.load(Ordering::SeqCst), 0);
    }
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
async fn airink_start_sidecar(
    app_handle: AppHandle,
    executable: Option<String>,
    args: Option<Vec<String>>,
) -> Result<String, String> {
    let executable = executable.unwrap_or_else(|| "python".to_string());
    let args = args.unwrap_or_else(|| vec!["-m".to_string(), "airink_sidecar".to_string()]);
    start_sidecar_with_status(app_handle, executable, args, "sidecar_session".to_string()).await
}

#[tauri::command]
async fn airink_start_mock_sidecar(app_handle: AppHandle) -> Result<String, String> {
    let script = resolve_mock_sidecar_path()?;
    start_sidecar_with_status(
        app_handle,
        "python".to_string(),
        vec![script.to_string_lossy().to_string()],
        "mock_sidecar_session".to_string(),
    )
    .await
}

async fn start_sidecar_with_status(
    app_handle: AppHandle,
    executable: String,
    args: Vec<String>,
    session_id: String,
) -> Result<String, String> {
    let message = sidecar::start_sidecar(app_handle.clone(), executable, args).await?;
    app_handle
        .emit("airink/camera_status", running_camera_status())
        .map_err(|e| e.to_string())?;
    app_handle
        .emit(
            "airink/session_status",
            SessionStatusEvent {
                status: "recording".to_string(),
                session_id: Some(session_id),
                stroke_count: 0,
            },
        )
        .map_err(|e| e.to_string())?;
    Ok(message)
}

#[tauri::command]
async fn airink_stop_sidecar(app_handle: AppHandle) -> Result<(), String> {
    sidecar::stop_sidecar().await?;
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

#[tauri::command]
fn airink_list_sessions() -> Vec<SessionMeta> {
    session::list_sessions()
}

#[tauri::command]
fn airink_delete_session(session_id: String) -> bool {
    session::delete_session(&session_id)
}

#[tauri::command]
fn airink_start_playback(app_handle: AppHandle, session_id: String, speed: Option<f64>) -> Result<(), String> {
    let speed = speed.unwrap_or(1.0).clamp(0.1, 10.0);
    app_handle
        .emit(
            "airink/session_status",
            SessionStatusEvent {
                status: "playback".to_string(),
                session_id: Some(session_id.clone()),
                stroke_count: 0,
            },
        )
        .map_err(|e| e.to_string())?;

    tokio::spawn(async move {
        for i in 0..180u64 {
            let t = i as f32 / 30.0;
            let frame = build_mock_frame(i + 1, t);
            app_handle.emit("airink/playback_frame", &frame).ok();
            app_handle.emit("airink/tracking_frame", frame).ok();
            let delay = (33.0 / speed).max(5.0) as u64;
            sleep(Duration::from_millis(delay)).await;
        }
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
fn airink_stop_playback(app_handle: AppHandle) -> Result<(), String> {
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
fn airink_get_calibration_profiles() -> CalibrationProfileList {
    config::get_profiles()
}

#[tauri::command]
fn airink_save_calibration_profile(profile_json: String) -> Result<CalibrationProfileList, String> {
    let profile: CalibrationProfile = serde_json::from_str(&profile_json).map_err(|e| e.to_string())?;
    Ok(config::save_profile(profile))
}

#[tauri::command]
fn airink_set_active_calibration(profile_name: String) -> Result<CalibrationProfileList, String> {
    config::set_active_profile(&profile_name)
}

#[tauri::command]
fn airink_delete_calibration_profile(profile_name: String) -> CalibrationProfileList {
    config::delete_profile(&profile_name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            airink_get_camera_status,
            airink_emit_mock_frame,
            airink_start_mock_stream,
            airink_stop_mock_stream,
            airink_start_sidecar,
            airink_start_mock_sidecar,
            airink_stop_sidecar,
            airink_describe_sidecar,
            airink_list_sessions,
            airink_delete_session,
            airink_start_playback,
            airink_stop_playback,
            airink_get_calibration_profiles,
            airink_save_calibration_profile,
            airink_set_active_calibration,
            airink_delete_calibration_profile,
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

fn resolve_mock_sidecar_path() -> Result<PathBuf, String> {
    let cwd = std::env::current_dir().map_err(|e| e.to_string())?;
    let candidates = vec![
        cwd.join("python_sidecar_contract/mock_sidecar.py"),
        cwd.join("../python_sidecar_contract/mock_sidecar.py"),
        cwd.join("../../python_sidecar_contract/mock_sidecar.py"),
        cwd.join("../../../python_sidecar_contract/mock_sidecar.py"),
        cwd.join("handconsole_adapter/python_sidecar_contract/mock_sidecar.py"),
    ];

    for candidate in &candidates {
        if candidate.exists() {
            return Ok(candidate.clone());
        }
    }

    let searched = candidates
        .iter()
        .map(|path| path.display().to_string())
        .collect::<Vec<_>>()
        .join("\n");
    Err(format!(
        "mock sidecar not found; current_dir={} searched:\n{}",
        cwd.display(), searched
    ))
}

fn now_ms() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis() as u64
}

fn now_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
