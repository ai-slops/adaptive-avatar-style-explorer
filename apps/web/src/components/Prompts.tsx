import { useState } from "react";
import type { Version, Evidence, Project, Plan } from "../types";
import { human, views, describe } from "../ui";
import { api, download } from "../api";
export function Prompts({
  version,
  evidence,
  project,
  plans,
  run,
  refresh,
  notice,
  onImport,
}: {
  version: Version;
  evidence: Evidence;
  project: Project;
  plans: Plan[];
  run: (f: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
  notice: (s: string) => void;
  onImport: () => void;
}) {
  const [purpose, setPurpose] = useState("additional_view"),
    [view, setView] = useState("character_left_profile"),
    [changes, setChanges] = useState("");
  const packs = plans.filter(
    (p) => p.targetDesignVersionId === version.version_id,
  );
  return (
    <>
      <section className="paper-panel">
        <h2>One request. One clear purpose.</h2>
        <p>
          Prepare text, then independently produce the result in a tool of your
          choice. Import it here for review.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              const seen = new Set<string>();
              const references = evidence.links
                .filter(
                  (l) =>
                    l.status === "compatible" &&
                    !seen.has(l.depiction.asset_id) &&
                    !!seen.add(l.depiction.asset_id),
                )
                .slice(0, 10)
                .map((l) => ({
                  assetId: l.depiction.asset_id,
                  role: "identity",
                  instruction: `Use this reviewed reference for the same ${describe(version)}. Preserve ${l.assessment.reviewedRegions.map(human).join(", ")}.`,
                }));
              await api(`/projects/${project.project_id}/prompt-packs`, {
                targetVersionId: version.version_id,
                purpose,
                recipe: { view },
                changeDesignProperties: changes.split("\n").filter(Boolean),
                references,
                expectedEventSequence: project.event_sequence,
              });
              await refresh();
              notice("Text prompt prepared. No image has been generated.");
            });
          }}
        >
          <div className="inline-inputs">
            <label>
              Purpose
              <select
                value={purpose}
                onChange={(e) => {
                  setPurpose(e.target.value);
                  setChanges("");
                }}
              >
                {[
                  "design_variant",
                  "additional_view",
                  "unspecified_part",
                  "state_study",
                  "depiction_correction",
                ].map((p) => (
                  <option value={p} key={p}>
                    {human(p)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Requested view
              <select value={view} onChange={(e) => setView(e.target.value)}>
                {views
                  .filter((v) => v !== "unknown")
                  .map((v) => (
                    <option value={v} key={v}>
                      {human(v)}
                    </option>
                  ))}
              </select>
            </label>
          </div>
          {["design_variant", "unspecified_part"].includes(purpose) && (
            <label>
              Properties to propose changes to
              <textarea
                required
                value={changes}
                onChange={(e) => setChanges(e.target.value)}
                placeholder="Existing property keys, one per line"
              />
            </label>
          )}
          <button className="primary">Prepare text prompt ↗</button>
        </form>
      </section>
      {packs.map((p) => (
        <section className="paper-panel prompt-card" key={p.planId}>
          <div className="section-heading">
            <div>
              <span className="small-tag">
                {human(p.purpose)} · {p.freshness}
              </span>
              <h2>
                Design v{version.revision} / prompt r{p.revision}
              </h2>
            </div>
            <button
              onClick={() =>
                void run(async () => {
                  await navigator.clipboard.writeText(p.promptText);
                  notice(
                    "Prompt copied. Attach the listed references independently.",
                  );
                })
              }
            >
              Copy text ↗
            </button>
          </div>
          <pre>{p.promptText}</pre>
          {p.references.map((r) => (
            <p key={r.attachmentOrder}>
              Attachment {r.attachmentOrder}: {r.role} ·{" "}
              <a
                href={`/api/projects/${project.project_id}/assets/${r.assetId}`}
                download={`reference-${r.attachmentOrder}.png`}
              >
                Download reference
              </a>
            </p>
          ))}
          <div className="inline-actions">
            <button
              onClick={() =>
                void run(() =>
                  download(
                    `/projects/${project.project_id}/exports`,
                    { versionId: version.version_id, kind: "prompt_pack" },
                    "prompt-pack.zip",
                  ),
                )
              }
            >
              Export prompt pack
            </button>
            <button onClick={onImport}>Import independent result →</button>
          </div>
        </section>
      ))}
      {!packs.length && (
        <div className="empty-state">
          <h2>A missing view is a useful next step.</h2>
          <p>Keep the character fixed while asking for new evidence.</p>
        </div>
      )}
    </>
  );
}
