import { create } from "zustand";
import type { SessionStatusEvent, StrokeUpdateEvent } from "../types/events";
import type { AirInkFrame } from "../types/frame";
import type { RecognitionResult } from "../types/recognition";
import type { Stroke, StrokePoint } from "../types/stroke";

export interface CameraStatus {
  status: "idle" | "starting" | "running" | "error";
  camera_index: number;
  width: number;
  height: number;
  fps: number;
  error_message?: string;
}

interface AirInkState {
  cameraStatus: CameraStatus;
  sessionStatus: SessionStatusEvent;
  latestFrame: AirInkFrame | null;
  frameCount: number;
  committedStrokes: Stroke[];
  activeStroke: Stroke | null;
  recognition: RecognitionResult | null;
  setCameraStatus: (status: CameraStatus) => void;
  setSessionStatus: (status: SessionStatusEvent) => void;
  addFrame: (frame: AirInkFrame) => void;
  applyStrokeUpdate: (event: StrokeUpdateEvent) => void;
  setStrokes: (committed: Stroke[], active: Stroke | null) => void;
  setRecognition: (result: RecognitionResult | null) => void;
  clear: () => void;
}

const MAX_ACTIVE_POINTS = 2000;

export const useAirInkStore = create<AirInkState>((set, get) => ({
  cameraStatus: {
    status: "idle",
    camera_index: 0,
    width: 0,
    height: 0,
    fps: 0,
  },
  sessionStatus: {
    status: "idle",
    session_id: null,
    stroke_count: 0,
  },
  latestFrame: null,
  frameCount: 0,
  committedStrokes: [],
  activeStroke: null,
  recognition: null,
  setCameraStatus: (cameraStatus) => set({ cameraStatus }),
  setSessionStatus: (sessionStatus) => set({ sessionStatus }),
  addFrame: (latestFrame) => {
    const state = get();
    const tip = latestFrame.tracking.stable_tip;
    let activeStroke = state.activeStroke;
    let committedStrokes = state.committedStrokes;

    if (latestFrame.gesture.drawing_active && tip) {
      const point: StrokePoint = {
        x: tip.x,
        y: tip.y,
        t: latestFrame.timestamp_ms,
        confidence: latestFrame.tracking.confidence,
      };
      if (!activeStroke) {
        activeStroke = { id: `stroke_${latestFrame.frame_id}`, points: [point] };
      } else {
        activeStroke = {
          ...activeStroke,
          points: [...activeStroke.points, point].slice(-MAX_ACTIVE_POINTS),
        };
      }
    } else if (activeStroke && activeStroke.points.length > 0) {
      committedStrokes = [...committedStrokes, activeStroke];
      activeStroke = null;
    }

    set({
      latestFrame,
      frameCount: state.frameCount + 1,
      activeStroke,
      committedStrokes,
      sessionStatus: {
        ...state.sessionStatus,
        stroke_count: committedStrokes.length + (activeStroke ? 1 : 0),
      },
    });
  },
  applyStrokeUpdate: (event) => set({
    activeStroke: event.active_stroke,
    committedStrokes: event.committed_strokes,
    sessionStatus: {
      status: event.session_id ? "recording" : "idle",
      session_id: event.session_id,
      stroke_count: event.stroke_count,
    },
  }),
  setStrokes: (committedStrokes, activeStroke) => set({ committedStrokes, activeStroke }),
  setRecognition: (recognition) => set({ recognition }),
  clear: () => set({
    latestFrame: null,
    frameCount: 0,
    committedStrokes: [],
    activeStroke: null,
    recognition: null,
    sessionStatus: {
      status: "idle",
      session_id: null,
      stroke_count: 0,
    },
  }),
}));
