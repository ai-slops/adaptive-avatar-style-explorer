import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Job, Plan, Project } from "../types";
import { human } from "../ui";

type Model = { slug: string; display_name: string; isDefault?: boolean };
type Status = {
  connected: boolean;
  account: { email?: string; planType?: string } | null;
};
export function CodexAccount({
  run,
}: {
  run: (f: () => Promise<void>) => Promise<void>;
}) {
  const [status, setStatus] = useState<Status | null>(null);
  const [url, setUrl] = useState("");
  async function load() {
    setStatus(await api<Status>("/codex/status"));
  }
  useEffect(() => {
    void run(load);
  }, []);
  return (
    <section className="paper-panel">
      <p className="eyebrow">LOCAL CODEX</p>
      <h1>Codex 연결</h1>
      <p>
        이 기기에 설치된 Codex의 ChatGPT 로그인을 사용합니다. 이미지 생성과
        디자인 분석을 실행할 수 있습니다.
      </p>
      <p role="status">
        {status
          ? status.connected
            ? `연결됨 · ${status.account?.email ?? "ChatGPT"} · ${status.account?.planType ?? ""}`
            : "Codex 로그인이 필요합니다."
          : "Codex 연결 확인 중…"}
      </p>
      <div className="inline-actions">
        {!status?.connected && (
          <button
            onClick={() =>
              void run(async () => {
                const r = await api<{ authorizationUrl: string }>(
                  "/codex/login",
                  {},
                );
                setUrl(r.authorizationUrl);
              })
            }
          >
            Codex에 ChatGPT로 로그인
          </button>
        )}
        <button onClick={() => void run(load)}>연결 상태 새로고침</button>
        {url && (
          <a href={url} target="_blank" rel="noreferrer">
            로그인 창 열기 ↗
          </a>
        )}
      </div>
      <p>
        생성 버튼을 누를 때마다 Codex 작업 1회를 요청합니다. 사용량은 로그인한
        Codex 계정에 적용됩니다. 자동 재시도는 하지 않습니다.
      </p>
      <p className="muted">
        로그인 정보는 Codex가 관리합니다. 앱에서 프로젝트를 삭제해도 Codex가
        관리하는 이미지 캐시나 이미 내려받은 파일은 남을 수 있습니다.
      </p>
    </section>
  );
}

export function CodexGenerate({
  plan,
  project,
  run,
  refresh,
  onReview,
}: {
  plan: Plan;
  project: Project;
  run: (f: () => Promise<void>) => Promise<void>;
  refresh: () => Promise<void>;
  onReview: () => void;
}) {
  const [models, setModels] = useState<Model[]>([]),
    [model, setModel] = useState("");
  const [references, setReferences] = useState(false),
    [permission, setPermission] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const seen = useRef(new Set<string>());
  const base = `/projects/${project.project_id}/codex`;
  async function load() {
    const list = await api<Job[]>(base + "/jobs");
    setJobs(list);
    for (const job of list) {
      if (job.result?.assetId && !seen.current.has(job.jobId)) {
        seen.current.add(job.jobId);
        await refresh();
      }
    }
  }
  useEffect(() => {
    void run(async () => {
      const [catalog, list] = await Promise.all([
        api<Model[]>("/codex/models"),
        api<Job[]>(base + "/jobs"),
      ]);
      setModels(catalog);
      setModel((catalog.find((m) => m.isDefault) ?? catalog[0])?.slug ?? "");
      list.forEach((j) => {
        if (j.result?.assetId) seen.current.add(j.jobId);
      });
      setJobs(list);
    });
  }, [project.project_id]);
  const live = jobs.some((j) => ["queued", "running"].includes(j.state));
  useEffect(() => {
    if (!live) return;
    const timer = setInterval(() => {
      void load().catch(() => {});
    }, 1500);
    return () => clearInterval(timer);
  }, [live, project.project_id]);
  return (
    <div className="codex-generation">
      <h3>Codex로 이미지 생성</h3>
      <p>
        이 프롬프트와 선택된 참조 이미지를 Codex로 전송합니다. 결과는 디자인을
        자동 변경하지 않으며 검토 대기 이미지로 저장됩니다.
      </p>
      <label>
        Codex 모델
        <select value={model} onChange={(e) => setModel(e.target.value)}>
          <option value="">모델 선택</option>
          {models.map((m) => (
            <option value={m.slug} key={m.slug}>
              {m.display_name}
            </option>
          ))}
        </select>
      </label>
      {!!plan.references.length && (
        <label className="checkbox">
          <input
            type="checkbox"
            checked={references}
            onChange={(e) => setReferences(e.target.checked)}
          />
          위 참조 이미지 {plan.references.length}장을 Codex로 전송하는 데
          동의합니다.
        </label>
      )}
      <label className="checkbox">
        <input
          type="checkbox"
          checked={permission}
          onChange={(e) => setPermission(e.target.checked)}
        />
        생성 이미지를 이 프로젝트의 내보내기에 포함합니다.
      </label>
      <button
        className="primary"
        disabled={
          !model ||
          live ||
          plan.freshness !== "current" ||
          (!!plan.references.length && !references)
        }
        onClick={() =>
          void run(async () => {
            await api(base + "/generate", {
              requestId: crypto.randomUUID(),
              planId: plan.planId,
              promptRevision: plan.revision,
              model,
              authorizeOneTurn: true,
              approveReferenceTransmission: references,
              exportPermission: permission,
              expectedEventSequence: project.event_sequence,
            });
            await load();
          })
        }
      >
        Codex로 이미지 1장 생성
      </button>
      <button onClick={() => void run(load)}>작업 상태 새로고침</button>
      {plan.freshness !== "current" && (
        <p>디자인 또는 증거가 변경되었습니다. 새 프롬프트를 준비해 주세요.</p>
      )}
      {jobs
        .filter(
          (j) =>
            j.task === "generate_image" &&
            j.planId === plan.planId &&
            j.promptRevision === plan.revision,
        )
        .map((j) => (
          <div className="job" key={j.jobId}>
            <p role="status">
              {human(j.state)}
              {j.result?.phase ? ` · ${human(j.result.phase)}` : ""}
            </p>
            {["queued", "running"].includes(j.state) && (
              <>
                <progress aria-label="Codex 이미지 생성 중" />
                <button
                  onClick={() =>
                    void run(async () => {
                      await api(base + `/jobs/${j.jobId}/cancel`, {});
                      await load();
                    })
                  }
                >
                  작업 취소
                </button>
              </>
            )}
            {j.result?.assetId && (
              <>
                <img
                  className="generated-preview"
                  src={`/api/projects/${project.project_id}/assets/${j.result.assetId}`}
                  alt="Codex 생성 이미지 · 검토 대기"
                />
                <p>
                  생성 완료 · 검토 대기
                  {j.state === "stale"
                    ? " · 요청 이후 디자인 또는 증거가 변경되었습니다."
                    : ""}
                </p>
                <button onClick={onReview}>생성 이미지 검토 →</button>
              </>
            )}
            {j.result?.error && <p role="alert">{j.result.error}</p>}
            {j.result?.message && <p>{j.result.message}</p>}
          </div>
        ))}
    </div>
  );
}
