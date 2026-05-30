import { invoke } from "@tauri-apps/api/core";
import { useAirInkStore } from "../../stores/airinkStore";

export default function MockStreamControls() {
  const status = useAirInkStore((state) => state.cameraStatus.status);
  const clear = useAirInkStore((state) => state.clear);

  const start = async () => {
    await invoke("airink_start_mock_stream");
  };

  const stop = async () => {
    await invoke("airink_stop_mock_stream");
  };

  const emitOne = async () => {
    await invoke("airink_emit_mock_frame");
  };

  return (
    <div className="mock-controls">
      <button className="btn primary" onClick={start} disabled={status === "running"}>
        Start Mock Stream
      </button>
      <button className="btn" onClick={stop} disabled={status !== "running"}>
        Stop
      </button>
      <button className="btn" onClick={emitOne}>
        Emit One Frame
      </button>
      <button className="btn danger" onClick={clear}>
        Clear
      </button>
    </div>
  );
}
