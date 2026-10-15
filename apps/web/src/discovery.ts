import type { Spec } from "./types";

export const parts = {
  face: "얼굴·턱",
  hair: "머리",
  outfit: "의상",
  body: "체형",
  accessories: "장식",
  palette: "색상",
} as const;
export type Part = keyof typeof parts;
export type DiscoveryImage = {
  linkId: string;
  assetId: string;
  status: string;
  versionId: string;
  exportPermission: boolean;
};
export type Candidate = {
  candidateId: string;
  directionId: string;
  roundId: string;
  versionId: string;
  position: number;
  label: string;
  purpose: string;
  kind: string;
  preserveParts: Part[];
  varyPart?: Part | "whole";
  view?: string;
  sourceCandidateId?: string;
  sourceLinkIds: string[];
  referenceImages: DiscoveryImage[];
  proposal: Spec;
  image: DiscoveryImage | null;
  returnName: string;
  prompt: {
    promptText: string;
    references: { assetId: string; instruction: string }[];
  } | null;
  job?: { state: string; result?: { error?: string } };
  error?: string;
};
export type Round = {
  roundId: string;
  ordinal: number;
  explanation: string;
  intent: string;
  preparation: string;
  error?: string;
  historicalFeedback: boolean;
  candidates: Candidate[];
};
export type Direction = {
  directionId: string;
  label: string;
  candidate: Candidate;
  preserved: Partial<Record<Part, { linkId: string; candidateId: string }>>;
};
export type Selection = {
  selectionId: string;
  candidateId: string;
  versionId: string;
  label: string;
  image: DiscoveryImage;
  preserved: Record<string, unknown>;
  coverageUnconfigured?: boolean;
  uncheckedViews: { view: string; status: string }[];
  unresolved: string[];
  status: string;
};
export type Batch = {
  batchId: string;
  roundId: string;
  state: string;
  candidateIds: string[];
  completed: number;
  authorizedTurns: number;
  message: string;
};
export type DiscoveryState = {
  revision: number;
  activeRoundId: string | null;
  rounds: Round[];
  directions: Direction[];
  selection: Selection | null;
  rejected: string[];
  wrongLinks: string[];
  history: {
    reactionId: string;
    action: string;
    labels: string[];
    part?: Part;
    canUndo: boolean;
  }[];
  library: { versionId: string; label: string; image: DiscoveryImage | null }[];
  inspirations: { inspirationId: string; assetId: string }[];
  batches: Batch[];
  nextStep: string;
  mode: string;
};
export const reactionNames: Record<string, string> = {
  interest: "이 방향 저장",
  release_direction: "방향 저장 해제",
  choose_a: "A 선택",
  choose_b: "B 선택",
  both: "둘 다 탐색",
  no_preference: "차이를 고르기 어려움",
  neither: "마음에 드는 후보 없음",
  skip: "판단 보류",
  image_wrong: "이미지 문제 표시",
  keep_part: "부분 보존",
  unlock_part: "부분 보존 해제",
  rename_direction: "방향 이름 변경",
  use_design: "디자인 선택",
};
export const assetURL = (project: string, asset: string) =>
  `/api/projects/${project}/assets/${asset}`;
