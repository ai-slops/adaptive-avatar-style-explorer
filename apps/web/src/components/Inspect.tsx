import { useState } from "react";
import type {
  Version,
  Evidence,
  Project,
  Plan,
  Preferences,
  Link,
} from "../types";
import { image, human } from "../ui";
import { api } from "../api";
import { EvidenceEditor } from "./EvidenceEditor";
export function Inspect({
  version,
  evidence,
  project,
  plans,
  preferences,
  onEdit,
  run,
  refresh,
  feedback,
}: {
  version: Version;
  evidence: Evidence;
  project: Project;
  plans: Plan[];
  preferences: Preferences | null;
  onEdit: () => void;
  run: (f: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
  feedback: (
    a: string,
    v?: string,
    e?: Record<string, unknown>,
  ) => Promise<void>;
}) {
  const [reviewing, setReviewing] = useState<Link | null>(null),
    [importPlan, setImportPlan] = useState(""),
    [exportPermission, setExportPermission] = useState(false);
  return (
    <>
      <div className="inspect-grid">
        <section className="paper-panel">
          <div className="section-heading">
            <h2>What defines this character</h2>
            <button onClick={onEdit}>Revise design ↗</button>
          </div>
          <p className="muted">
            Revision {version.revision} · {human(version.spec.morphology)}
          </p>
          {Object.entries(version.spec.properties).map(([key, p]) => (
            <div className="requirement" key={key}>
              <div>
                <strong>{human(key)}</strong>
                <p>{String(p.value ?? "Unknown")}</p>
                <span className="small-tag">{human(p.state)}</span>
              </div>
              <button
                onClick={() =>
                  void run(() =>
                    feedback(
                      preferences?.locks[version.version_id]?.includes(key)
                        ? "unlock_property"
                        : "lock_property",
                      version.version_id,
                      { propertyKey: key },
                    ),
                  )
                }
              >
                {preferences?.locks[version.version_id]?.includes(key)
                  ? "✓ Preserved"
                  : "Keep this component"}
              </button>
            </div>
          ))}
          {version.spec.unresolvedDecisions.length > 0 && (
            <div className="unresolved">
              <h3>Still to decide</h3>
              {version.spec.unresolvedDecisions.map((x) => (
                <p key={x}>○ {x}</p>
              ))}
            </div>
          )}
          <details>
            <summary>Canonical hash & component relationships</summary>
            <code>{version.canonical_hash}</code>
            {version.spec.componentRelations.map((r, i) => (
              <p key={i}>
                {r.component} {human(r.relation)} {r.target} ({human(r.state)})
              </p>
            ))}
          </details>
        </section>
        <section className="paper-panel">
          <h2>Reference coverage</h2>
          <p className="metric">
            {evidence.referenceCoverage === null
              ? "—"
              : `${Math.round(evidence.referenceCoverage * 100)}%`}
          </p>
          <p className="muted">{evidence.coverageMeaning}</p>
          {evidence.slots.map((slot) => (
            <div className="slot" key={slot.id}>
              <span>
                {human(slot.view)}
                <small>
                  {slot.framing} · {slot.required ? "required" : "recommended"}
                </small>
              </span>
              <span className={slot.status === "missing" ? "missing" : "good"}>
                {slot.status === "missing" ? "○ Missing" : "✓ Reviewed"}
              </span>
            </div>
          ))}
          {!evidence.slots.length && (
            <p>
              Configure evaluation requirements for this character structure.
              Humanoid slots are not assumed.
            </p>
          )}
        </section>
      </div>
      <section className="paper-panel import-panel">
        <div>
          <h2>Bring in real evidence.</h2>
          <p>
            Import independently produced PNG, JPEG or WebP files. Each result
            enters review.
          </p>
        </div>
        <label>
          Result belongs to
          <select
            value={importPlan}
            onChange={(e) => setImportPlan(e.target.value)}
          >
            <option value="">Unassociated reference / inspiration</option>
            {plans
              .filter((p) => p.targetDesignVersionId === version.version_id)
              .map((p) => (
                <option key={p.planId} value={p.planId}>
                  {human(p.purpose)} · revision {p.revision}
                </option>
              ))}
          </select>
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={exportPermission}
            onChange={(e) => setExportPermission(e.target.checked)}
          />
          I permit including this reference in exports
        </label>
        <label className="button primary upload">
          ＋ Import image
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              void run(async () => {
                const base = `/projects/${project.project_id}`;
                const a = await api<{ assetId: string }>(
                  base + "/assets",
                  file,
                );
                const plan = plans.find((p) => p.planId === importPlan);
                const d = await api<{ depictionId: string }>(
                  base + "/external-results",
                  {
                    assetId: a.assetId,
                    sourceKind: plan ? "external_result" : "reference",
                    originPlanId: plan?.planId ?? null,
                    originPromptRevision: plan?.revision ?? null,
                    explicitlyUnassociated: !plan,
                    exportPermission,
                  },
                );
                await api(base + "/depiction-links", {
                  depictionId: d.depictionId,
                  versionId: version.version_id,
                });
                await refresh();
              });
              e.target.value = "";
            }}
          />
        </label>
      </section>
      <div className="evidence-grid">
        {evidence.links.map((link) => (
          <article className="evidence-card" key={link.link_id}>
            <img
              src={image(project.project_id, link)}
              alt="Imported character depiction"
            />
            <div>
              <span className="small-tag">{human(link.status)}</span>
              <h3>
                {human(
                  link.observations[0]?.observedPresentation.view ??
                    "View not reviewed",
                )}
              </h3>
              <p>{human(link.depiction.source_kind)}</p>
              <button onClick={() => setReviewing(link)}>
                {link.status === "unreviewed"
                  ? "Review evidence"
                  : "Correct assessment"}{" "}
                →
              </button>
            </div>
          </article>
        ))}
      </div>
      {evidence.findings.length > 0 && (
        <section className="paper-panel">
          <h2>Findings & open questions</h2>
          {evidence.findings.map((f) => (
            <div className="finding" key={f.finding_id}>
              <span>
                {human(f.kind)} · {human(f.state)}
              </span>
              <p>{JSON.parse(f.details_json).description}</p>
            </div>
          ))}
        </section>
      )}
      <div className="inline-actions">
        <button
          onClick={() =>
            void run(() => feedback("reject_design", version.version_id))
          }
        >
          Not my design
        </button>
        {preferences?.activeEventIds.length ? (
          <button
            onClick={() =>
              void run(() =>
                feedback("undo", undefined, {
                  targetEventId: [...preferences.activeEventIds]
                    .reverse()
                    .find(() => true),
                }),
              )
            }
          >
            Undo latest action
          </button>
        ) : null}
      </div>
      {reviewing && (
        <EvidenceEditor
          link={reviewing}
          project={project}
          onClose={() => setReviewing(null)}
          onSave={async (data) => {
            await run(async () => {
              await api(
                `/projects/${project.project_id}/evidence-reviews`,
                data,
              );
              setReviewing(null);
              await refresh();
            });
          }}
        />
      )}
    </>
  );
}
