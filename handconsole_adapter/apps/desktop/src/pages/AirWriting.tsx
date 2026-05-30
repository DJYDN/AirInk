import { useAirInkStore } from "../stores/airinkStore";

export default function AirWriting() {
  const latestFrame = useAirInkStore((state) => state.latestFrame);

  return (
    <div className="page writing-page">
      <h1>Air Writing</h1>
      <div className="workspace-grid">
        <section className="panel preview-panel">
          <h2>Camera / Skeleton Preview</h2>
          <div className="placeholder-box">Preview pipeline scaffold</div>
        </section>
        <section className="panel canvas-panel">
          <h2>Writing Canvas</h2>
          <div className="canvas-placeholder">Stroke canvas scaffold</div>
        </section>
        <section className="panel debug-panel">
          <h2>Tracking Debug</h2>
          <dl>
            <dt>Gesture</dt>
            <dd>{latestFrame?.gesture.state ?? "--"}</dd>
            <dt>Pinch ratio</dt>
            <dd>{latestFrame?.tracking.pinch_ratio?.toFixed(3) ?? "--"}</dd>
            <dt>Extension ratio</dt>
            <dd>{latestFrame?.tracking.extension_ratio?.toFixed(3) ?? "--"}</dd>
            <dt>Confidence</dt>
            <dd>{latestFrame?.tracking.confidence.toFixed(3) ?? "--"}</dd>
          </dl>
        </section>
      </div>
    </div>
  );
}
