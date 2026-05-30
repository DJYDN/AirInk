import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { CalibrationProfile, CalibrationProfileList } from "../types/calibration";

function makeDefaultProfile(): CalibrationProfile {
  return {
    profile_name: `profile_${Date.now()}`,
    active_region: {
      x_min: 0.05,
      y_min: 0.05,
      x_max: 0.95,
      y_max: 0.95,
    },
    gesture: {
      pinch_down: 0.3,
      pinch_up: 0.42,
      min_confidence: 0.6,
    },
  };
}

export default function Calibration() {
  const [profiles, setProfiles] = useState<CalibrationProfile[]>([]);
  const [activeProfile, setActiveProfile] = useState<string | null>(null);
  const [draft, setDraft] = useState<CalibrationProfile>(() => makeDefaultProfile());
  const [message, setMessage] = useState("");

  const applyList = (list: CalibrationProfileList) => {
    setProfiles(list.profiles);
    setActiveProfile(list.active_profile);
  };

  const loadProfiles = async () => {
    const list = await invoke<CalibrationProfileList>("airink_get_calibration_profiles");
    applyList(list);
  };

  useEffect(() => {
    void loadProfiles().catch((error) => setMessage(String(error)));
  }, []);

  const saveDraft = async () => {
    const list = await invoke<CalibrationProfileList>("airink_save_calibration_profile", {
      profileJson: JSON.stringify(draft),
    });
    applyList(list);
    setMessage(`Saved ${draft.profile_name}`);
    setDraft(makeDefaultProfile());
  };

  const activate = async (profileName: string) => {
    const list = await invoke<CalibrationProfileList>("airink_set_active_calibration", { profileName });
    applyList(list);
    setMessage(`Activated ${profileName}`);
  };

  const remove = async (profileName: string) => {
    const list = await invoke<CalibrationProfileList>("airink_delete_calibration_profile", { profileName });
    applyList(list);
    setMessage(`Deleted ${profileName}`);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Calibration</h1>
          <p>Profile scaffold for active writing region and pinch thresholds.</p>
        </div>
        <button className="btn" onClick={() => void loadProfiles()}>Refresh</button>
      </div>

      <div className="two-column-grid">
        <section className="panel">
          <h2>Profiles</h2>
          {message && <p className="muted">{message}</p>}
          {profiles.length === 0 ? (
            <p className="muted">No calibration profiles.</p>
          ) : (
            <div className="session-list">
              {profiles.map((profile) => (
                <div key={profile.profile_name} className="session-row">
                  <div>
                    <strong>{profile.profile_name}</strong>
                    <small>
                      region [{profile.active_region.x_min}, {profile.active_region.y_min}] - [{profile.active_region.x_max}, {profile.active_region.y_max}]
                      {activeProfile === profile.profile_name ? " · active" : ""}
                    </small>
                  </div>
                  <div className="mock-controls">
                    <button className="btn" onClick={() => void activate(profile.profile_name)}>Load</button>
                    <button className="btn danger" onClick={() => void remove(profile.profile_name)}>Delete</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Create mock profile</h2>
          <label className="form-row">
            Name
            <input
              value={draft.profile_name}
              onChange={(event) => setDraft({ ...draft, profile_name: event.target.value })}
            />
          </label>
          <div className="form-grid">
            <label>Pinch down<input type="number" step="0.01" value={draft.gesture.pinch_down} onChange={(e) => setDraft({ ...draft, gesture: { ...draft.gesture, pinch_down: Number(e.target.value) } })} /></label>
            <label>Pinch up<input type="number" step="0.01" value={draft.gesture.pinch_up} onChange={(e) => setDraft({ ...draft, gesture: { ...draft.gesture, pinch_up: Number(e.target.value) } })} /></label>
            <label>Min confidence<input type="number" step="0.01" value={draft.gesture.min_confidence} onChange={(e) => setDraft({ ...draft, gesture: { ...draft.gesture, min_confidence: Number(e.target.value) } })} /></label>
          </div>
          <button className="btn primary" onClick={() => void saveDraft()}>Save Profile</button>
        </section>
      </div>
    </div>
  );
}
