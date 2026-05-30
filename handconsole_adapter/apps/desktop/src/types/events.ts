import type { AirInkFrame } from "./frame";
import type { RecognitionResult } from "./recognition";
import type { Stroke } from "./stroke";

export interface StrokeUpdateEvent {
  session_id: string | null;
  active_stroke: Stroke | null;
  committed_strokes: Stroke[];
  stroke_count: number;
}

export interface SessionStatusEvent {
  status: "idle" | "recording" | "pending_recognition" | "showing_candidates" | "playback";
  session_id: string | null;
  stroke_count: number;
}

export type RecognitionResultEvent = RecognitionResult;

export type PlaybackFrameEvent = AirInkFrame;
