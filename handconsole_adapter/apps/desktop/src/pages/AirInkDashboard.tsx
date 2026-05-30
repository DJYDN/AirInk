import { useAirInkStore } from "../stores/airinkStore";

export default function AirInkDashboard() {
  const cameraStatus = useAirInkStore((state) => state.cameraStatus);
  const latestFrame = useAirInkStore((state) => state.latestFrame);
  const strokeCount = useAirInkStore((state) => state.committedStrokes.length);

  return (
    <div className="page">
      <h1>AirInk Dashboard</h1>
      <div className="card-grid">
        <section className="card">
          <span className="card-label">Camera</span>
          <strong>{cameraStatus.status}</strong>
          <small>{cameraStatus.width} x {cameraStatus.height} @ {cameraStatus.fps} FPS</small>
        </section>
        <section className="card">
          <span className="card-label">Tracking</span>
          <strong>{latestFrame?.tracking.hand_detected ? "Hand detected" : "No hand"}</strong>
          <small>Confidence: {latestFrame?.tracking.confidence.toFixed(2) ?? "--"}</small>
        </section>
        <section className="card">
          <span className="card-label">Gesture</span>
          <strong>{latestFrame?.gesture.state ?? "--"}</strong>
          <small>Pinch: {latestFrame?.tracking.pinch_ratio?.toFixed(2) ?? "--"}</small>
        </section>
        <section className="card">
          <span className="card-label">Session</span>
          <strong>{strokeCount} strokes</strong>
          <small>Adapter scaffold</small>
        </section>
      </div>
    </div>
  );
}
