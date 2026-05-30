import type { Stroke } from "../../types/stroke";

interface WritingCanvasProps {
  committedStrokes: Stroke[];
  activeStroke: Stroke | null;
}

export default function WritingCanvas({ committedStrokes, activeStroke }: WritingCanvasProps) {
  const strokes = activeStroke ? [...committedStrokes, activeStroke] : committedStrokes;

  return (
    <svg className="writing-canvas" viewBox="0 0 1 1" preserveAspectRatio="none">
      <rect x="0" y="0" width="1" height="1" rx="0.02" fill="rgba(255,255,255,0.035)" />
      {strokes.map((stroke) => (
        <polyline
          key={stroke.id}
          points={stroke.points.map((point) => `${point.x},${point.y}`).join(" ")}
          fill="none"
          stroke="currentColor"
          strokeWidth="0.006"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
    </svg>
  );
}
