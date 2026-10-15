import { useState } from "react";
import type { Version, Evidence, Project } from "../types";
import { api, download } from "../api";
export function Handoff({
  version,
  evidence,
  project,
  run,
  refresh,
  notice,
}: {
  version: Version;
  evidence: Evidence;
  project: Project;
  run: (f: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
  notice: (s: string) => void;
}) {
  const [gaps, setGaps] = useState(""),
    [checks, setChecks] = useState(
      "Confirm identity across views\nReview silhouette and component attachments\nTest garment behavior in relevant poses",
    ),
    [stage, setStage] = useState("design_selected");
  return (
    <div className="inspect-grid">
      <section className="paper-panel">
        <h2>Confirm a design checkpoint.</h2>
        <p>
          Preserve this version with the gaps and acceptance checks a model
          maker needs.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              await api(`/projects/${project.project_id}/checkpoints`, {
                versionId: version.version_id,
                stage,
                acceptedGaps: gaps.split("\n").filter(Boolean),
                acceptanceChecks: checks.split("\n").filter(Boolean),
                expectedEventSequence: project.event_sequence,
              });
              await refresh();
              notice(
                "Checkpoint recorded. Technical model checks remain pending.",
              );
            });
          }}
        >
          <label>
            Checkpoint stage
            <select value={stage} onChange={(e) => setStage(e.target.value)}>
              <option value="design_selected">Design selected</option>
              <option value="reference_handoff_ready">
                Reference handoff ready
              </option>
            </select>
          </label>
          <label>
            Accepted gaps and tradeoffs
            <textarea
              value={gaps}
              onChange={(e) => setGaps(e.target.value)}
              placeholder="Record missing surfaces, conflicting references, or untested states explicitly."
            />
          </label>
          <label>
            Model-build acceptance checks
            <textarea
              required
              value={checks}
              onChange={(e) => setChecks(e.target.value)}
            />
          </label>
          <button className="primary">Confirm checkpoint →</button>
        </form>
      </section>
      <section className="paper-panel export-panel">
        <span className="eyebrow">DESIGN HANDOFF / V{version.revision}</span>
        <h2>Ready for the next pair of hands.</h2>
        <p>
          Your canonical specification, component relationships, reference
          manifest, coverage, findings, prompt packs, and learning provenance in
          one archive.
        </p>
        <div className="handoff-stat">
          <strong>
            {evidence.referenceCoverage === null
              ? "—"
              : `${Math.round(evidence.referenceCoverage * 100)}%`}
          </strong>
          <span>
            reference completeness
            <br />
            for this profile
          </span>
        </div>
        <p className="muted">
          Unseen geometry stays unknown. Topology, rigging, skinning, and
          runtime performance remain pending until tested on an actual model.
        </p>
        <button
          className="primary"
          onClick={() =>
            void run(() =>
              download(
                `/projects/${project.project_id}/exports`,
                { versionId: version.version_id, kind: "handoff" },
                "avatar-design-handoff.zip",
              ),
            )
          }
        >
          Export 3D design handoff ↓
        </button>
      </section>
    </div>
  );
}
