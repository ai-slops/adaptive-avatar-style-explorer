import { useState } from "react";
import type { Evidence, Project, Slot, Region } from "../types";
import { human, views, regions } from "../ui";
import { api } from "../api";
export function ProfileEditor({
  evidence,
  project,
  onClose,
  onSaved,
  run,
}: {
  evidence: Evidence;
  project: Project;
  onClose: () => void;
  onSaved: () => Promise<void>;
  run: (f: () => Promise<void>) => Promise<void>;
}) {
  const [slots, setSlots] = useState<Slot[]>(structuredClone(evidence.slots)),
    [stage, setStage] = useState("custom"),
    [rationale, setRationale] = useState("");
  function update(index: number, change: Partial<Slot>) {
    setSlots((rows) =>
      rows.map((slot, i) => (i === index ? { ...slot, ...change } : slot)),
    );
  }
  return (
    <div className="modal-scrim">
      <section
        className="modal wide"
        role="dialog"
        aria-modal="true"
        aria-labelledby="profile-title"
      >
        <button className="close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <p className="eyebrow">A TEST PLAN, NOT A TASTE PROFILE</p>
        <h2 id="profile-title">What must this character hold up to?</h2>
        <p>
          Set required surfaces and relevant states for this design. A new
          profile preserves older comparison snapshots.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              await api(`/projects/${project.project_id}/evaluation-profiles`, {
                versionId: evidence.version.version_id,
                stage,
                slots: slots.map((s) => ({
                  id: s.id,
                  view: s.view,
                  framing: s.framing,
                  region: s.region ?? "whole",
                  poseId: s.poseId ?? "neutral",
                  expressionId: s.expressionId ?? "neutral",
                  required: s.required,
                  notApplicableReason: s.notApplicableReason ?? null,
                  notApplicableBasis: s.notApplicableReason
                    ? (s.notApplicableBasis ?? "project_scope")
                    : null,
                })),
                changeRationale: rationale,
                expectedEventSequence: project.event_sequence,
              });
              await onSaved();
              onClose();
            });
          }}
        >
          <label>
            Evaluation stage
            <select value={stage} onChange={(e) => setStage(e.target.value)}>
              {[
                "screening",
                "shortlist",
                "finalist",
                "prototype",
                "custom",
              ].map((x) => (
                <option key={x} value={x}>
                  {human(x)}
                </option>
              ))}
            </select>
          </label>
          {slots.map((slot, index) => (
            <section className="profile-slot" key={slot.id}>
              <div className="section-heading">
                <h3>Slot {index + 1}</h3>
                <button
                  type="button"
                  onClick={() =>
                    setSlots((rows) => rows.filter((_, i) => i !== index))
                  }
                >
                  Remove slot
                </button>
              </div>
              <div className="inline-inputs">
                <label>
                  View
                  <select
                    value={slot.view}
                    onChange={(e) => update(index, { view: e.target.value })}
                  >
                    {views
                      .filter((v) => v !== "unknown")
                      .map((v) => (
                        <option key={v} value={v}>
                          {human(v)}
                        </option>
                      ))}
                  </select>
                </label>
                <label>
                  Framing
                  <select
                    value={slot.framing}
                    onChange={(e) => update(index, { framing: e.target.value })}
                  >
                    {["full_body", "upper_body", "face", "detail"].map((v) => (
                      <option key={v} value={v}>
                        {human(v)}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Review region
                  <select
                    value={slot.region ?? "whole"}
                    onChange={(e) =>
                      update(index, { region: e.target.value as Region })
                    }
                  >
                    {regions.map((r) => (
                      <option key={r} value={r}>
                        {human(r)}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="inline-inputs">
                <label>
                  Pose / articulation state
                  <input
                    value={slot.poseId ?? "neutral"}
                    required
                    onChange={(e) => update(index, { poseId: e.target.value })}
                  />
                </label>
                <label>
                  Expression / deformation state
                  <input
                    value={slot.expressionId ?? "neutral"}
                    required
                    onChange={(e) =>
                      update(index, { expressionId: e.target.value })
                    }
                  />
                </label>
              </div>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={slot.required}
                  onChange={(e) =>
                    update(index, { required: e.target.checked })
                  }
                />
                Required for this evaluation stage
              </label>
              <div className="inline-inputs">
                <label>
                  Not applicable reason, if any
                  <input
                    value={slot.notApplicableReason ?? ""}
                    minLength={10}
                    onChange={(e) =>
                      update(index, {
                        notApplicableReason: e.target.value || null,
                      })
                    }
                    placeholder="Explain morphology or project scope"
                  />
                </label>
                {slot.notApplicableReason && (
                  <label>
                    Reason basis
                    <select
                      value={slot.notApplicableBasis ?? "project_scope"}
                      onChange={(e) =>
                        update(index, {
                          notApplicableBasis: e.target.value as
                            "morphology" | "project_scope",
                        })
                      }
                    >
                      <option value="morphology">Morphology</option>
                      <option value="project_scope">Project scope</option>
                    </select>
                  </label>
                )}
              </div>
            </section>
          ))}
          <button
            type="button"
            onClick={() =>
              setSlots([
                ...slots,
                {
                  id: crypto.randomUUID(),
                  view: "front",
                  framing: "full_body",
                  region: "whole",
                  poseId: "neutral",
                  expressionId: "neutral",
                  required: true,
                  status: "missing",
                  linkIds: [],
                },
              ])
            }
          >
            ＋ Add view or state
          </button>
          <label className="profile-rationale">
            Why this profile changes
            <textarea
              required
              minLength={10}
              value={rationale}
              onChange={(e) => setRationale(e.target.value)}
              placeholder="Do not remove difficult views merely to improve coverage."
            />
          </label>
          <button className="primary">Publish evaluation profile →</button>
        </form>
      </section>
    </div>
  );
}
