//! In-memory mock session registry for the adapter scaffold.
//!
//! This is not the final persistence layer. It gives the frontend a realistic
//! list/playback command surface while the real AirInk session model is still
//! being designed.

use serde::{Deserialize, Serialize};
use std::sync::{Mutex, OnceLock};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionMeta {
    pub session_id: String,
    pub name: String,
    pub start_time: u64,
    pub end_time: Option<u64>,
    pub frame_count: u64,
    pub stroke_count: usize,
    pub source_type: String,
}

#[derive(Debug, Default)]
struct MockSessionRegistry {
    sessions: Vec<SessionMeta>,
}

static REGISTRY: OnceLock<Mutex<MockSessionRegistry>> = OnceLock::new();

fn registry() -> &'static Mutex<MockSessionRegistry> {
    REGISTRY.get_or_init(|| {
        Mutex::new(MockSessionRegistry {
            sessions: vec![SessionMeta {
                session_id: "mock_demo_session".to_string(),
                name: "Mock demo session".to_string(),
                start_time: now_secs(),
                end_time: Some(now_secs()),
                frame_count: 300,
                stroke_count: 3,
                source_type: "Mock".to_string(),
            }],
        })
    })
}

pub fn list_sessions() -> Vec<SessionMeta> {
    registry()
        .lock()
        .map(|guard| guard.sessions.clone())
        .unwrap_or_default()
}

pub fn upsert_mock_session(session_id: &str, frame_count: u64, stroke_count: usize) -> SessionMeta {
    let meta = SessionMeta {
        session_id: session_id.to_string(),
        name: session_id.to_string(),
        start_time: now_secs(),
        end_time: Some(now_secs()),
        frame_count,
        stroke_count,
        source_type: "Mock".to_string(),
    };

    if let Ok(mut guard) = registry().lock() {
        guard.sessions.retain(|s| s.session_id != session_id);
        guard.sessions.insert(0, meta.clone());
    }

    meta
}

pub fn delete_session(session_id: &str) -> bool {
    if let Ok(mut guard) = registry().lock() {
        let before = guard.sessions.len();
        guard.sessions.retain(|s| s.session_id != session_id);
        return guard.sessions.len() != before;
    }
    false
}

fn now_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}
