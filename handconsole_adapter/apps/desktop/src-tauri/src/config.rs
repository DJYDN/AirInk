//! Adapter configuration scaffold.
//!
//! This module defines calibration profile types and in-memory profile commands.
//! Persistent storage should be added after the data model is verified in the UI.

use serde::{Deserialize, Serialize};
use std::sync::{Mutex, OnceLock};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ActiveRegion {
    pub x_min: f32,
    pub y_min: f32,
    pub x_max: f32,
    pub y_max: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GestureThresholds {
    pub pinch_down: f32,
    pub pinch_up: f32,
    pub min_confidence: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalibrationProfile {
    pub profile_name: String,
    pub active_region: ActiveRegion,
    pub gesture: GestureThresholds,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalibrationProfileList {
    pub profiles: Vec<CalibrationProfile>,
    pub active_profile: Option<String>,
}

#[derive(Debug)]
struct ProfileRegistry {
    profiles: Vec<CalibrationProfile>,
    active_profile: Option<String>,
}

static PROFILES: OnceLock<Mutex<ProfileRegistry>> = OnceLock::new();

fn registry() -> &'static Mutex<ProfileRegistry> {
    PROFILES.get_or_init(|| {
        Mutex::new(ProfileRegistry {
            profiles: vec![default_profile()],
            active_profile: Some("default_mock".to_string()),
        })
    })
}

pub fn get_profiles() -> CalibrationProfileList {
    registry()
        .lock()
        .map(|guard| CalibrationProfileList {
            profiles: guard.profiles.clone(),
            active_profile: guard.active_profile.clone(),
        })
        .unwrap_or(CalibrationProfileList {
            profiles: vec![],
            active_profile: None,
        })
}

pub fn save_profile(profile: CalibrationProfile) -> CalibrationProfileList {
    if let Ok(mut guard) = registry().lock() {
        guard.profiles.retain(|p| p.profile_name != profile.profile_name);
        guard.active_profile = Some(profile.profile_name.clone());
        guard.profiles.insert(0, profile);
    }
    get_profiles()
}

pub fn set_active_profile(profile_name: &str) -> Result<CalibrationProfileList, String> {
    if let Ok(mut guard) = registry().lock() {
        if guard.profiles.iter().any(|p| p.profile_name == profile_name) {
            guard.active_profile = Some(profile_name.to_string());
            return Ok(CalibrationProfileList {
                profiles: guard.profiles.clone(),
                active_profile: guard.active_profile.clone(),
            });
        }
    }
    Err(format!("Calibration profile '{}' not found", profile_name))
}

pub fn delete_profile(profile_name: &str) -> CalibrationProfileList {
    if let Ok(mut guard) = registry().lock() {
        guard.profiles.retain(|p| p.profile_name != profile_name);
        if guard.active_profile.as_deref() == Some(profile_name) {
            guard.active_profile = guard.profiles.first().map(|p| p.profile_name.clone());
        }
    }
    get_profiles()
}

fn default_profile() -> CalibrationProfile {
    CalibrationProfile {
        profile_name: "default_mock".to_string(),
        active_region: ActiveRegion {
            x_min: 0.05,
            y_min: 0.05,
            x_max: 0.95,
            y_max: 0.95,
        },
        gesture: GestureThresholds {
            pinch_down: 0.30,
            pinch_up: 0.42,
            min_confidence: 0.60,
        },
    }
}
