export interface ActiveRegion {
  x_min: number;
  y_min: number;
  x_max: number;
  y_max: number;
}

export interface GestureThresholds {
  pinch_down: number;
  pinch_up: number;
  min_confidence: number;
}

export interface CalibrationProfile {
  profile_name: string;
  active_region: ActiveRegion;
  gesture: GestureThresholds;
}

export interface CalibrationProfileList {
  profiles: CalibrationProfile[];
  active_profile: string | null;
}
