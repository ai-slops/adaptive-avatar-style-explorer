import type { Region, Spec, Property, Link, Version } from "./types";
export const views = [
  "front",
  "front_three_quarter",
  "character_left_profile",
  "character_right_profile",
  "back",
  "back_three_quarter",
  "top",
  "bottom",
  "other",
  "unknown",
];
export const regions: Region[] = [
  "whole",
  "face",
  "hair",
  "body",
  "outfit",
  "accessories",
  "palette",
  "surface",
  "custom",
];
export const human = (s: string) =>
  s.replaceAll("_", " ").replaceAll(".", " · ");
export const emptySpec = (): Spec => ({
  morphology: "unspecified",
  properties: {},
  componentRelations: [],
  unresolvedDecisions: [],
});
export const property = (value: string): Property => ({
  value: value || null,
  state: value ? "proposed" : "unspecified",
  sourceEventIds: [],
  sourceDepictionLinkIds: [],
  notes: "",
});
export const image = (p: string, link: Link) =>
  `/api/projects/${p}/assets/${link.depiction.asset_id}`;
export const describe = (v: Version) =>
  Object.entries(v.spec.properties)
    .filter(([, p]) => p.value !== null)
    .map(([k, p]) => `${human(k)}: ${String(p.value)}`)
    .join(" · ") ||
  "An open design direction. Add a description or reference to begin.";
