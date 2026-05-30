import { create } from "zustand";
import type { AirInkFrame } from "../types/frame";
import type { RecognitionResult } from "../types/recognition";
import type { Stroke } from "../types/stroke";

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
  committedStrokes: Stroke[];
  activeStroke: Stroke | null;
  recognition: RecognitionResult | null;
  setCameraStatus: (status: CameraStatus) => void;
  addFrame: (frame: AirInkFrame) => void;
  setStrokes: (committed: Stroke[], active: Stroke | null) => void;
  setRecognition: (result: RecognitionResult | null) => void;
  clear: () => void;
}

export const useAirInkStore = create<AirInkState>((set) => ({
  cameraStatus: {
    status: "idle",
    camera_index: 0,
    width: 0,
    height: 0,
    fps: 0,
  },
  latestFrame: null,
  committedStrokes: [],
  activeStroke: null,
  recognition: null,
  setCameraStatus: (cameraStatus) => set({ cameraStatus }),
  addFrame: (latestFrame) => set({ latestFrame }),
  setStrokes: (committedStrokes, activeStroke) => set({ committedStrokes, activeStroke }),
  setRecognition: (recognition) => set({ recognition }),
  clear: () => set({ latestFrame: null, committedStrokes: [], activeStroke: null, recognition: null }),
}));
