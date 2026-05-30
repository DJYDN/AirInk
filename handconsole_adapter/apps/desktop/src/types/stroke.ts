export interface StrokePoint {
  x: number;
  y: number;
  t: number;
  confidence: number;
}

export interface Stroke {
  id: string;
  points: StrokePoint[];
}

export interface AirInkSession {
  session_id: string;
  name: string;
  start_time: number;
  end_time: number | null;
  strokes: Stroke[];
  recognized_text: string;
}
