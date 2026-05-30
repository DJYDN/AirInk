import type { AirInkFrame, Point2D } from "../../types/frame";

interface SkeletonOverlayProps {
  frame: AirInkFrame | null;
}

function toPoint(point: Point2D | null | undefined): string | null {
  if (!point) return null;
  return `${point.x},${point.y}`;
}

export default function SkeletonOverlay({ frame }: SkeletonOverlayProps) {
  const tip = frame?.tracking.stable_tip ?? null;
  const thumb = frame?.tracking.landmarks[2] ?? null;
  const wrist = frame?.tracking.landmarks[0] ?? null;
  const tipPoint = toPoint(tip);
  const thumbPoint = toPoint(thumb);
  const wristPoint = toPoint(wrist);

  return (
    <svg className="skeleton-overlay" viewBox="0 0 1 1" preserveAspectRatio="none">
      <rect x="0" y="0" width="1" height="1" rx="0.02" fill="rgba(255,255,255,0.035)" />
      <line x1="0" y1="0.5" x2="1" y2="0.5" stroke="rgba(255,255,255,0.08)" strokeWidth="0.002" />
      <line x1="0.5" y1="0" x2="0.5" y2="1" stroke="rgba(255,255,255,0.08)" strokeWidth="0.002" />
      {wrist && tip && (
        <line
          x1={wrist.x}
          y1={wrist.y}
          x2={tip.x}
          y2={tip.y}
          stroke="rgba(124,196,255,0.7)"
          strokeWidth="0.005"
        />
      )}
      {thumb && tip && (
        <line
          x1={thumb.x}
          y1={thumb.y}
          x2={tip.x}
          y2={tip.y}
          stroke="rgba(255,176,32,0.8)"
          strokeWidth="0.004"
          strokeDasharray="0.01 0.008"
        />
      )}
      {wristPoint && <circle cx={wrist!.x} cy={wrist!.y} r="0.018" className="joint wrist" />}
      {tipPoint && <circle cx={tip!.x} cy={tip!.y} r="0.02" className="joint tip" />}
      {thumbPoint && <circle cx={thumb!.x} cy={thumb!.y} r="0.017" className="joint thumb" />}
      {!frame && <text x="0.5" y="0.5" textAnchor="middle" className="overlay-label">Waiting for tracking frame</text>}
      {frame && (
        <text x="0.035" y="0.07" className="overlay-label">
          {frame.gesture.state} · pinch {frame.tracking.pinch_ratio?.toFixed(2) ?? "--"}
        </text>
      )}
    </svg>
  );
}
