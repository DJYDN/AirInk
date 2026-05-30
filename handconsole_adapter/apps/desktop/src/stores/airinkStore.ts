import { create } from "zustand";
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
  latestFrame: AirInkFrame | null;
  frameCount: number;
  committedStrokes: Stroke[];
  activeStroke: Stroke | null;
  recognition: RecognitionResult | null;
  setCameraStatus: (status: CameraStatus) => void;
  addFrame: (frame: AirInkFrame) => void;
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
  latestFrame: null,
  frameCount: 0,
  committedStrokes: [],
  activeStroke: null,
  recognition: null,
  setCameraStatus: (cameraStatus) => set({ cameraStatus }),
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
    });
  },
  setStrokes: (committedStrokes, activeStroke) => set({ committedStrokes, activeStroke }),
  setRecognition: (recognition) => set({ recognition }),
  clear: () => set({
    latestFrame: null,
    frameCount: 0,
    committedStrokes: [],
    activeStroke: null,
    recognition: null,
  }),
}));
