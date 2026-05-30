export interface RecognitionCandidate {
  id: string;
  text: string;
  confidence: number | null;
}

export interface RecognitionResult {
  session_id: string | null;
  provider: string;
  elapsed_ms: number;
  candidates: RecognitionCandidate[];
}
