import { useEffect, useState } from "react";
import { api } from "../api";

export function ConnectBrowser({
  onConnected,
}: {
  onConnected: () => Promise<void>;
}) {
  const [link, setLink] = useState(""),
    [busy, setBusy] = useState(false);
  const [error, setError] = useState(""),
    [opened, setOpened] = useState(false);
  async function connect(secret: string) {
    await api("/session/bootstrap", { secret, rememberBrowser: true });
    await onConnected();
  }
  useEffect(() => {
    if (!opened) return;
    let attempts = 0;
    const timer = setInterval(() => {
      if (++attempts > 30) {
        clearInterval(timer);
        return;
      }
      void api("/session")
        .then(async () => {
          clearInterval(timer);
          await onConnected();
        })
        .catch(() => {});
    }, 2000);
    return () => clearInterval(timer);
  }, [opened]);
  return (
    <section className="browser-connect" aria-labelledby="connect-title">
      <h2 id="connect-title">이 브라우저를 연결해 주세요.</h2>
      <p>
        처음 한 번 연결하면 30일 동안 이 브라우저를 기억합니다. 다음부터는 기본
        주소로 바로 들어올 수 있습니다.
      </p>
      <button
        className="primary"
        disabled={busy}
        onClick={() => {
          setBusy(true);
          setError("");
          void api("/session/open-browser", {})
            .then(() => setOpened(true))
            .catch((e) => setError(e.message))
            .finally(() => setBusy(false));
        }}
      >
        이 기기에서 워크스페이스 열기 ↗
      </button>
      <p className="muted">
        서버가 실행 중인 기기의 기본 브라우저에서 연결 창을 엽니다.
      </p>
      {opened && (
        <p role="status">
          연결 창을 열었습니다. 새 창에서 연결하면 여기도 자동으로 열립니다.
          다른 브라우저가 열렸다면 그 창을 사용해 주세요.
        </p>
      )}
      <details>
        <summary>창이 열리지 않거나 다른 브라우저를 사용하시나요?</summary>
        <p>
          최초 연결 링크를 한 번만 붙여 넣어 주세요. 브라우저 주소는 기본 주소로
          유지됩니다.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setBusy(true);
            setError("");
            void (async () => {
              const url = new URL(link.trim());
              if (url.origin !== location.origin)
                throw new Error("현재 서버의 연결 링크를 사용해 주세요.");
              const secret = new URLSearchParams(url.hash.slice(1)).get(
                "launch",
              );
              if (!secret)
                throw new Error(
                  "launch 값이 포함된 최초 연결 링크를 사용해 주세요.",
                );
              await connect(secret);
            })()
              .catch((e) => setError(e.message))
              .finally(() => setBusy(false));
          }}
        >
          <label>
            최초 연결 링크
            <input
              type="password"
              autoComplete="off"
              value={link}
              onChange={(e) => setLink(e.target.value)}
              required
            />
          </label>
          <button disabled={busy || !link.trim()}>
            이 브라우저 연결하고 기억하기
          </button>
        </form>
      </details>
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
