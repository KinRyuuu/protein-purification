/**
 * Client-side state mirror.
 * Reflects the server's SessionState after each API response.
 */

export interface ProteinStability {
  temp: number;
  ph1: number;
  ph2: number;
}

export interface ProteinInfo {
  index: number;
  name: string;
  molWt: number;
  amount: number;
  activity: number;
  isopoint: number;
  stability: ProteinStability;
}

export interface StepRecord {
  stepType: string;
  proteinAmount: number;
  enzymeUnits: number;
  enzymeYield: number;
  enrichment: number;
  costPerUnit: number;
}

export interface GelBand {
  lane: number;
  position: number;
  intensity: number;
  proteinIndex: number;
  subunitMw: number;
}

export interface GelSpot {
  x: number;
  y: number;
  intensity: number;
  proteinIndex: number;
}

export interface SessionState {
  sessionId: string;
  phase: string;
  mixtureName: string;
  enzymeIndex: number;
  pooled: boolean;
  hasFractions: boolean;
  assayed: boolean;
  hasGradient: boolean;
  twoDGel: boolean;
  showBlot: boolean;
  scale: number;
  overDiluted: boolean;
  step: number;
  canSeparate: boolean;
  canPool: boolean;
  canAssay: boolean;
  canDilute: boolean;
  fractions: number[][];
  records: StepRecord[];
  gradientStart: number;
  gradientEnd: number;
  gradientType: string;
  separationTitle: string;
  proteins: ProteinInfo[];
  asResult?: { soluble: number[]; insoluble: number[] } | null;
  gelData?: (GelBand | GelSpot)[] | null;
  hicPrecipitation?: number;
  failureMessage?: string;
}

const STATE_CHANGE_EVENT = "pp-state-change";

let currentState: SessionState | null = null;

export function initState(): void {
  currentState = null;
}

export function getState(): SessionState | null {
  return currentState;
}

export function updateState(newState: SessionState): void {
  currentState = newState;
  document.dispatchEvent(
    new CustomEvent<SessionState>(STATE_CHANGE_EVENT, { detail: newState }),
  );
}

export function onStateChange(
  callback: (state: SessionState) => void,
): () => void {
  const handler = (e: Event) => {
    callback((e as CustomEvent<SessionState>).detail);
  };
  document.addEventListener(STATE_CHANGE_EVENT, handler);
  return () => document.removeEventListener(STATE_CHANGE_EVENT, handler);
}
