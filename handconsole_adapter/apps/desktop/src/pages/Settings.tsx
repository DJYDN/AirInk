import { useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { useAirInkStore } from "../stores/airinkStore";

export default function Settings() {
  const [executable, setExecutable] = useState("python");
  const [args, setArgs] = useState("../../python_sidecar_contract/mock_sidecar.py");
  const [message, setMessage] = useState("");
  const cameraStatus = useAirInkStore((state) => state.cameraStatus.status);
  const sidecarErrors = useAirInkStore((state) => state.sidecarErrors);
  const clearSidecarErrors = useAirInkStore((state) => state.clearSidecarErrors);

  const parsedArgs = useMemo(
    () => args.split(" ").map((item) => item.trim()).filter(Boolean),
    [args],
  );

  const describe = async () => {
    const text = await invoke<string>("airink_describe_sidecar", {
      executable,
      args: parsedArgs,
    });
    setMessage(text);
  };

  const startSidecar = async () => {
    const text = await invoke<string>("airink_start_sidecar", {
      executable,
      args: parsedArgs,
    });
    setMessage(text);
  };

  const stopSidecar = async () => {
    await invoke("airink_stop_sidecar");
    setMessage("sidecar stopped");
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Settings</h1>
          <p>Adapter settings and Python JSONL sidecar controls.</p>
        </div>
        <span className="status-pill">Camera: {cameraStatus}</span>
      </div>

      <div className="two-column-grid">
        <section className="panel">
          <h2>Python sidecar</h2>
          <label className="form-row">
            Executable
            <input value={executable} onChange={(event) => setExecutable(event.target.value)} />
          </label>
          <label className="form-row">
            Arguments
            <input value={args} onChange={(event) => setArgs(event.target.value)} />
          </label>
          <p className="muted">Arguments are split by spaces. The default points to the adapter mock sidecar.</p>
          <div className="mock-controls left">
            <button className="btn" onClick={() => void describe()}>Describe</button>
            <button className="btn primary" onClick={() => void startSidecar()}>Start Sidecar</button>
            <button className="btn" onClick={() => void stopSidecar()}>Stop Sidecar</button>
          </div>
          {message && <p className="muted">{message}</p>}
        </section>

        <section className="panel">
          <div className="panel-header-row">
            <h2>Sidecar errors</h2>
            <button className="btn" onClick={clearSidecarErrors}>Clear</button>
          </div>
          {sidecarErrors.length === 0 ? (
            <p className="muted">No sidecar errors.</p>
          ) : (
            <div className="error-list">
              {sidecarErrors.map((error, index) => (
                <div key={`${error.kind}-${index}`} className="error-row">
                  <strong>{error.kind}</strong>
                  <small>{error.message}</small>
                  {error.line && <code>{error.line}</code>}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="panel settings-notes">
        <h2>Planned settings</h2>
        <ul>
          <li>Camera index, resolution, FPS</li>
          <li>Tracking confidence and smoothing</li>
          <li>Pinch down/up thresholds</li>
          <li>Stroke filter parameters</li>
          <li>Canvas and recognition options</li>
        </ul>
      </section>
    </div>
  );
}
