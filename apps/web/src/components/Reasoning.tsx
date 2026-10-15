import { useState, useEffect } from "react";
import type {
  SessionInfo,
  Job,
  Version,
  Evidence,
  Project,
  Link,
  Observation,
} from "../types";
import { human, image } from "../ui";
import { api } from "../api";
import { EvidenceEditor } from "./EvidenceEditor";
export function Reasoning({
  version,
  evidence,
  project,
  run,
}: {
  version: Version;
  evidence: Evidence;
  project: Project;
  run: (f: () => Promise<void>) => Promise<void>;
}) {
  const [session, setSession] = useState<SessionInfo | null>(null),
    [models, setModels] = useState<{ slug: string; display_name: string }[]>(
      [],
    ),
    [model, setModel] = useState(""),
    [task, setTask] = useState("describe_depictions"),
    [consent, setConsent] = useState(false),
    [selected, setSelected] = useState<string[]>([]),
    [jobs, setJobs] = useState<Job[]>([]),
    [budget, setBudget] = useState(1),
    [reviewSuggestion, setReviewSuggestion] = useState<{
      link: Link;
      observation: Observation;
    } | null>(null);
  const base = `/projects/${project.project_id}`;
  async function load() {
    const [s, c, j] = await Promise.all([
      api<SessionInfo>("/session"),
      api<{ allowImageAnalysis: boolean }>(base + "/image-analysis-consent"),
      api<SessionInfo>("/session").then((s) =>
        api<Job[]>(base + (s.mode === "codex_local" ? "/codex/jobs" : "/jobs")),
      ),
    ]);
    setSession(s);
    setConsent(c.allowImageAnalysis);
    setJobs(j);
  }
  useEffect(() => {
    setSelected([]);
    void run(load);
  }, [version.version_id]);
  const live = jobs.some((j) => ["queued", "running"].includes(j.state));
  useEffect(() => {
    if (!live) return;
    const timer = setInterval(() => {
      void load().catch(() => {});
    }, 1000);
    return () => clearInterval(timer);
  }, [live, version.version_id]);
  const native = session?.mode === "codex_local";
  const jobsPath = base + (native ? "/codex/jobs" : "/jobs");
  if (!native && !session?.registrationId) return null;
  return (
    <details className="paper-panel assistance">
      <summary>
        Optional {native ? "Codex" : "account"} analysis ·{" "}
        {native
          ? "one turn per action"
          : `${session?.remainingRequests} requests left`}{" "}
        {session?.usagePaused ? "· Usage paused" : ""}
      </summary>
      <p>
        Explicitly choose a bounded text/vision task. Results are suggestions
        for review; they never confirm intent or validate geometry.
      </p>
      <div className="inline-inputs">
        {!native && (
          <>
            <label>
              Session request budget
              <input
                type="number"
                min={0}
                max={20}
                value={budget}
                onChange={(e) => setBudget(Number(e.target.value))}
              />
            </label>
            <button
              onClick={() =>
                void run(async () => {
                  await api("/provider/budget", { requests: budget });
                  await load();
                })
              }
            >
              Set budget
            </button>
            <button
              onClick={() =>
                void run(async () => {
                  await api("/provider/budget", { requests: 0 });
                  await load();
                })
              }
            >
              Pause new requests
            </button>
          </>
        )}
        <button
          onClick={() =>
            void run(async () => {
              const catalog = await api<
                { slug: string; display_name: string }[]
              >(native ? "/codex/models" : "/provider/models");
              setModels(catalog);
              setModel(catalog[0]?.slug ?? "");
            })
          }
        >
          Load available models
        </button>
      </div>
      <div className="inline-inputs">
        <label>
          Admitted model
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="">Load your model catalog</option>
            {models.map((m) => (
              <option value={m.slug} key={m.slug}>
                {m.display_name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Analysis task
          <select value={task} onChange={(e) => setTask(e.target.value)}>
            {[
              "describe_depictions",
              "review_design_consistency",
              "propose_next_actions",
              "compile_prompt_pack",
              "summarize_preferences",
              "compile_design_handoff",
            ].map((t) => (
              <option value={t} key={t}>
                {human(t)}
              </option>
            ))}
          </select>
        </label>
      </div>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) =>
            void run(async () => {
              await api(base + "/image-analysis-consent", {
                allowImageAnalysis: e.target.checked,
              });
              await load();
            })
          }
        />
        I allow sending selected project images to OpenAI for analysis.
      </label>
      <div className="selected-images">
        {evidence.links.map((l) => (
          <label className="checkbox" key={l.link_id}>
            <input
              type="checkbox"
              disabled={!consent}
              checked={selected.includes(l.link_id)}
              onChange={(e) =>
                setSelected((ids) =>
                  e.target.checked
                    ? [...ids, l.link_id].slice(-4)
                    : ids.filter((id) => id !== l.link_id),
                )
              }
            />
            <img
              src={image(project.project_id, l)}
              alt="Selectable analysis reference"
            />
            {human(
              l.observations[0]?.observedPresentation.view ?? "unreviewed",
            )}
          </label>
        ))}
      </div>
      <button
        className="primary"
        disabled={
          !model ||
          (!native &&
            ((session?.remainingRequests ?? 0) < 1 || session?.usagePaused)) ||
          live
        }
        onClick={() =>
          void run(async () => {
            await api(native ? base + "/codex/analyze" : jobsPath, {
              ...(native
                ? {
                    authorizeOneTurn: true,
                    approveReferenceTransmission: consent,
                  }
                : {}),
              requestId: crypto.randomUUID(),
              task,
              versionId: version.version_id,
              model,
              depictionLinkIds: consent ? selected : [],
              expectedEventSequence: project.event_sequence,
            });
            await load();
          })
        }
      >
        Analyze selected evidence as text →
      </button>
      {jobs
        .filter(
          (j) =>
            j.versionId === version.version_id && j.task !== "generate_image",
        )
        .map((j) => (
          <div className="job" key={j.jobId}>
            <div className="section-heading">
              <strong>
                {human(j.task)} · {human(j.state)}
              </strong>
              {["queued", "running"].includes(j.state) && (
                <button
                  onClick={() =>
                    void run(async () => {
                      await api(jobsPath + `/${j.jobId}/cancel`, {});
                      await load();
                    })
                  }
                >
                  Cancel local request
                </button>
              )}
            </div>
            {j.result?.suggestions && (
              <>
                <p>{j.result.suggestions.summary}</p>
                {j.result.suggestions.findings.map((f, i) => (
                  <p key={i}>
                    Suggested finding: {human(f.finding.kind)} —{" "}
                    {f.finding.description}
                  </p>
                ))}
                {j.result.suggestions.observations.map((o, i) => (
                  <div key={i}>
                    <p>
                      Proposed {human(o.observation.region)} observation:{" "}
                      {Object.entries(o.observation.attributes)
                        .map(
                          ([k, a]) =>
                            `${human(k)}: ${String(a.value ?? "unknown")} (${a.visibility})`,
                        )
                        .join(" · ")}
                    </p>
                    <button
                      disabled={
                        j.state !== "succeeded" ||
                        !evidence.links.some((l) => l.link_id === o.linkId)
                      }
                      onClick={() => {
                        const link = evidence.links.find(
                          (l) => l.link_id === o.linkId,
                        );
                        if (link)
                          setReviewSuggestion({
                            link,
                            observation: o.observation,
                          });
                      }}
                    >
                      Review suggestion against image
                    </button>
                  </div>
                ))}
                {j.result.suggestions.nextActions.map((a, i) => (
                  <p key={i}>
                    {human(a.kind)}: {a.reason}
                  </p>
                ))}
                <p className="muted">
                  {j.result.suggestions.observations.length} proposed
                  observations. Review against the imported images before
                  adopting features. This result is{" "}
                  {j.state === "stale" ? "historical and stale" : "unconfirmed"}
                  .
                </p>
              </>
            )}
            {j.result?.error && <p>{j.result.error}</p>}
            {j.result?.message && <p>{j.result.message}</p>}
          </div>
        ))}
      {reviewSuggestion && (
        <EvidenceEditor
          link={reviewSuggestion.link}
          project={project}
          suggestion={reviewSuggestion.observation}
          onClose={() => setReviewSuggestion(null)}
          onSave={async (data) => {
            await run(async () => {
              await api(base + "/evidence-reviews", data);
              setReviewSuggestion(null);
              location.reload();
            });
          }}
        />
      )}
    </details>
  );
}
