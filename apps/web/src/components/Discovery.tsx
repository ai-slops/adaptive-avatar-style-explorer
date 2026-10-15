import { useEffect, useRef, useState } from "react";
import { api, download } from "../api";
import type { Project } from "../types";
import { assetURL, parts, reactionNames } from "../discovery";
import type {
  Batch,
  Candidate,
  DiscoveryState,
  Part,
  Round,
} from "../discovery";

function Dialog({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const close = useRef(onClose);
  close.current = onClose;
  useEffect(() => {
    const origin = document.activeElement as HTMLElement | null;
    ref.current?.showModal();
    return () => {
      ref.current?.close();
      origin?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`discovery-dialog ${wide ? "wide" : ""}`}
      aria-label={title}
      onCancel={(e) => {
        e.preventDefault();
        close.current();
      }}
    >
      <div className="dialog-heading">
        <h2>{title}</h2>
        <button onClick={onClose} aria-label="닫기">
          닫기 ×
        </button>
      </div>
      {children}
    </dialog>
  );
}

type ImportRow = { assetId: string; filename: string; target: string };
type Generation = { round: Round; ids: string[] };

export function Discovery({
  project,
  codex,
  onCreated,
  onAdvanced,
  onSettings,
}: {
  project?: Project;
  codex: boolean;
  onCreated: (p: Project) => void;
  onAdvanced: (version?: string) => void;
  onSettings: () => void;
}) {
  const pid = project?.project_id ?? "";
  const base = `/projects/${pid}/discovery`;
  const [state, setState] = useState<DiscoveryState | null>(null);
  const [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const working = useRef(false);
  const readVersion = useRef(0);
  const [name, setName] = useState(""),
    [brief, setBrief] = useState("");
  const [connection, setConnection] = useState<string>(
    codex ? "접속 확인 중" : "외부 생성 후 가져오기",
  );
  const [loadedLinks, setLoadedLinks] = useState<Record<string, string>>({});
  const [compare, setCompare] = useState<string[]>([]),
    [focused, setFocused] = useState(false);
  const [enlarge, setEnlarge] = useState<{
    assetId: string;
    label: string;
  } | null>(null);
  const [generation, setGeneration] = useState<Generation | null>(null);
  const [consent, setConsent] = useState(false),
    [exportPermission, setExportPermission] = useState(false);
  const [model, setModel] = useState(""),
    [catalog, setCatalog] = useState<
      { slug: string; display_name: string; isDefault?: boolean }[]
    >([]);
  const [imports, setImports] = useState<ImportRow[] | null>(null),
    [importRound, setImportRound] = useState<Round | null>(null);
  const [importProject, setImportProject] = useState("");
  const [startReferences, setStartReferences] = useState(false);
  const [refine, setRefine] = useState<Candidate | null>(null),
    [part, setPart] = useState<Part>("hair"),
    [preserve, setPreserve] = useState<Part | "">("");
  const [problem, setProblem] = useState<Candidate | null>(null);
  const [replace, setReplace] = useState<Candidate | null>(null);
  const [choiceOpen, setChoiceOpen] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [directionName, setDirectionName] = useState<{
    candidate: Candidate;
    name: string;
  } | null>(null);
  const referenceInput = useRef<HTMLInputElement>(null),
    resultInput = useRef<HTMLInputElement>(null);
  const uploadRequest = useRef(crypto.randomUUID());
  const createdProject = useRef<Project | null>(null);
  const round = state?.rounds.find((r) => r.roundId === state.activeRoundId);
  const allCandidates = state?.rounds.flatMap((r) => r.candidates) ?? [];
  const activeBatch = state?.batches.find((b) =>
    ["queued", "running"].includes(b.state),
  );
  const currentBatches =
    state?.batches.filter((b) => b.roundId === round?.roundId) ?? [];
  const visible = focused
    ? compare
        .map((id) => allCandidates.find((c) => c.candidateId === id))
        .filter((c): c is Candidate => !!c)
    : (round?.candidates ?? []);
  const selectedDirections = new Set(
    state?.directions.map((d) => d.candidate.candidateId),
  );
  const references = generation
    ? Array.from(
        new Map(
          generation.round.candidates
            .filter((c) => generation.ids.includes(c.candidateId))
            .flatMap((c) => c.referenceImages)
            .map((i) => [i.assetId, i]),
        ).values(),
      )
    : [];

  async function load() {
    if (!pid) return;
    const version = ++readVersion.current;
    const next = await api<DiscoveryState>(base);
    if (version === readVersion.current) setState(next);
  }
  async function run(action: () => Promise<void>) {
    if (working.current) return;
    working.current = true;
    ++readVersion.current;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await action();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      working.current = false;
      setBusy(false);
    }
  }
  useEffect(() => {
    if (pid) void run(load);
  }, [pid]);
  useEffect(() => {
    if (!codex) return;
    let live = true;
    void api<{ connected: boolean }>("/codex/status")
      .then((s) => {
        if (live)
          setConnection(s.connected ? "Codex 연결됨" : "Codex 로그인 필요");
      })
      .catch(() => {
        if (live) setConnection("Codex 연결 확인 필요");
      });
    return () => {
      live = false;
    };
  }, [codex]);
  useEffect(() => {
    if (!pid || !activeBatch) return;
    let live = true;
    const timer = window.setInterval(() => {
      if (working.current) return;
      const version = ++readVersion.current;
      void api<DiscoveryState>(base)
        .then((s) => {
          if (live && !working.current && version === readVersion.current)
            setState(s);
        })
        .catch(() => {
          if (live)
            setError(
              "진행 상태를 확인하지 못했습니다. 저장된 결과는 유지됩니다. 상태를 다시 불러와 주세요.",
            );
        });
    }, 1500);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [pid, activeBatch?.batchId]);

  async function ensureProject() {
    if (project) return project;
    if (createdProject.current) return createdProject.current;
    const created = await api<Project>("/projects", {
      title: name.trim() || "나의 아바타 탐색",
    });
    createdProject.current = created;
    return created;
  }
  async function begin() {
    const p = await ensureProject();
    await api(`/projects/${p.project_id}/discovery/rounds`, {
      requestId: crypto.randomUUID(),
      expectedRevision: state?.revision ?? 0,
      brief,
    });
    if (!project) onCreated(p);
    else await load();
  }
  async function prepare(extra: Record<string, unknown> = {}) {
    if (!state) return;
    await api(base + "/rounds", {
      requestId: crypto.randomUUID(),
      expectedRevision: state.revision,
      ...extra,
    });
    setFocused(false);
    setCompare([]);
    setRefine(null);
    setProblem(null);
    setCopied(null);
    await load();
  }
  async function react(
    action: string,
    candidates: Candidate[] = [],
    extra: Record<string, unknown> = {},
  ) {
    if (!state) return;
    await api(base + "/reactions", {
      requestId: crypto.randomUUID(),
      expectedRevision: state.revision,
      action,
      candidateIds: candidates.map((c) => c.candidateId),
      linkIds: candidates.map((c) => c.image!.linkId),
      ...extra,
    });
    setNotice(
      `${reactionNames[action] ?? "선택 되돌리기"} 저장됨. 이미지는 그대로 두고 다음 제안에 반영합니다.`,
    );
    await load();
  }
  function showGeneration(r: Round) {
    setConsent(false);
    setExportPermission(false);
    setModel("");
    setCatalog([]);
    setGeneration({
      round: r,
      ids: r.candidates.filter((c) => !c.image).map((c) => c.candidateId),
    });
  }
  async function generate() {
    if (!generation) return;
    const data = {
      requestId: crypto.randomUUID(),
      candidateIds: generation.ids,
      authorizeTurns: generation.ids.length,
      approveReferenceTransmission: consent,
      exportPermission,
      ...(model ? { model } : {}),
    };
    await api(base + `/rounds/${generation.round.roundId}/generate`, data);
    setGeneration(null);
    await load();
  }
  async function upload(files: FileList | null, reference: boolean) {
    if (!files?.length) return;
    const list = Array.from(files);
    if (list.length > 12)
      throw new Error("한 번에 최대 12장까지 가져올 수 있습니다.");
    const p = await ensureProject();
    const rows: ImportRow[] = [];
    // Keep uploaded local assets reusable if the matching step is deferred.
    for (const file of list) {
      const asset = await api<{ assetId: string }>(
        `/projects/${p.project_id}/assets`,
        file,
      );
      const match =
        !reference &&
        round?.candidates.find(
          (c) =>
            c.returnName.replace(/\.[^.]+$/, "") ===
            file.name.replace(/\.[^.]+$/, ""),
        );
      rows.push({
        assetId: asset.assetId,
        filename: file.name,
        target: reference ? "reference" : match ? match.candidateId : "",
      });
    }
    setImportProject(p.project_id);
    setImportRound(reference ? null : (round ?? null));
    setStartReferences(reference && !state?.rounds.length);
    setImports(rows);
    uploadRequest.current = crypto.randomUUID();
    setExportPermission(false);
  }
  async function finishImport() {
    if (!imports) return;
    const result = await api<{ inspirationId?: string }[]>(
      `/projects/${importProject}/discovery/imports`,
      {
        requestId: uploadRequest.current,
        ...(importRound ? { roundId: importRound.roundId } : {}),
        items: imports.map((i) => ({
          assetId: i.assetId,
          filename: i.filename,
          ...(i.target === "reference"
            ? { independentReference: true }
            : { candidateId: i.target }),
          exportPermission,
        })),
      },
    );
    if (startReferences) {
      const current = await api<DiscoveryState>(
        `/projects/${importProject}/discovery`,
      );
      await api(`/projects/${importProject}/discovery/references`, {
        requestId: uploadRequest.current + ":start",
        expectedRevision: current.revision,
        inspirationIds: result.flatMap((r) =>
          r.inspirationId ? [r.inspirationId] : [],
        ),
      });
    }
    setImports(null);
    setNotice(
      "이미지를 가져왔습니다. 아직 원래 의도와 일치한다고 검토한 것은 아닙니다.",
    );
    if (!project && createdProject.current) onCreated(createdProject.current);
    else await load();
  }
  async function copyRound(r: Round) {
    const text = r.candidates
      .filter((c) => c.prompt)
      .map(
        (c) =>
          `${c.label}\n${c.purpose}\n\n${c.prompt!.promptText}\n\n저장할 파일 이름: ${c.returnName}`,
      )
      .join("\n\n---\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setNotice(
        "묶음 프롬프트를 복사했습니다. 외부 도구에서 각각 생성한 뒤 원래 파일 이름으로 가져와 주세요.",
      );
    } catch {
      setCopied(text);
    }
  }
  function choose(c: Candidate) {
    if (state?.selection && state.selection.versionId !== c.versionId)
      setReplace(c);
    else
      void run(async () => {
        await react("use_design", [c]);
        setChoiceOpen(true);
      });
  }
  async function revisit(c: Candidate) {
    await api(base + "/active-round", { roundId: c.roundId });
    setFocused(false);
    setCompare([]);
    await load();
  }

  function visual(c: Candidate, prefix = "") {
    return c.image ? (
      <button
        className="discovery-visual"
        onClick={() =>
          setEnlarge({ assetId: c.image!.assetId, label: c.label })
        }
        aria-label={`${prefix}${c.label} 크게 보기`}
      >
        <img
          key={c.image.linkId}
          src={assetURL(pid, c.image.assetId)}
          alt={`${c.label}의 참고 이미지`}
          onLoad={() =>
            setLoadedLinks((loaded) =>
              loaded[c.candidateId] === c.image!.linkId
                ? loaded
                : { ...loaded, [c.candidateId]: c.image!.linkId },
            )
          }
        />
        <span>크게 보기 ↗</span>
      </button>
    ) : (
      <div className="discovery-pending">
        <span>
          {c.job?.state === "running"
            ? "이미지 생성 중"
            : c.error
              ? "이번 요청에서 이미지를 얻지 못했습니다"
              : codex
                ? "생성할 후보 제안"
                : "외부에서 만들 이미지"}
        </span>
        <p>
          {c.preserveParts.length
            ? `${c.preserveParts.map((p) => parts[p]).join(", ")} 보존 · `
            : ""}
          {c.varyPart && c.varyPart !== "whole"
            ? `${parts[c.varyPart]} 대안`
            : c.label}
        </p>
        <small>실제 이미지가 도착하면 반응할 수 있습니다.</small>
      </div>
    );
  }
  function card(c: Candidate, index: number) {
    const saved = selectedDirections.has(c.candidateId);
    const imageReady =
      !!c.image && loadedLinks[c.candidateId] === c.image.linkId;
    return (
      <article
        key={c.candidateId}
        className={`discovery-card ${saved ? "saved" : ""}`}
        data-candidate={c.candidateId}
      >
        <div className="discovery-card-heading">
          <span>
            {focused
              ? index === 0
                ? "A"
                : "B"
              : String(c.position + 1).padStart(2, "0")}
          </span>
          <h2>{c.label}</h2>
        </div>
        {visual(c)}
        <div className="discovery-card-body">
          <p className="discovery-kind">
            {c.kind === "observation"
              ? "같은 디자인 · 다른 모습 확인"
              : c.kind === "correction"
                ? "같은 디자인 · 이미지 수정"
                : "디자인 방향"}
            {c.preserveParts.length > 0
              ? ` · ${c.preserveParts.map((p) => parts[p]).join(", ")} 보존`
              : ""}
            {c.image?.status === "unreviewed" ? " · 미검토 이미지" : ""}
          </p>
          {c.image ? (
            <>
              <div className="discovery-reactions">
                <button
                  disabled={busy || !imageReady}
                  aria-pressed={saved}
                  onClick={() =>
                    void run(() =>
                      react(saved ? "release_direction" : "interest", [c]),
                    )
                  }
                >
                  {saved ? "✓ 저장한 방향" : "이런 방향 더 보기"}
                </button>
                <button
                  disabled={busy || !imageReady}
                  onClick={() => choose(c)}
                >
                  이 디자인 사용
                </button>
              </div>
              <div className="discovery-card-tools">
                <button
                  aria-pressed={compare.includes(c.candidateId)}
                  onClick={() =>
                    setCompare((ids) =>
                      ids.includes(c.candidateId)
                        ? ids.filter((id) => id !== c.candidateId)
                        : [...ids.slice(-1), c.candidateId],
                    )
                  }
                >
                  {compare.includes(c.candidateId)
                    ? "✓ 비교에 담음"
                    : "비교에 담기"}
                </button>
                <details>
                  <summary>부분·다른 모습</summary>
                  <div className="discovery-menu">
                    <button
                      onClick={() => {
                        setRefine(c);
                        setPart("hair");
                        setPreserve("");
                      }}
                    >
                      부분을 보존하거나 바꾸기
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void run(() =>
                          prepare({
                            candidateId: c.candidateId,
                            intent: "continue",
                            count: 3,
                          }),
                        )
                      }
                    >
                      이 방향에서 새 대안
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void run(() =>
                          prepare({
                            candidateId: c.candidateId,
                            intent: "observe",
                            view: "character_left_profile",
                          }),
                        )
                      }
                    >
                      같은 디자인 옆모습 확인
                    </button>
                    <button
                      disabled={busy}
                      onClick={() =>
                        void run(() =>
                          prepare({
                            candidateId: c.candidateId,
                            intent: "observe",
                            view: "back",
                          }),
                        )
                      }
                    >
                      같은 디자인 뒷모습 확인
                    </button>
                    <button onClick={() => setProblem(c)}>
                      이미지가 틀리거나 판단하기 어려움
                    </button>
                    <button
                      disabled={busy}
                      onClick={() => void run(() => react("skip", [c]))}
                    >
                      지금은 판단 보류
                    </button>
                    <button onClick={() => onAdvanced(c.versionId)}>
                      세부 설계·근거 검토
                    </button>
                  </div>
                </details>
              </div>
              {state?.wrongLinks.includes(c.image.linkId) && (
                <p className="discovery-note">
                  이미지 문제로 표시됨 · 디자인을 거절한 반응은 아닙니다.
                </p>
              )}
              {state?.rejected.includes(c.candidateId) && (
                <p className="discovery-note">
                  다른 방향을 요청한 후보 · 기록에서 되돌릴 수 있습니다.
                </p>
              )}
            </>
          ) : (
            <details>
              <summary>무엇을 만들까요?</summary>
              <p>{c.purpose}</p>
              {c.prompt && (
                <details>
                  <summary>생성 프롬프트 (영문)</summary>
                  <pre className="discovery-prompt">{c.prompt.promptText}</pre>
                </details>
              )}
            </details>
          )}
          {c.error && (
            <details>
              <summary>요청 중단 사유</summary>
              <p>{c.error}</p>
              <button onClick={onSettings}>연결·사용량 설정</button>
            </details>
          )}
        </div>
      </article>
    );
  }

  if (!project || (state && !state.rounds.length))
    return (
      <section className="discovery discovery-start">
        <p className="eyebrow">나에게 맞는 아바타 찾기</p>
        <h1>
          아직 몰라도 괜찮아요.
          <br />
          보면서 골라 보세요.
        </h1>
        <p>
          서로 다른 캐릭터를 보고, 마음에 드는 방향을 남기면 다음 후보를
          준비합니다.
        </p>
        <details>
          <summary>이름이나 떠오르는 생각이 있나요? 선택 사항</summary>
          <label>
            탐색 이름
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={120}
            />
          </label>
          <label>
            짧은 설명
            <textarea
              value={brief}
              onChange={(e) => setBrief(e.target.value)}
              maxLength={2000}
              placeholder="예: 따뜻한 분위기의 여행자. 비워 두어도 됩니다."
            />
          </label>
        </details>
        <div className="discovery-start-actions">
          <button
            className="primary"
            disabled={busy}
            onClick={() => void run(begin)}
          >
            다양한 방향 탐색하기 ↗
          </button>
          <button
            disabled={busy}
            onClick={() => referenceInput.current?.click()}
          >
            참고 이미지로 시작하기
          </button>
        </div>
        <input
          ref={referenceInput}
          className="sr-only"
          tabIndex={-1}
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          aria-label="시작할 참고 이미지"
          onChange={(e) => {
            const files = e.target.files;
            void run(() => upload(files, true));
            e.target.value = "";
          }}
        />
        <p className="discovery-note">
          {codex
            ? "후보 4개를 먼저 제안합니다. 이미지 생성은 다음 화면에서 횟수를 확인하고 요청합니다."
            : "후보 4개의 프롬프트를 준비합니다. 외부 도구에서 생성한 이미지를 한 번에 가져올 수 있습니다."}
        </p>
        {busy && <p role="status">출발점을 준비하고 있습니다…</p>}
        {error && (
          <div role="alert" className="message error">
            {error}
          </div>
        )}
        {state?.library.some((l) => l.image) && (
          <section className="discovery-library">
            <h2>이전에 만든 이미지에서 이어가기</h2>
            <div className="discovery-library-grid">
              {state.library
                .filter((l) => l.image)
                .map((l) => (
                  <button
                    disabled={busy}
                    key={l.versionId}
                    onClick={() =>
                      void run(async () => {
                        await api(base + "/library", {
                          requestId: crypto.randomUUID(),
                          expectedRevision: state.revision,
                          versionId: l.versionId,
                        });
                        await load();
                      })
                    }
                  >
                    <img src={assetURL(pid, l.image!.assetId)} alt="" />
                    <span>{l.label}</span>
                  </button>
                ))}
            </div>
          </section>
        )}
        <details>
          <summary>직접 설계하거나 기존 도구 사용</summary>
          <button
            disabled={busy}
            onClick={() =>
              void run(async () => {
                const p = await ensureProject();
                if (!project) onCreated(p);
                onAdvanced();
              })
            }
          >
            고급 작업 도구 열기
          </button>
        </details>
        {renderImports()}
      </section>
    );

  function renderImports() {
    return (
      imports && (
        <Dialog title="이미지 가져오기" wide onClose={() => setImports(null)}>
          <p>
            이 단계는 기기에 이미지를 저장합니다. Codex나 다른 서비스로 전송하지
            않습니다.
          </p>
          <div className="discovery-import-list">
            {imports.map((item, i) => (
              <fieldset key={item.assetId + i} className="discovery-import-row">
                <legend>{item.filename}</legend>
                <img
                  src={assetURL(importProject, item.assetId)}
                  alt={`${item.filename} 미리 보기`}
                />
                <div>
                  <p>어느 후보의 결과인가요?</p>
                  <div className="discovery-match-options">
                    {(importRound?.candidates ?? []).map((c) => (
                      <label key={c.candidateId} className="discovery-match">
                        <input
                          type="radio"
                          name={`match-${i}`}
                          checked={item.target === c.candidateId}
                          onChange={() =>
                            setImports((rows) =>
                              rows!.map((r, n) =>
                                n === i ? { ...r, target: c.candidateId } : r,
                              ),
                            )
                          }
                        />
                        {c.image || c.referenceImages[0] ? (
                          <img
                            src={assetURL(
                              importProject,
                              (c.image ?? c.referenceImages[0]).assetId,
                            )}
                            alt={
                              c.image
                                ? "현재 결과 이미지"
                                : "출발점 참고 이미지 · 새 결과 아님"
                            }
                          />
                        ) : (
                          <span className="match-number">{c.position + 1}</span>
                        )}
                        <span>{c.label}</span>
                      </label>
                    ))}
                    <label className="discovery-match">
                      <input
                        type="radio"
                        name={`match-${i}`}
                        checked={item.target === "reference"}
                        onChange={() =>
                          setImports((rows) =>
                            rows!.map((r, n) =>
                              n === i ? { ...r, target: "reference" } : r,
                            ),
                          )
                        }
                      />
                      <span>잘 모르겠음 · 독립 참고자료</span>
                    </label>
                  </div>
                  {!item.target && (
                    <p className="discovery-note">
                      파일 이름만으로 대상을 알 수 없습니다. 위에서 선택해
                      주세요.
                    </p>
                  )}
                </div>
              </fieldset>
            ))}
          </div>
          <label className="check">
            <input
              type="checkbox"
              checked={exportPermission}
              onChange={(e) => setExportPermission(e.target.checked)}
            />
            이 이미지들을 이후 파일 묶음으로 내보내도 됩니다. 선택 사항
          </label>
          <button
            className="primary"
            disabled={busy || imports.some((i) => !i.target)}
            onClick={() => void run(finishImport)}
          >
            {startReferences
              ? "각 참고자료에서 탐색 시작"
              : `${imports.length}장 가져오기`}
          </button>
          {error && <p role="alert">{error}</p>}
        </Dialog>
      )
    );
  }

  return (
    <section className="discovery" aria-label="캐릭터 탐색">
      <div className="discovery-heading">
        <div>
          <p className="eyebrow">아바타 디자인 탐색</p>
          <h1>어떤 캐릭터를 쓰고 싶나요?</h1>
        </div>
        <button className="text-button" onClick={onSettings}>
          {connection} · 설정
        </button>
      </div>
      <div aria-live="polite">
        {error && (
          <div className="message error" role="alert">
            <span>{error}</span>
            <button onClick={() => void run(load)}>상태 다시 불러오기</button>
            <button onClick={onSettings}>연결·사용량 설정</button>
          </div>
        )}
        {notice && (
          <div className="discovery-notice">
            {notice}
            {state?.history[0] && (
              <button
                disabled={busy}
                onClick={() =>
                  void run(() =>
                    react("undo", [], {
                      targetReactionId: state.history[0].reactionId,
                    }),
                  )
                }
              >
                마지막 선택 되돌리기
              </button>
            )}
          </div>
        )}
        {busy && (
          <span className="sr-only" role="status">
            저장 중
          </span>
        )}
      </div>
      {state?.selection && (
        <div className="discovery-choice">
          <span>✓ 선택한 디자인: {state.selection.label}</span>
          <button onClick={() => setChoiceOpen(true)}>선택 기록 보기</button>
          <span>계속 탐색해도 이 선택은 유지됩니다.</span>
        </div>
      )}
      {!!state?.directions.length && (
        <section className="discovery-directions" aria-label="저장한 방향">
          <h2>{state.directions.length}개 방향 저장됨</h2>
          <div>
            {state.directions.map((d) => (
              <article key={d.directionId}>
                {d.candidate.image && (
                  <button
                    className="direction-thumb"
                    aria-label={`${d.label} 다시 보기`}
                    onClick={() => void run(() => revisit(d.candidate))}
                  >
                    <img
                      src={assetURL(pid, d.candidate.image.assetId)}
                      alt=""
                    />
                  </button>
                )}
                <div>
                  <strong>{d.label}</strong>
                  <p>
                    {Object.keys(d.preserved).length
                      ? `${Object.keys(d.preserved)
                          .map((p) => parts[p as Part])
                          .join(", ")} 보존`
                      : "부분을 고정하지 않은 탐색 방향"}
                  </p>
                  <div className="inline-actions">
                    <button
                      disabled={busy}
                      onClick={() =>
                        void run(() =>
                          prepare({
                            candidateId: d.candidate.candidateId,
                            intent: "continue",
                            count: 3,
                          }),
                        )
                      }
                    >
                      이 방향 발전
                    </button>
                    <button
                      onClick={() =>
                        setDirectionName({
                          candidate: d.candidate,
                          name: d.label,
                        })
                      }
                    >
                      이름 바꾸기
                    </button>
                    <button
                      onClick={() =>
                        setCompare((ids) =>
                          ids.includes(d.candidate.candidateId)
                            ? ids.filter((id) => id !== d.candidate.candidateId)
                            : [...ids.slice(-1), d.candidate.candidateId],
                        )
                      }
                    >
                      비교에 담기
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}
      <div className="discovery-round-bar">
        <div>
          <strong>
            {focused
              ? "두 방향 비교"
              : round
                ? `${round.ordinal}번째 후보 묶음`
                : "후보 불러오는 중"}
          </strong>
          <p>{round?.explanation}</p>
          {round?.historicalFeedback && (
            <small>
              이 묶음은 현재 선택이 바뀌기 전에 준비했습니다. 새 요청에는 최신
              선택을 반영합니다.
            </small>
          )}
        </div>
        {focused && (
          <button onClick={() => setFocused(false)}>
            후보 묶음으로 돌아가기
          </button>
        )}
        {compare.length === 2 && !focused && (
          <button className="primary" onClick={() => setFocused(true)}>
            담은 두 후보 비교
          </button>
        )}
        <details className="discovery-round-history">
          <summary>이전 묶음</summary>
          {state?.rounds.map((r) => (
            <button
              disabled={busy}
              key={r.roundId}
              aria-pressed={r.roundId === round?.roundId}
              onClick={(event) => {
                const details = event.currentTarget.closest("details");
                if (details) details.open = false;
                void run(async () => {
                  await api(base + "/active-round", { roundId: r.roundId });
                  setFocused(false);
                  setCompare([]);
                  await load();
                });
              }}
            >
              {r.ordinal}번째 · {r.candidates.filter((c) => c.image).length}/
              {r.candidates.length}개 이미지
            </button>
          ))}
        </details>
      </div>
      {round?.error && (
        <div role="alert" className="message error">
          {round.error}
          <button
            disabled={busy}
            onClick={() => void run(() => prepare({ intent: "different" }))}
          >
            새로운 방향 준비
          </button>
        </div>
      )}
      <div
        className={`discovery-board count-${visible.length} ${focused ? "focused" : ""}`}
      >
        {visible.map(card)}
      </div>
      {focused && visible.length === 2 && visible.every((c) => c.image) && (
        <section className="discovery-compare-reactions" aria-label="비교 반응">
          <h2>어느 캐릭터를 더 쓰고 싶나요?</h2>
          <p>
            지금 보이는 이미지에 대한 탐색 반응입니다. 모든 부분이나 보이지 않는
            모습을 확정하지 않습니다.
          </p>
          <div>
            {[
              ["choose_a", "A가 더 좋아요"],
              ["choose_b", "B가 더 좋아요"],
              ["both", "둘 다 더 탐색"],
              ["no_preference", "선호 차이 없음"],
              ["neither", "둘 다 마음에 안 들어요"],
              ["skip", "판단 보류"],
            ].map(([action, label]) => (
              <button
                key={action}
                disabled={
                  busy ||
                  visible.some(
                    (c) =>
                      !c.image || loadedLinks[c.candidateId] !== c.image.linkId,
                  )
                }
                onClick={() => void run(() => react(action, visible))}
              >
                {label}
              </button>
            ))}
          </div>
        </section>
      )}
      <section className="discovery-next" aria-label="다음 탐색">
        <div>
          <h2>다음에는 무엇을 볼까요?</h2>
          <p>{state?.nextStep}</p>
        </div>
        <div className="discovery-next-actions">
          {round &&
            round.candidates.some((c) => !c.image) &&
            (codex ? (
              <button
                className="primary"
                disabled={busy || !!activeBatch}
                onClick={() => showGeneration(round)}
              >
                {round.candidates.some((c) => c.image || c.error)
                  ? "남은 후보 생성·재시도"
                  : "제안한 후보 생성"}
              </button>
            ) : (
              <>
                <button
                  className="primary"
                  disabled={busy}
                  onClick={() => void run(() => copyRound(round))}
                >
                  묶음 프롬프트 복사
                </button>
                <button
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      download(
                        base + `/rounds/${round.roundId}/export`,
                        {},
                        "discovery-prompts.zip",
                      ),
                    )
                  }
                >
                  파일 묶음 내보내기
                </button>
              </>
            ))}
          {round?.candidates.some((c) => c.image) && (
            <button
              className="primary"
              disabled={busy || !!activeBatch}
              onClick={() => void run(() => prepare())}
            >
              {codex ? "다음 후보 생성 준비" : "다음 프롬프트 준비"}
            </button>
          )}
          <button
            disabled={busy}
            onClick={() => void run(() => prepare({ intent: "different" }))}
          >
            다른 방향 탐색
          </button>
          {visible.some(
            (c) => c.image && loadedLinks[c.candidateId] === c.image.linkId,
          ) && (
            <button
              disabled={busy}
              onClick={() =>
                void run(() =>
                  react(
                    "neither",
                    visible.filter(
                      (c) =>
                        c.image &&
                        loadedLinks[c.candidateId] === c.image.linkId,
                    ),
                  ),
                )
              }
            >
              마음에 드는 후보 없음
            </button>
          )}
          <button disabled={busy} onClick={() => resultInput.current?.click()}>
            결과 이미지 여러 장 가져오기
          </button>
        </div>
        <p className="discovery-note">
          {codex
            ? "다음 후보를 먼저 제안하고, 생성 횟수와 참조 전송을 확인합니다. 선택이나 페이지 이동만으로는 생성하지 않습니다."
            : "이 모드는 이미지를 생성하지 않습니다. 프롬프트를 외부 도구에서 각각 실행한 뒤 파일 이름을 유지해 가져와 주세요."}
        </p>
      </section>
      {currentBatches.map((b) => (
        <section
          className="discovery-progress"
          key={b.batchId}
          aria-label="생성 진행"
        >
          <strong>
            {batchLabel(b)} · {b.completed}/{b.authorizedTurns}회 처리
          </strong>
          <p>{b.message}</p>
          {["queued", "running"].includes(b.state) && (
            <>
              <progress max={b.authorizedTurns} value={b.completed} />
              <button
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    await api(base + `/batches/${b.batchId}/cancel`, {});
                    await load();
                  })
                }
              >
                남은 생성 취소
              </button>
            </>
          )}
        </section>
      ))}
      {activeBatch && activeBatch.roundId !== round?.roundId && (
        <div className="message">
          <span>
            다른 묶음에서 생성이 진행 중입니다. 결과는 원래 자리에 저장됩니다.
          </span>
          <button
            onClick={() =>
              void run(async () => {
                await api(base + "/active-round", {
                  roundId: activeBatch.roundId,
                });
                setFocused(false);
                await load();
              })
            }
          >
            진행 중인 묶음 보기
          </button>
          <button
            onClick={() =>
              void run(async () => {
                await api(base + `/batches/${activeBatch.batchId}/cancel`, {});
                await load();
              })
            }
          >
            남은 생성 취소
          </button>
        </div>
      )}
      {copied !== null && (
        <label>
          복사할 묶음 프롬프트
          <textarea
            className="discovery-copy"
            value={copied}
            readOnly
            onFocus={(e) => e.target.select()}
          />
        </label>
      )}
      <input
        ref={resultInput}
        className="sr-only"
        tabIndex={-1}
        type="file"
        accept="image/png,image/jpeg,image/webp"
        multiple
        aria-label="결과 이미지 파일"
        onChange={(e) => {
          const files = e.target.files;
          void run(() => upload(files, false));
          e.target.value = "";
        }}
      />
      <details className="discovery-history">
        <summary>선택 기록·기존 이미지·참고자료</summary>
        <div>
          <h2>선택 기록</h2>
          {state?.history.length ? (
            state.history.map((h) => (
              <div className="discovery-history-row" key={h.reactionId}>
                <span>
                  {reactionNames[h.action] ?? h.action} · {h.labels.join(", ")}
                  {h.part ? ` · ${parts[h.part]}` : ""}
                </span>
                <button
                  disabled={busy}
                  onClick={() =>
                    void run(() =>
                      react("undo", [], { targetReactionId: h.reactionId }),
                    )
                  }
                >
                  되돌리기
                </button>
              </div>
            ))
          ) : (
            <p>아직 저장한 반응이 없습니다.</p>
          )}
          <h2>독립 참고자료</h2>
          <p>후보와의 관계를 추측하지 않고 보관한 이미지입니다.</p>
          <button
            disabled={busy}
            onClick={() => referenceInput.current?.click()}
          >
            참고 이미지 더 가져오기
          </button>
          <input
            ref={referenceInput}
            className="sr-only"
            type="file"
            multiple
            accept="image/png,image/jpeg,image/webp"
            aria-label="추가 참고 이미지"
            onChange={(e) => {
              const files = e.target.files;
              void run(() => upload(files, true));
              e.target.value = "";
            }}
          />
          {!!state?.inspirations.length && (
            <>
              <div className="discovery-library-grid">
                {state.inspirations.map((i) => (
                  <button
                    key={i.inspirationId}
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        await api(base + "/references", {
                          requestId: crypto.randomUUID(),
                          expectedRevision: state.revision,
                          inspirationIds: [i.inspirationId],
                        });
                        await load();
                      })
                    }
                  >
                    <img src={assetURL(pid, i.assetId)} alt="독립 참고자료" />
                    <span>이 자료에서 탐색</span>
                  </button>
                ))}
              </div>
              <button
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    await api(base + "/references", {
                      requestId: crypto.randomUUID(),
                      expectedRevision: state.revision,
                      inspirationIds: state.inspirations
                        .slice(0, 12)
                        .map((i) => i.inspirationId),
                    });
                    await load();
                  })
                }
              >
                참고자료를 각각 출발점으로 보기
              </button>
            </>
          )}
          <h2>기존 이미지 라이브러리</h2>
          <p>과거 기록의 묶음이나 취향을 추측하지 않습니다.</p>
          <div className="discovery-library-grid">
            {state?.library
              .filter((l) => l.image)
              .map((l) => (
                <button
                  disabled={busy}
                  key={l.versionId}
                  onClick={() =>
                    void run(async () => {
                      await api(base + "/library", {
                        requestId: crypto.randomUUID(),
                        expectedRevision: state.revision,
                        versionId: l.versionId,
                      });
                      setFocused(false);
                      await load();
                    })
                  }
                >
                  <img src={assetURL(pid, l.image!.assetId)} alt="" />
                  <span>{l.label}</span>
                </button>
              ))}
          </div>
        </div>
      </details>
      <p className="discovery-note">
        부분 보존은 선택한 방향에만 적용됩니다. 이미지는 숨은 구조나 실제 3D
        모델의 완성을 증명하지 않습니다.
      </p>
      {renderImports()}
      {enlarge && (
        <Dialog title={enlarge.label} wide onClose={() => setEnlarge(null)}>
          <img
            className="discovery-enlarged"
            src={assetURL(pid, enlarge.assetId)}
            alt={`${enlarge.label} 확대 이미지`}
          />
        </Dialog>
      )}
      {generation && (
        <Dialog title="이번 후보 생성 확인" onClose={() => setGeneration(null)}>
          <p>
            선택한 후보마다 Codex 작업 1회를 요청합니다. 자동 재시도나 유료 API
            대체 실행은 없습니다.
          </p>
          <fieldset>
            <legend>이번에 만들 후보</legend>
            {generation.round.candidates
              .filter((c) => !c.image)
              .map((c) => (
                <label className="check" key={c.candidateId}>
                  <input
                    type="checkbox"
                    checked={generation.ids.includes(c.candidateId)}
                    onChange={(e) =>
                      setGeneration(
                        (g) =>
                          g && {
                            ...g,
                            ids: e.target.checked
                              ? [...g.ids, c.candidateId]
                              : g.ids.filter((id) => id !== c.candidateId),
                          },
                      )
                    }
                  />
                  {c.label} ·{" "}
                  {c.preserveParts.length
                    ? `${c.preserveParts.map((p) => parts[p]).join(", ")} 보존 / `
                    : ""}
                  {c.kind === "observation"
                    ? "같은 디자인의 다른 모습"
                    : c.varyPart && c.varyPart !== "whole"
                      ? `${parts[c.varyPart]} 변경`
                      : "새 디자인 제안"}
                </label>
              ))}
          </fieldset>
          {!!references.length && (
            <>
              <p>
                아래 참조 이미지 {references.length}장이 기기 밖의 Codex로
                전송됩니다.
              </p>
              <div className="discovery-reference-strip">
                {references.map((i) => (
                  <img
                    key={i.assetId}
                    src={assetURL(pid, i.assetId)}
                    alt="생성에 사용할 참조 이미지"
                  />
                ))}
              </div>
              <label className="check">
                <input
                  type="checkbox"
                  checked={consent}
                  onChange={(e) => setConsent(e.target.checked)}
                />
                표시된 참조 이미지 전송에 동의합니다
              </label>
            </>
          )}
          <details
            onToggle={(e) => {
              if (e.currentTarget.open && !catalog.length)
                void api<
                  { slug: string; display_name: string; isDefault?: boolean }[]
                >("/codex/models")
                  .then(setCatalog)
                  .catch((e) => setError(e.message));
            }}
          >
            <summary>모델·내보내기 옵션</summary>
            <label>
              생성 모델
              <select value={model} onChange={(e) => setModel(e.target.value)}>
                <option value="">Codex의 사용 가능한 기본 모델</option>
                {catalog.map((m) => (
                  <option key={m.slug} value={m.slug}>
                    {m.display_name || m.slug}
                  </option>
                ))}
              </select>
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={exportPermission}
                onChange={(e) => setExportPermission(e.target.checked)}
              />
              생성 이미지를 이후 파일 묶음에 포함해도 됩니다
            </label>
          </details>
          <p className="discovery-note">
            로그인한 Codex 계정의 사용량이 적용됩니다. 정확한 잔여량은 이
            화면에서 알 수 없습니다. 취소해도 이미 제출한 작업은 완료되거나
            사용량을 소비할 수 있습니다.
          </p>
          <button
            className="primary"
            disabled={
              busy ||
              !generation.ids.length ||
              (!!references.length && !consent)
            }
            onClick={() => void run(generate)}
          >
            {generation.ids.length}회 요청하고 생성 시작
          </button>
          {error && <p role="alert">{error}</p>}
        </Dialog>
      )}
      {refine && (
        <Dialog
          title="좋아하는 부분을 두고 새 대안 보기"
          onClose={() => setRefine(null)}
        >
          <p>
            선택한 방향의 한 부분만 바꾼 새 디자인을 제안합니다. 조합 전체가
            마음에 드는지는 다시 판단해 주세요.
          </p>
          <label>
            바꿔 보고 싶은 부분
            <select
              value={part}
              onChange={(e) => setPart(e.target.value as Part)}
            >
              {Object.entries(parts).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <label>
            이번 제안에서 그대로 둘 부분
            <select
              value={preserve}
              onChange={(e) => setPreserve(e.target.value as Part | "")}
            >
              <option value="">기존에 보존한 부분만 유지</option>
              {Object.entries(parts).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </label>
          <p>
            변경: {parts[part]} · 보존:{" "}
            {Array.from(
              new Set([
                ...(state?.directions.find(
                  (d) => d.directionId === refine.directionId,
                )?.preserved
                  ? Object.keys(
                      state.directions.find(
                        (d) => d.directionId === refine.directionId,
                      )!.preserved,
                    ).map((p) => parts[p as Part])
                  : []),
                ...(preserve ? [parts[preserve]] : []),
              ]),
            ).join(", ") || "따로 선택한 부분 없음"}
          </p>
          <button
            className="primary"
            disabled={busy || preserve === part}
            onClick={() =>
              void run(() =>
                prepare({
                  candidateId: refine.candidateId,
                  intent: "focus",
                  part,
                  ...(preserve ? { preservePart: preserve } : {}),
                  count: 3,
                }),
              )
            }
          >
            이 범위로 대안 3개 준비
          </button>
          <hr />
          <p>
            이 방향의 다음 제안들에도 보존할 부분은 따로 저장할 수 있습니다.
            언제든 해제할 수 있습니다.
          </p>
          <div className="discovery-part-actions">
            {Object.entries(parts).map(([key, value]) => {
              const kept = !!state?.directions.find(
                (d) => d.directionId === refine.directionId,
              )?.preserved[key as Part];
              return (
                <button
                  key={key}
                  disabled={busy}
                  aria-pressed={kept}
                  onClick={() =>
                    void run(() =>
                      react(kept ? "unlock_part" : "keep_part", [refine], {
                        part: key,
                      }),
                    )
                  }
                >
                  {value} {kept ? "보존 해제" : "계속 보존"}
                </button>
              );
            })}
          </div>
          {error && <p role="alert">{error}</p>}
        </Dialog>
      )}
      {problem && (
        <Dialog
          title="이 모습에서 무엇이 걸리나요?"
          onClose={() => setProblem(null)}
        >
          <p>
            그림의 오류와 디자인 자체의 선호를 구분해 다음 작업을 준비합니다.
          </p>
          <div className="discovery-problem-options">
            <button
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await react("image_wrong", [problem]);
                  setProblem(null);
                })
              }
            >
              이미지가 틀린 것 같아요 · 문제로 표시만 하기
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void run(() =>
                  prepare({
                    candidateId: problem.candidateId,
                    intent: "correct",
                    view: problem.view ?? "front",
                  }),
                )
              }
            >
              얼굴 등이 원래와 달라요 · 같은 디자인으로 수정
            </button>
            <button
              onClick={() => {
                setRefine(problem);
                setPart("face");
                setProblem(null);
              }}
            >
              원래 디자인이지만 얼굴·턱이 마음에 안 들어요 · 디자인 변경
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void run(() =>
                  prepare({
                    candidateId: problem.candidateId,
                    intent: "focus",
                    part: "outfit",
                    view: "back",
                    count: 3,
                  }),
                )
              }
            >
              뒷모습은 아직 안 정했어요 · 새 디자인 대안
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void run(() =>
                  prepare({
                    candidateId: problem.candidateId,
                    intent: "observe",
                    view: "front",
                  }),
                )
              }
            >
              가려져 판단하기 어려워요 · 더 선명한 정면 확인
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void run(() =>
                  prepare({
                    candidateId: problem.candidateId,
                    intent: "adopt",
                  }),
                )
              }
            >
              의도와 다르지만 좋아요 · 독립 후보로 보관
            </button>
            <button
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await react("skip", [problem]);
                  setProblem(null);
                })
              }
            >
              지금은 보류하고 계속 탐색
            </button>
          </div>
          <p className="discovery-note">
            같은 디자인의 이미지 수정은 결과가 요청된 기준으로 최대 두
            번까지입니다. 해결되지 않으면 보류하거나 외부 제작 방법을 이용할 수
            있습니다.
          </p>
          {error && <p role="alert">{error}</p>}
        </Dialog>
      )}
      {replace && (
        <Dialog
          title="선택한 디자인을 바꿀까요?"
          onClose={() => setReplace(null)}
        >
          <p>
            {state?.selection?.label} 대신 {replace.label}을 선택합니다. 이전
            선택은 기록에서 복구할 수 있습니다.
          </p>
          <button
            className="primary"
            disabled={busy}
            onClick={() =>
              void run(async () => {
                await react("use_design", [replace], {
                  replaceSelection: true,
                });
                setReplace(null);
                setChoiceOpen(true);
              })
            }
          >
            이 디자인으로 선택 교체
          </button>
        </Dialog>
      )}
      {choiceOpen && state?.selection && (
        <Dialog title="내가 선택한 디자인" onClose={() => setChoiceOpen(false)}>
          <img
            className="discovery-choice-image"
            src={assetURL(pid, state.selection.image.assetId)}
            alt={state.selection.label}
          />
          <h3>{state.selection.label}</h3>
          <p>디자인 선택 완료 · 모델 제작 검토와는 별개입니다.</p>
          <p>
            보존한 부분:{" "}
            {Object.keys(state.selection.preserved)
              .map((p) => parts[p as Part])
              .join(", ") || "별도로 확정하지 않음"}
          </p>
          <p>
            {state.selection.coverageUnconfigured
              ? "다른 모습을 확인할 범위가 아직 정해지지 않았습니다. 미정인 범위를 선택 기록에 함께 보관했습니다."
              : state.selection.uncheckedViews.length
                ? "확인되지 않은 모습이 남아 있습니다. 그 공백을 선택 기록에 함께 보관했습니다."
                : "이미지만으로 실제 3D 모델의 구조와 작동을 검증하지는 않았습니다."}
          </p>
          <p>
            다른 방향과 미정인 구조도 그대로 남습니다. 모델링 참고 정리는 필요할
            때 이어갈 수 있습니다.
          </p>
          <button
            onClick={() => {
              setChoiceOpen(false);
              onAdvanced(state.selection!.versionId);
            }}
          >
            세부 근거·모델링 준비 보기
          </button>
        </Dialog>
      )}
      {directionName && (
        <Dialog title="방향 이름 바꾸기" onClose={() => setDirectionName(null)}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run(async () => {
                await react("rename_direction", [directionName.candidate], {
                  name: directionName.name,
                });
                setDirectionName(null);
              });
            }}
          >
            <label>
              방향 이름
              <input
                required
                maxLength={120}
                value={directionName.name}
                onChange={(e) =>
                  setDirectionName((d) => d && { ...d, name: e.target.value })
                }
              />
            </label>
            <button className="primary" disabled={busy}>
              이름 저장
            </button>
          </form>
        </Dialog>
      )}
    </section>
  );
}

function batchLabel(batch: Batch) {
  return (
    (
      {
        queued: "생성 대기",
        running: "생성 진행 중",
        completed: "요청 처리 완료",
        cancelled: "남은 생성 취소됨",
        interrupted: "앱 중단 후 복구됨",
        stopped: "연결·조건 변경으로 중단됨",
      } as Record<string, string>
    )[batch.state] ?? "작업 상태 확인 필요"
  );
}
