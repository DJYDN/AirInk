import WritingCanvas from "../components/canvas/WritingCanvas";
import MockStreamControls from "../components/tracking/MockStreamControls";
import SkeletonOverlay from "../components/tracking/SkeletonOverlay";
import { useAirInkStore } from "../stores/airinkStore";

export default function AirWriting() {
  const latestFrame = useAirInkStore((state) => state.latestFrame);
  const committedStrokes = useAirInkStore((state) => state.committedStrokes);
  const activeStroke = useAirInkStore((state) => state.activeStroke);
  const frameCount = useAirInkStore((state) => state.frameCount);
  const sessionStatus = useAirInkStore((state) => state.sessionStatus);

  return (
    <div className="page writing-page">
      <div className="page-header">
        <div>
          <h1>Air Writing</h1>
          <p>Mock event pipeline scaffold for the future HandConsole-style AirInk module.</p>
        </div>
        <MockStreamControls />
      </div>

      <div className="workspace-grid">
        <section className="panel preview-panel">
          <h2>Camera / Skeleton Preview</h2>
          <SkeletonOverlay frame={latestFrame} />
        </section>
        <section className="panel canvas-panel">
          <h2>Writing Canvas</h2>
          <WritingCanvas committedStrokes={committedStrokes} activeStroke={activeStroke} />
        </section>
        <section className="panel debug-panel">
          <h2>Tracking Debug</h2>
          <dl>
            <dt>Frames</dt>
            <dd>{frameCount}</dd>
            <dt>Session</dt>
            <dd>{sessionStatus.status}</dd>
            <dt>Gesture</dt>
            <dd>{latestFrame?.gesture.state ?? "--"}</dd>
            <dt>Drawing active</dt>
            <dd>{latestFrame?.gesture.drawing_active ? "yes" : "no"}</dd>
            <dt>Pinch ratio</dt>
            <dd>{latestFrame?.tracking.pinch_ratio?.toFixed(3) ?? "--"}</dd>
            <dt>Extension ratio</dt>
            <dd>{latestFrame?.tracking.extension_ratio?.toFixed(3) ?? "--"}</dd>
            <dt>Confidence</dt>
            <dd>{latestFrame?.tracking.confidence.toFixed(3) ?? "--"}</dd>
            <dt>Committed strokes</dt>
            <dd>{committedStrokes.length}</dd>
            <dt>Active points</dt>
            <dd>{activeStroke?.points.length ?? 0}</dd>
          </dl>
        </section>
      </div>
    </div>
  );
}
