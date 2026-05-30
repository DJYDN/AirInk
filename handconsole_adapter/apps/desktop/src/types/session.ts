export interface SessionMeta {
  session_id: string;
  name: string;
  start_time: number;
  end_time: number | null;
  frame_count: number;
  stroke_count: number;
  source_type: string;
}
