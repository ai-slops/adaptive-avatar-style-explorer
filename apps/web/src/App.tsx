import { useEffect, useState } from "react";
import { api, setCSRF } from "./api";
import type {
  Project,
  Design,
  Evidence,
  Preferences,
  Plan,
  Version,
} from "./types";
import { human, describe, image } from "./ui";
import { DesignEditor } from "./components/DesignEditor";
import { Compare } from "./components/Compare";
import { Inspect } from "./components/Inspect";
import { Prompts } from "./components/Prompts";
import { Handoff } from "./components/Handoff";
import { Account } from "./components/Account";
import { ReviewHistory } from "./components/ReviewHistory";
import { Reasoning } from "./components/Reasoning";
export function App() {
  const [ready, setReady] = useState(false),
    [needsLaunch, setNeedsLaunch] = useState(false);
  const [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false);
  const [projects, setProjects] = useState<Project[]>([]),
    [projectId, setProjectId] = useState("");
  const [designs, setDesigns] = useState<Design[]>([]),
    [evidence, setEvidence] = useState<Record<string, Evidence>>({});
  const [preferences, setPreferences] = useState<Preferences | null>(null),
    [plans, setPlans] = useState<Plan[]>([]);
  const [screen, setScreen] = useState("explore"),
    [selected, setSelected] = useState(""),
    [editor, setEditor] = useState<Version | null | false>(false);
  const [compareIds, setCompareIds] = useState<string[]>([]),
    [branch, setBranch] = useState("main");
  const [branches, setBranches] = useState<
    { branch_id: string; parent_sequence: number | null }[]
  >([]);
  const [codex, setCodex] = useState(false);
  const [rankingRegion, setRankingRegion] = useState("whole");
  const project = projects.find((p) => p.project_id === projectId);
  const allVersions = designs.flatMap((d) => d.versions);
  const version = allVersions.find((v) => v.version_id === selected);
  const title = (v: string) =>
    designs.find((d) => d.versions.some((x) => x.version_id === v))?.title ??
    "Design";
  const base = `/projects/${projectId}`;
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }
  async function refresh(p = projectId, branchId = branch) {
    const list = await api<Project[]>("/projects");
    setProjects(list);
    if (!p) return;
    const [ds, pref, packs, branchList] = await Promise.all([
      api<Design[]>(`/projects/${p}/designs?branchId=${branchId}`),
      api<Preferences>(`/projects/${p}/preferences?branchId=${branchId}`),
      api<Plan[]>(`/projects/${p}/prompt-packs`),
      api<{ branch_id: string; parent_sequence: number | null }[]>(
        `/projects/${p}/branches`,
      ),
    ]);
    setBranches(branchList);
    setDesigns(ds);
    setPreferences(pref);
    setPlans(packs);
    const es = await Promise.all(
      ds
        .flatMap((d) => d.versions)
        .map(
          async (v) =>
            [
              v.version_id,
              await api<Evidence>(
                `/projects/${p}/design-versions/${v.version_id}/evidence`,
              ),
            ] as const,
        ),
    );
    setEvidence(Object.fromEntries(es));
  }
  useEffect(() => {
    void run(async () => {
      const launch = new URLSearchParams(location.hash.slice(1)).get("launch");
      try {
        const session = launch
          ? await api<{ csrfToken: string; mode: string }>(
              "/session/bootstrap",
              {
                secret: launch,
              },
            )
          : await api<{ csrfToken: string; mode: string }>("/session");
        setCSRF(session.csrfToken);
        setCodex(session.mode === "codex_local");
        history.replaceState(null, "", location.pathname);
        setReady(true);
        const list = await api<Project[]>("/projects");
        setProjects(list);
        if (list[0]) setProjectId(list[0].project_id);
      } catch {
        setNeedsLaunch(true);
      }
    });
  }, []);
  useEffect(() => {
    if (ready && projectId) void run(() => refresh(projectId));
  }, [projectId, ready, branch]);
  async function feedback(
    action: string,
    v?: string,
    extra: Record<string, unknown> = {},
  ) {
    await api(base + "/feedback", {
      eventId: crypto.randomUUID(),
      branchId: branch,
      action,
      domain: "project",
      subjectVersionIds: v ? [v] : [],
      expectedEventSequence: project?.event_sequence,
      ...extra,
    });
    await refresh();
  }
  const current = designs
    .filter((d) => d.branch_id === branch || branch !== "main")
    .flatMap((d) => [
      d.versions[0],
      ...d.versions
        .slice(1)
        .filter((v) => preferences?.shortlist.includes(v.version_id)),
    ])
    .filter((v) => !preferences?.rejected.includes(v.version_id));

  const ranking = preferences?.rankings[rankingRegion];
  const boardOrder = [
    ...(ranking?.boardVersionIds ?? []),
    ...current.map((v) => v.version_id),
  ];
  const board = listUnique(boardOrder)
    .map((id) => current.find((v) => v.version_id === id))
    .filter((v): v is Version => !!v);
  if (!ready)
    return (
      <main className="launch">
        <div className="brandmark">f.</div>
        <p className="eyebrow">FORM & CHARACTER</p>
        <h1>
          A character worth
          <br />
          bringing to life.
        </h1>
        <p>
          {needsLaunch
            ? "Open the launch link printed by the local server to enter your private workspace."
            : "Opening your local workspace…"}
        </p>
        {error && <p role="alert">{error}</p>}
      </main>
    );
  return (
    <div className="app">
      <aside className="sidebar">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            setScreen("explore");
          }}
        >
          <span className="brandmark">f.</span>
          <span>
            form &<br />
            character
          </span>
        </a>
        <p className="sidebar-label">YOUR WORKSPACE</p>
        <label className="sr-only" htmlFor="project">
          Project
        </label>
        <select
          id="project"
          value={projectId}
          onChange={(e) => {
            setBranch("main");
            setProjectId(e.target.value);
            setSelected("");
            setCompareIds([]);
          }}
        >
          <option value="">Choose a project</option>
          {projects.map((p) => (
            <option key={p.project_id} value={p.project_id}>
              {p.title}
            </option>
          ))}
        </select>
        <button
          className="text-button"
          onClick={() => setScreen("new-project")}
        >
          ＋ New project
        </button>
        {project && (
          <label className="branch-picker">
            Design branch
            <select
              value={branch}
              onChange={(e) => {
                setBranch(e.target.value);
                setSelected("");
                setCompareIds([]);
              }}
            >
              {branches.map((b) => (
                <option value={b.branch_id} key={b.branch_id}>
                  {b.branch_id === "main"
                    ? "Main exploration"
                    : `Alternative · through ${b.parent_sequence}`}
                </option>
              ))}
            </select>
          </label>
        )}
        <nav aria-label="Workspace">
          {[
            ["explore", "01", "Explore designs"],
            ["compare", "02", "Compare"],
            ["inspect", "03", "Design & evidence"],
            ["prompts", "04", "Prompt workspace"],
            ["handoff", "05", "3D handoff"],
            ["account", "06", "Account & privacy"],
          ].map(([id, n, label]) => (
            <button
              key={id}
              className={screen === id ? "active" : ""}
              onClick={() => setScreen(id)}
            >
              <span>{n}</span>
              {label}
              {id === "compare" && compareIds.length > 0 && (
                <small>{compareIds.length}</small>
              )}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" /> Local private workspace
          <p>
            Selected images leave only with consent.
            <br />
            {codex
              ? "Codex generates images on request."
              : "Prompts are prepared as text."}
          </p>
          <button
            className="text-button"
            onClick={() =>
              void run(async () => {
                await api("/auth/sign-out", {});
                setReady(false);
                setNeedsLaunch(true);
              })
            }
          >
            Sign out locally
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            {project?.title || "Your next character"}{" "}
            <span className="muted">/ {human(screen)}</span>
          </span>
          <span className="pill">{codex ? "LOCAL CODEX" : "PROMPT ONLY"}</span>
        </header>
        <main>
          <div aria-live="polite">
            {error && (
              <div className="message error" role="alert">
                {error}
                <button aria-label="Dismiss error" onClick={() => setError("")}>
                  ×
                </button>
              </div>
            )}
            {notice && <div className="message">{notice}</div>}
            {busy && (
              <p className="working" role="status">
                Saving your workspace…
              </p>
            )}
          </div>
          {screen === "account" ? (
            <Account
              codex={codex}
              run={run}
              onSwitch={async () => {
                setProjectId("");
                setSelected("");
                setCompareIds([]);
                setDesigns([]);
                setEvidence({});
                setBranch("main");
                const list = await api<Project[]>("/projects");
                setProjects(list);
                if (list[0]) setProjectId(list[0].project_id);
              }}
            />
          ) : !project || screen === "new-project" ? (
            <section className="onboarding">
              <p className="eyebrow">A REUSABLE 3D AVATAR</p>
              <h1>Start with a possibility.</h1>
              <p>
                A name is enough to begin. Bring a reference, a rough idea, or
                an open mind.
              </p>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const data = new FormData(e.currentTarget);
                  void run(async () => {
                    const p = await api<Project>("/projects", {
                      title: data.get("title"),
                    });
                    setBranch("main");
                    setProjectId(p.project_id);
                    await refresh(p.project_id, "main");
                    setScreen("explore");
                  });
                }}
              >
                <label>
                  Project name
                  <input
                    name="title"
                    placeholder="My avatar exploration"
                    required
                    maxLength={120}
                  />
                </label>
                <button className="primary" disabled={busy}>
                  Create workspace ↗
                </button>
              </form>
            </section>
          ) : (
            <>
              {screen === "explore" && (
                <>
                  <div className="page-heading">
                    <div>
                      <p className="eyebrow">
                        DESIGN DISCOVERY /{" "}
                        {String(current.length).padStart(2, "0")} DIRECTIONS
                      </p>
                      <h1>Find your character.</h1>
                      <p>
                        Choose a design you want to use as a 3D avatar.
                        <br />
                        Every view is evidence. Every design stays its own
                        direction.
                      </p>
                    </div>
                    <button className="primary" onClick={() => setEditor(null)}>
                      ＋ Add a design
                    </button>
                  </div>
                  <div className="workspace-note">
                    <span>↗</span>
                    <div>
                      <strong>
                        From an idea to a character that holds together.
                      </strong>
                      <p>
                        Explore directions first. Then inspect profiles, missing
                        surfaces, and expressions before handing off to a model
                        maker.
                      </p>
                    </div>
                  </div>
                  <div className="ranking-controls">
                    <label>
                      Explore a design scope
                      <select
                        value={rankingRegion}
                        onChange={(e) => setRankingRegion(e.target.value)}
                      >
                        {Object.keys(
                          preferences?.rankings ?? { whole: null },
                        ).map((r) => (
                          <option key={r} value={r}>
                            {human(r)}
                          </option>
                        ))}
                      </select>
                    </label>
                    <p>
                      {ranking?.state === "ranked_on_common_basis"
                        ? `Ordered within a shared basis of ${ranking.basis.length} observed ${human(rankingRegion)} features. Other scopes stay separate.`
                        : "Not enough common visual evidence to rank this scope. Missing views are evidence requests."}
                    </p>
                  </div>
                  <div className="board-toolbar">
                    <span>
                      {current.length} distinct design
                      {current.length === 1 ? "" : "s"}{" "}
                      <span className="muted">· showing up to six</span>
                    </span>
                    <span className="muted">
                      {preferences?.shortlist.length || 0} on your shortlist
                    </span>
                  </div>
                  {current.length === 0 ? (
                    <div className="empty-state">
                      <span className="empty-orbit">＋</span>
                      <h2>Your first direction starts here.</h2>
                      <p>
                        Add a short character idea, then import a reference.
                        <br />
                        Text ideas remain proposals until you review them.
                      </p>
                      <button
                        className="primary"
                        onClick={() => setEditor(null)}
                      >
                        Add your first design ↗
                      </button>
                    </div>
                  ) : (
                    <div className="design-grid">
                      {board.slice(0, 6).map((v, i) => {
                        const ev = evidence[v.version_id],
                          preview =
                            ev?.links.find((l) => l.status === "compatible") ??
                            ev?.links[0],
                          shortlisted = preferences?.shortlist.includes(
                            v.version_id,
                          );
                        return (
                          <article className="design-card" key={v.version_id}>
                            <button
                              className="card-visual"
                              onClick={() => {
                                setSelected(v.version_id);
                                setScreen("inspect");
                              }}
                            >
                              {preview ? (
                                <img
                                  src={image(projectId, preview)}
                                  alt={`Imported depiction of ${title(v.version_id)}`}
                                />
                              ) : (
                                <div className="text-concept">
                                  <span>UNRENDERED IDEA</span>
                                  <p>{describe(v)}</p>
                                </div>
                              )}
                              <span className="card-number">
                                {String(i + 1).padStart(2, "0")}
                              </span>
                              <span className="version-tag">v{v.revision}</span>
                            </button>
                            <div className="card-content">
                              <div className="card-title">
                                <h2>{title(v.version_id)}</h2>
                                <button
                                  aria-label={
                                    shortlisted
                                      ? "Remove from shortlist"
                                      : "Add to shortlist"
                                  }
                                  aria-pressed={shortlisted}
                                  className={
                                    shortlisted ? "star selected" : "star"
                                  }
                                  onClick={() =>
                                    void run(() =>
                                      feedback(
                                        shortlisted
                                          ? "shortlist_remove"
                                          : "shortlist_add",
                                        v.version_id,
                                      ),
                                    )
                                  }
                                >
                                  {shortlisted ? "★" : "☆"}
                                </button>
                              </div>
                              <p className="clamped">{describe(v)}</p>
                              <div className="coverage-line">
                                <span>Reference coverage</span>
                                <strong>
                                  {ev?.referenceCoverage == null
                                    ? "Unconfigured"
                                    : `${Math.round(ev.referenceCoverage * 100)}%`}
                                </strong>
                              </div>
                              <progress
                                className="coverage-track"
                                max={1}
                                value={ev?.referenceCoverage ?? 0}
                                aria-label="Reference coverage"
                              />
                              <div className="card-bottom">
                                <span>
                                  {ev?.links.length || 0} depictions ·{" "}
                                  {ev?.findings.filter(
                                    (f) => f.state === "open",
                                  ).length || 0}{" "}
                                  issues
                                </span>
                                <button
                                  onClick={() => {
                                    setCompareIds((ids) =>
                                      ids.includes(v.version_id)
                                        ? ids.filter((x) => x !== v.version_id)
                                        : [...ids.slice(-1), v.version_id],
                                    );
                                  }}
                                  aria-pressed={compareIds.includes(
                                    v.version_id,
                                  )}
                                >
                                  {compareIds.includes(v.version_id)
                                    ? "✓ Selected"
                                    : "Compare ＋"}
                                </button>
                              </div>
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  )}
                  {compareIds.length === 2 && (
                    <div className="compare-dock">
                      <span>Two directions. One considered choice.</span>
                      <button
                        className="primary"
                        onClick={() => setScreen("compare")}
                      >
                        Compare designs →
                      </button>
                    </div>
                  )}
                  <section className="subtle-panel">
                    <h3>Your learning history</h3>
                    <p>
                      {preferences?.state === "insufficient_evidence"
                        ? "Not enough qualified visual evidence yet. Start with a scoped, matched comparison."
                        : Object.entries(preferences?.models ?? {})
                            .map(
                              ([r, m]) =>
                                `${human(r)}: ${m.effectiveWeight.toFixed(1)} effective comparison weight`,
                            )
                            .join(" · ")}
                    </p>
                    {preferences?.contextualDisagreements.map((d, i) => (
                      <p className="disagreement" key={i}>
                        {human(d.region)}: {d.message}
                      </p>
                    ))}
                    <div className="inline-actions">
                      <button
                        onClick={() =>
                          void run(async () => {
                            const result = await api<{ childBranchId: string }>(
                              base + "/feedback",
                              {
                                eventId: crypto.randomUUID(),
                                branchId: branch,
                                action: "fork_branch",
                                expectedEventSequence: project.event_sequence,
                              },
                            );
                            setBranch(result.childBranchId);
                            setNotice(
                              "Created an alternative branch with a frozen history boundary.",
                            );
                          })
                        }
                      >
                        Fork this direction
                      </button>
                      <button
                        onClick={() =>
                          void run(() =>
                            feedback("reset", undefined, {
                              preserveLocks: true,
                            }),
                          )
                        }
                      >
                        Reset learning, keep locks
                      </button>
                      {branch !== "main" && (
                        <button onClick={() => setBranch("main")}>
                          Return to main branch
                        </button>
                      )}
                    </div>
                  </section>
                  <ReviewHistory
                    project={project}
                    branch={branch}
                    run={run}
                    onUndo={async (id) => {
                      await feedback("undo", undefined, { targetEventId: id });
                    }}
                  />
                </>
              )}
              {screen === "compare" && (
                <Compare
                  versions={allVersions}
                  ids={compareIds}
                  setIds={setCompareIds}
                  evidence={evidence}
                  project={project}
                  title={title}
                  branch={branch}
                  run={run}
                  refresh={() => refresh()}
                  setNotice={setNotice}
                />
              )}
              {["inspect", "prompts", "handoff"].includes(screen) && (
                <>
                  <div className="page-heading">
                    <div>
                      <p className="eyebrow">
                        {screen === "inspect"
                          ? "CANONICAL DESIGN + OBSERVED EVIDENCE"
                          : screen === "prompts"
                            ? "PREPARE / EXPORT / IMPORT"
                            : "THE NEXT STEP IS A MODEL"}
                      </p>
                      <h1>
                        {screen === "inspect"
                          ? "Look beyond one image."
                          : screen === "prompts"
                            ? "Ask for the evidence you need."
                            : "A clear brief. An honest handoff."}
                      </h1>
                    </div>
                  </div>
                  <label className="version-selector">
                    Design version
                    <select
                      value={selected}
                      onChange={(e) => setSelected(e.target.value)}
                    >
                      <option value="">Choose a design version</option>
                      {designs.flatMap((d) =>
                        d.versions.map((v) => (
                          <option value={v.version_id} key={v.version_id}>
                            {d.title} · v{v.revision}
                          </option>
                        )),
                      )}
                    </select>
                  </label>
                  {version && evidence[selected] && (
                    <Reasoning
                      version={version}
                      evidence={evidence[selected]}
                      project={project}
                      run={run}
                    />
                  )}
                  {version && evidence[selected] ? (
                    screen === "inspect" ? (
                      <Inspect
                        version={version}
                        evidence={evidence[selected]}
                        project={project}
                        plans={plans}
                        preferences={preferences}
                        onEdit={() => setEditor(version)}
                        run={run}
                        refresh={() => refresh()}
                        feedback={feedback}
                      />
                    ) : screen === "prompts" ? (
                      <Prompts
                        version={version}
                        evidence={evidence[selected]}
                        project={project}
                        plans={plans}
                        codex={codex}
                        run={run}
                        refresh={() => refresh()}
                        notice={setNotice}
                        onImport={() => setScreen("inspect")}
                      />
                    ) : (
                      <Handoff
                        version={version}
                        evidence={evidence[selected]}
                        project={project}
                        run={run}
                        refresh={() => refresh()}
                        notice={setNotice}
                      />
                    )
                  ) : (
                    <div className="empty-state">
                      <h2>Choose a direction to continue.</h2>
                      <p>
                        Each version has its own specification and evidence
                        history.
                      </p>
                    </div>
                  )}
                </>
              )}
            </>
          )}
        </main>
        <footer>
          FORM & CHARACTER{" "}
          <span>A design discovery studio for reusable avatars.</span>
          <span>Concept evidence ≠ a validated 3D model</span>
        </footer>
      </div>
      {editor !== false && (
        <DesignEditor
          current={editor}
          onClose={() => setEditor(false)}
          onSave={async (title, spec, reason) => {
            await run(async () => {
              const inherited =
                editor &&
                designs.find((d) => d.design_id === editor.design_id)
                  ?.branch_id !== branch;
              const v = inherited
                ? await api<Version>(base + "/designs", {
                    title: `${designs.find((d) => d.design_id === editor.design_id)?.title ?? "Design"} · alternative`,
                    spec,
                    branchId: branch,
                    basedOnVersionId: editor.version_id,
                  })
                : editor
                  ? await api<Version>(
                      base + `/designs/${editor.design_id}/versions`,
                      {
                        parentVersionId: editor.version_id,
                        spec,
                        reason,
                        expectedEventSequence: project?.event_sequence,
                      },
                    )
                  : await api<Version>(base + "/designs", {
                      title,
                      spec,
                      branchId: branch,
                    });
              setSelected(v.version_id);
              await refresh();
              setEditor(false);
              setScreen("inspect");
            });
          }}
        />
      )}
    </div>
  );
}

function listUnique(values: string[]) {
  return [...new Set(values)];
}
