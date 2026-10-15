import { useState, useEffect } from "react";
import type { SessionInfo, Registration, Project } from "../types";
import { human } from "../ui";
import { CodexAccount } from "./Codex";
import { api } from "../api";
export function Account({
  codex = false,
  run,
  onSwitch,
}: {
  codex?: boolean;
  run: (f: () => Promise<void>) => Promise<void>;
  onSwitch: () => Promise<void>;
}) {
  const [session, setSession] = useState<SessionInfo | null>(null),
    [registrations, setRegistrations] = useState<Registration[]>([]),
    [offline, setOffline] = useState<Project[]>([]),
    [deleting, setDeleting] = useState("");
  async function load() {
    const [s, r, p] = await Promise.all([
      api<SessionInfo>("/session"),
      api<Registration[]>("/auth/registrations"),
      api<Project[]>("/auth/offline-projects"),
    ]);
    setSession(s);
    setRegistrations(r);
    setOffline(p);
  }
  useEffect(() => {
    void run(load);
  }, []);
  return (
    <>
      {codex ? (
        <CodexAccount run={run} />
      ) : (
        <>
          <div className="page-heading">
            <div>
              <p className="eyebrow">YOUR DEVICE / YOUR ACCOUNT</p>
              <h1>
                A private workspace.
                <br />
                Optional assistance.
              </h1>
              <p>
                Connect your own ChatGPT account for text and vision analysis.
                <br />
                All design exploration and text exports also work offline.
              </p>
            </div>
          </div>
          <div className="inspect-grid">
            <section className="paper-panel">
              <h2>Continue with ChatGPT</h2>
              <p>
                Sign-in registers this local application. Plan use requires a
                separate grant. Your conversations and memories are not
                imported.
              </p>
              <button
                className="primary"
                onClick={() =>
                  void run(async () => {
                    const result = await api<{ authorizationUrl: string }>(
                      "/auth/siwc/start",
                      {},
                    );
                    location.assign(result.authorizationUrl);
                  })
                }
              >
                Continue with ChatGPT ↗
              </button>
              <p className="muted account-note">
                Review your app usage limit and credit settings with the
                provider before enabling analysis. This app cannot certify
                current provider billing settings. Local request budgets measure
                requests, not tokens or money.
              </p>
              <a
                href="https://chatgpt.com/#settings"
                target="_blank"
                rel="noreferrer"
              >
                Review ChatGPT settings ↗
              </a>
            </section>
            <section className="paper-panel">
              <h2>Saved registrations</h2>
              <p>
                Active:{" "}
                {session?.registrationId
                  ? registrations.find(
                      (r) => r.registration_id === session.registrationId,
                    )?.display_name
                  : "Local offline profile"}
              </p>
              <button
                onClick={() =>
                  void run(async () => {
                    await api("/auth/active-registration", {
                      registrationId: null,
                    });
                    await onSwitch();
                    await load();
                  })
                }
              >
                Use offline profile
              </button>
              {registrations.map((r) => (
                <div className="registration" key={r.registration_id}>
                  <strong>{r.display_name}</strong>
                  <small>
                    {r.issued_client_id} · {human(r.grant_state)}
                  </small>
                  <div className="inline-actions">
                    <button
                      disabled={r.grant_state === "disconnected"}
                      onClick={() =>
                        void run(async () => {
                          await api("/auth/active-registration", {
                            registrationId: r.registration_id,
                          });
                          await onSwitch();
                          await load();
                        })
                      }
                    >
                      {session?.registrationId === r.registration_id
                        ? "Active"
                        : "Switch account"}
                    </button>
                    <button
                      onClick={() =>
                        void run(async () => {
                          const result = await api<{
                            authorizationUrl: string;
                          }>("/auth/siwc/start", {
                            registrationId: r.registration_id,
                          });
                          location.assign(result.authorizationUrl);
                        })
                      }
                    >
                      Reconnect
                    </button>
                  </div>
                </div>
              ))}
            </section>
          </div>
          {session?.registrationId && offline.length > 0 && (
            <section className="paper-panel">
              <h2>Bring an offline project into this account.</h2>
              <p>
                This explicitly binds the project to the currently validated
                registration. Other accounts will not see it.
              </p>
              {offline.map((p) => (
                <div className="slot" key={p.project_id}>
                  <span>{p.title}</span>
                  <button
                    onClick={() =>
                      void run(async () => {
                        await api("/auth/bind-offline-project", {
                          projectId: p.project_id,
                        });
                        await onSwitch();
                        await load();
                      })
                    }
                  >
                    Bind to active account
                  </button>
                </div>
              ))}
            </section>
          )}
        </>
      )}
      <section className="paper-panel">
        <h2>이 브라우저의 연결</h2>
        <label className="checkbox">
          <input
            type="checkbox"
            checked={session?.rememberBrowser ?? false}
            disabled={!session}
            onChange={(e) => {
              const rememberBrowser = e.target.checked;
              void run(async () => {
                await api("/session/remember", { rememberBrowser });
                await load();
              });
            }}
          />
          이 브라우저를 30일 동안 기억하기
        </label>
        <p>
          연결을 기억하면 서버를 다시 시작해도 기본 주소로 바로 들어올 수
          있습니다. ‘Sign out locally’를 누르면 이 브라우저의 연결을 해제합니다.
        </p>
        {session?.rememberBrowser && (
          <p className="muted">
            연결 만료:{" "}
            {new Date(session.sessionExpiresAt * 1000).toLocaleDateString()}
          </p>
        )}
      </section>
      <section className="paper-panel">
        <h2>Delete local project data</h2>
        <p>
          Deletion removes project images, feedback, observations, plans, jobs
          and caches from this installation. Previously downloaded archives and
          Codex-managed caches remain outside the app's control. Signing out is
          a separate action.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void run(async () => {
              await api(`/projects/${deleting}`, undefined, "DELETE");
              setDeleting("");
              await onSwitch();
              await load();
            });
          }}
        >
          <DeleteProjectSelect value={deleting} onChange={setDeleting} />
          <button disabled={!deleting}>Delete selected project data</button>
        </form>
      </section>
    </>
  );
}
function DeleteProjectSelect({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [projects, setProjects] = useState<Project[]>([]);
  useEffect(() => {
    void api<Project[]>("/projects").then(setProjects);
  }, []);
  return (
    <label>
      Project to delete
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Choose a project to delete</option>
        {projects.map((p) => (
          <option key={p.project_id} value={p.project_id}>
            {p.title}
          </option>
        ))}
      </select>
    </label>
  );
}
