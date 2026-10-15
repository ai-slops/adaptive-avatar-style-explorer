import { useState } from "react";
import type { Version, Evidence, Project, Region } from "../types";
import { views, regions, image, human, describe, emptySpec } from "../ui";
import { api } from "../api";
export function Compare({
  versions,
  ids,
  setIds,
  evidence,
  project,
  title,
  branch,
  run,
  refresh,
  setNotice,
}: {
  versions: Version[];
  ids: string[];
  setIds: (ids: string[]) => void;
  evidence: Record<string, Evidence>;
  project: Project;
  title: (v: string) => string;
  branch: string;
  run: (f: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
  setNotice: (s: string) => void;
}) {
  const [region, setRegion] = useState<Region>("hair"),
    [view, setView] = useState("front"),
    [intent, setIntent] = useState(false),
    [review, setReview] = useState<{
      reviewSessionId: string;
      qualification: { eligible: boolean; reasons: string[] };
    } | null>(null);
  const links = ids
    .slice(0, 2)
    .map(
      (id) =>
        evidence[id]?.links.filter((l) =>
          l.observations.some(
            (o) =>
              o.observedPresentation.view === view &&
              (region === "whole" ||
                o.region === region ||
                o.region === "whole"),
          ),
        ) ?? [],
    );
  const [selectedLinks, setSelectedLinks] = useState<string[]>([]);
  const chosen = links.map(
    (ls, i) =>
      ls.find((l) => l.link_id === selectedLinks[i]) ??
      ls.find((l) => l.status === "compatible") ??
      ls[0],
  );
  const structuralViews = [
    "front",
    "character_left_profile",
    "character_right_profile",
    "back",
  ];
  const wholeLinks = ids.slice(0, 2).map((id) =>
    structuralViews.map((view) => {
      const candidates =
        evidence[id]?.links.filter((l) =>
          l.observations.some((o) => o.observedPresentation.view === view),
        ) ?? [];
      return candidates.find((l) => l.status === "compatible") ?? candidates[0];
    }),
  );
  const exposed = ids
    .slice(0, 2)
    .map((_, i) =>
      intent
        ? []
        : region === "whole"
          ? wholeLinks[i].filter((l) => !!l).map((l) => l.link_id)
          : chosen[i]
            ? [chosen[i].link_id]
            : [],
    );
  function change(action: () => void) {
    setReview(null);
    action();
  }
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">A CONSIDERED COMPARISON</p>
          <h1>Which design feels like you?</h1>
          <p>Compare the same observed view. Missing evidence stays missing.</p>
        </div>
      </div>
      <div className="compare-controls">
        <label>
          Compare scope
          <select
            value={region}
            onChange={(e) => change(() => setRegion(e.target.value as Region))}
          >
            {regions.map((r) => (
              <option key={r} value={r}>
                {human(r)}
              </option>
            ))}
          </select>
        </label>
        <label>
          View
          <select
            value={view}
            disabled={region === "whole"}
            onChange={(e) => change(() => setView(e.target.value))}
          >
            {views.map((v) => (
              <option key={v} value={v}>
                {human(v)}
              </option>
            ))}
          </select>
        </label>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={intent}
            onChange={(e) => change(() => setIntent(e.target.checked))}
          />
          Compare written ideas only
        </label>
      </div>
      <div className="comparison-grid">
        {[0, 1].map((side) => (
          <section className="compare-side" key={side}>
            <div className="compare-side-heading">
              <span>{side === 0 ? "A" : "B"}</span>
              <label>
                Design {side === 0 ? "A" : "B"}
                <select
                  value={ids[side] ?? ""}
                  onChange={(e) =>
                    change(() => {
                      const next = [...ids];
                      next[side] = e.target.value;
                      setIds(next);
                    })
                  }
                >
                  <option value="">Choose a design</option>
                  {versions.map((v) => (
                    <option value={v.version_id} key={v.version_id}>
                      {title(v.version_id)} · v{v.revision}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            {!intent && region === "whole" ? (
              <div className="multi-compare">
                {structuralViews.map((v, i) => (
                  <figure key={v}>
                    {wholeLinks[side]?.[i] ? (
                      <img
                        src={image(project.project_id, wholeLinks[side][i])}
                        alt={`Comparison ${side === 0 ? "A" : "B"}: observed ${human(v)}`}
                      />
                    ) : (
                      <div className="missing-view">No evidence</div>
                    )}
                    <figcaption>{human(v)}</figcaption>
                  </figure>
                ))}
              </div>
            ) : (
              <>
                <label
                  className={
                    links[side]?.length > 1 ? "depiction-choice" : "sr-only"
                  }
                >
                  Depiction for {side === 0 ? "A" : "B"}
                  <select
                    value={chosen[side]?.link_id ?? ""}
                    onChange={(e) =>
                      change(() => {
                        const selected = [...selectedLinks];
                        selected[side] = e.target.value;
                        setSelectedLinks(selected);
                      })
                    }
                  >
                    {links[side]?.map((l) => (
                      <option key={l.link_id} value={l.link_id}>
                        {human(
                          l.observations[0]?.observedPresentation.framing ??
                            "unknown",
                        )}{" "}
                        · {l.link_id.slice(0, 8)}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="comparison-image">
                  {!intent && chosen[side] ? (
                    <img
                      src={image(project.project_id, chosen[side])}
                      alt={`Comparison ${side === 0 ? "A" : "B"}: observed ${human(view)}`}
                    />
                  ) : (
                    <div className="empty-state">
                      <h3>
                        {intent
                          ? "Written design intent"
                          : "No evidence in this view"}
                      </h3>
                      <p>
                        {intent
                          ? describe(
                              versions.find(
                                (v) => v.version_id === ids[side],
                              ) ?? ({ spec: emptySpec() } as Version),
                            )
                          : "Import and review this slot before comparing visual properties."}
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}
            {chosen[side] && !intent && region !== "whole" && (
              <p className="muted">
                {human(chosen[side].status)} ·{" "}
                {human(
                  chosen[side].observations[0]?.observedPresentation
                    .projection ?? "unknown",
                )}{" "}
                projection ·{" "}
                {chosen[side].assessment.reviewedRegions.map(human).join(", ")}
              </p>
            )}
          </section>
        ))}
      </div>
      {!review ? (
        <button
          className="primary"
          disabled={ids.length < 2 || !ids[0] || !ids[1]}
          onClick={() =>
            void run(async () => {
              setReview(
                await api(`/projects/${project.project_id}/review-sessions`, {
                  branchId: branch,
                  region,
                  versionA: ids[0],
                  versionB: ids[1],
                  linkIdsA: [...new Set(exposed[0])],
                  linkIdsB: [...new Set(exposed[1])],
                  domain: intent ? "design_intent" : "visual_design",
                  expectedEventSequence: project.event_sequence,
                }),
              );
            })
          }
        >
          Seal this comparison →
        </button>
      ) : (
        <section className="feedback-panel">
          <p>
            {review.qualification.eligible
              ? "This matched, scoped comparison can inform visual preference learning."
              : `Saved as provisional interest. ${review.qualification.reasons.join(". ")}`}
          </p>
          <div className="feedback-buttons">
            {[
              ["A", "Choose A"],
              ["B", "Choose B"],
              ["tie", "No preference"],
              ["neither", "Neither"],
              ["skip", "Skip"],
            ].map(([outcome, label]) => (
              <button
                className={outcome === "A" || outcome === "B" ? "primary" : ""}
                key={outcome}
                onClick={() =>
                  void run(async () => {
                    await api(`/projects/${project.project_id}/feedback`, {
                      eventId: crypto.randomUUID(),
                      branchId: branch,
                      action: "compare",
                      domain: intent ? "design_intent" : "visual_design",
                      reviewSessionId: review.reviewSessionId,
                      region,
                      outcome,
                      expectedEventSequence: project.event_sequence,
                    });
                    setReview(null);
                    await refresh();
                    setNotice("Decision saved with the exact evidence shown.");
                  })
                }
              >
                {label}
              </button>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
