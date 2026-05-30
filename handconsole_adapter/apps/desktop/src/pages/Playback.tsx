import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { SessionMeta } from "../types/session";

export default function Playback() {
  const [sessions, setSessions] = useState<SessionMeta[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [speed, setSpeed] = useState(1);
  const [message, setMessage] = useState("");

  const loadSessions = async () => {
    const list = await invoke<SessionMeta[]>("airink_list_sessions");
    setSessions(list);
    if (!selectedId && list.length > 0) setSelectedId(list[0].session_id);
  };

  useEffect(() => {
    void loadSessions().catch((error) => setMessage(String(error)));
  }, []);

  const startPlayback = async () => {
    if (!selectedId) return;
    await invoke("airink_start_playback", { sessionId: selectedId, speed });
    setMessage(`Playing ${selectedId} at ${speed}x`);
  };

  const stopPlayback = async () => {
    await invoke("airink_stop_playback");
    setMessage("Playback stopped");
  };

  const deleteSession = async (sessionId: string) => {
    await invoke("airink_delete_session", { sessionId });
    await loadSessions();
    setMessage(`Deleted ${sessionId}`);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Playback</h1>
          <p>Mock session list and replay command surface.</p>
        </div>
        <div className="mock-controls">
          <button className="btn" onClick={() => void loadSessions()}>Refresh</button>
          <select className="select" value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={4}>4x</option>
          </select>
          <button className="btn primary" onClick={() => void startPlayback()} disabled={!selectedId}>Play</button>
          <button className="btn" onClick={() => void stopPlayback()}>Stop</button>
        </div>
      </div>

      <section className="panel">
        <h2>Sessions</h2>
        {message && <p className="muted">{message}</p>}
        {sessions.length === 0 ? (
          <p className="muted">No sessions yet. Start and stop the mock stream to create one.</p>
        ) : (
          <div className="session-list">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className={`session-row ${selectedId === session.session_id ? "selected" : ""}`}
                onClick={() => setSelectedId(session.session_id)}
              >
                <div>
                  <strong>{session.name}</strong>
                  <small>
                    {session.frame_count} frames · {session.stroke_count} strokes · {session.source_type}
                  </small>
                </div>
                <button
                  className="btn danger"
                  onClick={(event) => {
                    event.stopPropagation();
                    void deleteSession(session.session_id);
                  }}
                >
                  Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
