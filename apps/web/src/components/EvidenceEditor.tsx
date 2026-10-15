import { useState } from "react";
import type { Link, Project, Observation, Region } from "../types";
import { regions, views, image, human } from "../ui";

const numericFeatures: Record<string, string[]> = {
  whole: [
    "body.head_ratio",
    "face.angularity",
    "face.eye_exaggeration",
    "hair.volume",
    "outfit.ornament_density",
    "outfit.layering",
    "palette.saturation",
    "palette.lightness",
    "palette.contrast",
    "material.gloss",
  ],
  face: ["face.angularity", "face.eye_exaggeration"],
  hair: ["hair.volume"],
  body: ["body.head_ratio"],
  outfit: ["outfit.ornament_density", "outfit.layering"],
  palette: ["palette.saturation", "palette.lightness", "palette.contrast"],
  surface: ["material.gloss"],
};
export function EvidenceEditor({
  link,
  project,
  onClose,
  onSave,
  suggestion,
}: {
  link: Link;
  project: Project;
  onClose: () => void;
  onSave: (data: unknown) => Promise<void>;
  suggestion?: Observation;
}) {
  const existing = suggestion ?? link.observations[0];
  const [region, setRegion] = useState<Region>(existing?.region ?? "whole"),
    [status, setStatus] = useState(
      link.status === "unreviewed" ? "compatible" : link.status,
    );
  const [presentation, setPresentation] = useState(
    existing?.observedPresentation ?? {
      view: "unknown",
      projection: "unknown",
      framing: "unknown",
      poseId: null,
      expressionId: null,
      lightingClass: null,
      backgroundClass: null,
      source: "user_reported",
    },
  );
  const [values, setValues] = useState<Record<string, string>>(
      Object.fromEntries(
        Object.entries(existing?.attributes ?? {})
          .filter(
            ([, a]) =>
              typeof a.value === "number" &&
              a.visibility === "visible" &&
              a.confidence >= 0.6,
          )
          .map(([k, a]) => [k, String(a.value)]),
      ),
    ),
    [issue, setIssue] = useState(""),
    [kind, setKind] = useState("identity_or_design_drift");
  return (
    <div className="modal-scrim">
      <section
        className="modal wide"
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidence-title"
      >
        <button className="close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <p className="eyebrow">REVIEW WHAT IS ACTUALLY VISIBLE</p>
        <h2 id="evidence-title">Evidence, not assumptions.</h2>
        <div className="review-layout">
          <img
            src={image(project.project_id, link)}
            alt="Depiction being assessed"
          />
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const attributes = Object.fromEntries(
                Object.entries(values)
                  .filter(([, v]) => v !== "")
                  .map(([k, v]) => [
                    k,
                    {
                      value: Number(v),
                      confidence: 0.8,
                      visibility: "visible",
                    },
                  ]),
              );
              void onSave({
                linkId: link.link_id,
                status,
                reviewedRegions: [region],
                observations:
                  status === "mismatch"
                    ? []
                    : [
                        {
                          region,
                          attributes,
                          observedPresentation: presentation,
                        },
                      ],
                findings: issue
                  ? [
                      {
                        kind,
                        region,
                        severity:
                          status === "compatible" ? "warning" : "blocking",
                        description: issue,
                      },
                    ]
                  : [],
                expectedEventSequence: project.event_sequence,
              });
            }}
          >
            <label>
              Does this depict the intended design?
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="compatible">Compatible in reviewed scope</option>
                <option value="partial">Only some regions are faithful</option>
                <option value="mismatch">
                  Different character / bad depiction
                </option>
              </select>
            </label>
            <label>
              Reviewed scope
              <select
                value={region}
                onChange={(e) => {
                  setRegion(e.target.value as Region);
                  setValues({});
                }}
              >
                {regions.map((r) => (
                  <option key={r} value={r}>
                    {human(r)}
                  </option>
                ))}
              </select>
            </label>
            <div className="inline-inputs">
              <label>
                Observed view
                <select
                  value={presentation.view}
                  onChange={(e) =>
                    setPresentation({ ...presentation, view: e.target.value })
                  }
                >
                  {views.map((v) => (
                    <option key={v} value={v}>
                      {human(v)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Observed framing
                <select
                  value={presentation.framing}
                  onChange={(e) =>
                    setPresentation({
                      ...presentation,
                      framing: e.target.value,
                    })
                  }
                >
                  {["unknown", "full_body", "upper_body", "face", "detail"].map(
                    (v) => (
                      <option key={v} value={v}>
                        {human(v)}
                      </option>
                    ),
                  )}
                </select>
              </label>
            </div>
            <label>
              Observed projection
              <select
                value={presentation.projection}
                onChange={(e) =>
                  setPresentation({
                    ...presentation,
                    projection: e.target.value,
                  })
                }
              >
                <option value="unknown">
                  Unknown — requested orthographic is not proof
                </option>
                <option value="orthographic">
                  Orthographic, supported by evidence
                </option>
                <option value="perspective">Perspective</option>
              </select>
            </label>
            <div className="inline-inputs">
              {[
                ["poseId", "Pose"],
                ["expressionId", "Expression"],
                ["lightingClass", "Lighting"],
                ["backgroundClass", "Background"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <input
                    value={presentation[key as keyof typeof presentation] ?? ""}
                    onChange={(e) =>
                      setPresentation({
                        ...presentation,
                        [key]: e.target.value || null,
                      })
                    }
                    placeholder={
                      key === "backgroundClass"
                        ? "plain (if observed)"
                        : "neutral (if observed)"
                    }
                  />
                </label>
              ))}
            </div>
            {status !== "mismatch" && (
              <details>
                <summary>Manual visual feature entry (optional)</summary>
                <p className="muted">
                  Only enter visible, reliable properties. Blank means unknown.
                  Numeric descriptors are coarse judgments.
                </p>
                {(numericFeatures[region] ?? []).map((k) => (
                  <label key={k}>
                    {human(k)}
                    <input
                      type="number"
                      step="0.01"
                      min={k === "body.head_ratio" ? ".08" : "0"}
                      max={k === "body.head_ratio" ? ".60" : "1"}
                      value={values[k] ?? ""}
                      onChange={(e) =>
                        setValues({ ...values, [k]: e.target.value })
                      }
                      placeholder="Unknown"
                    />
                  </label>
                ))}
              </details>
            )}
            <label>
              Finding type
              <select value={kind} onChange={(e) => setKind(e.target.value)}>
                {[
                  "identity_or_design_drift",
                  "presentation_mismatch",
                  "design_unspecified",
                  "cross_view_conflict",
                  "design_suitability",
                  "execution_defect",
                ].map((k) => (
                  <option key={k} value={k}>
                    {human(k)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Concern or unresolved detail
              <textarea
                value={issue}
                onChange={(e) => setIssue(e.target.value)}
                placeholder="The profile changed the hairstyle; this is not a rejection of the design."
              />
            </label>
            <button className="primary">Publish assessment →</button>
          </form>
        </div>
      </section>
    </div>
  );
}
