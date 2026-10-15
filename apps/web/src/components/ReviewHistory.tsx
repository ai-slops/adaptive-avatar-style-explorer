import { useEffect, useState } from "react";
import { api } from "../api";
import { human, describe } from "../ui";
import type { Project, Version } from "../types";
type Event = {
  event_id: string;
  action: string;
  domain: string;
  sequence: number;
  review_id: string | null;
  effective: boolean;
  payload: {
    outcome?: string;
    subjectVersionIds?: string[];
    trainingStatus?: string;
    region?: string;
  };
};
type FrozenReview = {
  region: string;
  qualification: {
    eligible: boolean;
    reasons: string[];
    preFeedbackPrediction: { probabilityA: number } | null;
  };
  sides: {
    side: string;
    version: Version;
    bundle: {
      items: {
        depiction: { asset_id: string };
        link: { status: string };
        observations: unknown[];
      }[];
    };
    evidenceHash: string;
  }[];
};
export function ReviewHistory({
  project,
  branch,
  run,
  onUndo,
}: {
  project: Project;
  branch: string;
  run: (f: () => Promise<void>) => Promise<void>;
  onUndo: (id: string) => Promise<void>;
}) {
  const [events, setEvents] = useState<Event[]>([]),
    [review, setReview] = useState<FrozenReview | null>(null);
  useEffect(() => {
    void api<Event[]>(
      `/projects/${project.project_id}/events?branchId=${branch}`,
    )
      .then(setEvents)
      .catch(() => {});
  }, [project.event_sequence, branch]);
  const undone = new Set(
    events
      .filter((e) => e.action === "undo")
      .map((e) => (e.payload as { targetEventId?: string }).targetEventId),
  );
  return (
    <section className="subtle-panel">
      <h3>Your decisions, with their original context.</h3>
      {events
        .filter((e) => e.action === "compare")
        .slice(-8)
        .reverse()
        .map((e) => (
          <div className="history-row" key={e.event_id}>
            <div>
              <strong>
                {human(e.payload.outcome ?? "choice")} ·{" "}
                {human(e.payload.region ?? "whole")}
              </strong>
              <p>
                Decision {e.sequence} ·{" "}
                {e.effective ? "effective" : "undone or superseded"} ·{" "}
                {human(e.payload.trainingStatus ?? "provisional")}
              </p>
            </div>
            <button
              onClick={() =>
                void run(async () => {
                  setReview(
                    await api(
                      `/projects/${project.project_id}/review-sessions/${e.review_id}`,
                    ),
                  );
                })
              }
            >
              Revisit frozen evidence
            </button>
            {e.effective && !undone.has(e.event_id) && (
              <button onClick={() => void run(() => onUndo(e.event_id))}>
                Undo decision
              </button>
            )}
          </div>
        ))}
      {review && (
        <div className="modal-scrim">
          <section
            className="modal wide"
            role="dialog"
            aria-modal="true"
            aria-labelledby="history-title"
          >
            <button
              className="close"
              aria-label="Close"
              onClick={() => setReview(null)}
            >
              ×
            </button>
            <p className="eyebrow">A HISTORICAL SNAPSHOT</p>
            <h2 id="history-title">The evidence behind your choice.</h2>
            <p>
              Later imports and corrections do not rewrite this context. A
              previous qualification may have since been invalidated.
            </p>
            <div className="comparison-grid">
              {review.sides.map((side) => (
                <section key={side.side}>
                  <h3>
                    {side.side} · revision {side.version.revision}
                  </h3>
                  <p>{describe(side.version)}</p>
                  {side.bundle.items.map((item, i) => (
                    <figure key={i}>
                      <img
                        className="historical-image"
                        src={`/api/projects/${project.project_id}/assets/${item.depiction.asset_id}`}
                        alt={`Historical side ${side.side} depiction ${i + 1}`}
                      />
                      <figcaption>
                        Exposed as {human(item.link.status)}
                      </figcaption>
                    </figure>
                  ))}
                </section>
              ))}
            </div>
            <p>
              Scope: {human(review.region)}.{" "}
              {review.qualification.eligible
                ? "Qualified when opened."
                : review.qualification.reasons.join(". ")}{" "}
              {review.qualification.preFeedbackPrediction
                ? `Before this decision, predicted A preference was ${(review.qualification.preFeedbackPrediction.probabilityA * 100).toFixed(0)}%.`
                : "No fitted prediction was available before this choice."}
            </p>
          </section>
        </div>
      )}
    </section>
  );
}
