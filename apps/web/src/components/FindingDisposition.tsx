import { useState } from "react";
import { api } from "../api";
import { human } from "../ui";
import type { Project } from "../types";
export function FindingDisposition({
  finding,
  project,
  run,
  refresh,
}: {
  finding: {
    finding_id: string;
    kind: string;
    state: string;
    details_json: string;
  };
  project: Project;
  run: (f: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
}) {
  const [state, setState] = useState("resolved"),
    [rationale, setRationale] = useState("");
  return (
    <div className="finding">
      <span>
        {human(finding.kind)} · {human(finding.state)}
      </span>
      <p>{JSON.parse(finding.details_json).description}</p>
      {finding.state === "open" && (
        <details>
          <summary>Record a resolution or tradeoff</summary>
          <p>
            A tradeoff does not make an unfaithful depiction valid evidence.
            Review a corrected result or adopt a new design version.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run(async () => {
                await api(
                  `/projects/${project.project_id}/findings/${finding.finding_id}/disposition`,
                  {
                    state,
                    rationale,
                    expectedEventSequence: project.event_sequence,
                  },
                );
                await refresh();
              });
            }}
          >
            <div className="inline-inputs">
              <label>
                Disposition
                <select
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                >
                  {["resolved", "accepted_tradeoff", "dismissed"].map((s) => (
                    <option key={s} value={s}>
                      {human(s)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Reason
                <input
                  required
                  minLength={10}
                  value={rationale}
                  onChange={(e) => setRationale(e.target.value)}
                />
              </label>
            </div>
            <button>Record disposition</button>
          </form>
        </details>
      )}
    </div>
  );
}
