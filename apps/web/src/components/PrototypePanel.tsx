import { useState } from "react";
import { api } from "../api";
import type { Version, Project, ModelBuild } from "../types";
export function PrototypePanel({
  version,
  project,
  builds,
  run,
  onSaved,
}: {
  version: Version;
  project: Project;
  builds: ModelBuild[];
  run: (f: () => Promise<void>) => Promise<void>;
  onSaved: () => Promise<void>;
}) {
  const [label, setLabel] = useState(""),
    [hash, setHash] = useState(""),
    [scope, setScope] = useState("");
  return (
    <section className="paper-panel">
      <p className="eyebrow">WHEN A REAL PROTOTYPE EXISTS</p>
      <h2>Track a model build and what you tested.</h2>
      <p>
        Register an externally produced revision, then import its captures from
        Design & evidence. A supplied hash identifies provenance; this
        application does not inspect the model artifact or render it.
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void run(async () => {
            await api(`/projects/${project.project_id}/model-builds`, {
              targetVersionId: version.version_id,
              label,
              artifactHash: hash || null,
              testScope: scope,
            });
            setLabel("");
            setHash("");
            setScope("");
            await onSaved();
          });
        }}
      >
        <div className="inline-inputs">
          <label>
            External build label
            <input
              required
              value={label}
              maxLength={200}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Blender prototype, revision 2"
            />
          </label>
          <label>
            Reported artifact SHA-256, optional
            <input
              value={hash}
              pattern="[0-9a-f]{64}"
              onChange={(e) => setHash(e.target.value)}
            />
          </label>
        </div>
        <label>
          Reported test scope
          <textarea
            required
            value={scope}
            onChange={(e) => setScope(e.target.value)}
            placeholder="Neutral front/profile/back screenshots. Raised-arm clipping checked. Rig and runtime tests still pending."
          />
        </label>
        <button>Register external model build</button>
      </form>
      {builds.map((b) => (
        <div className="finding" key={b.build_id}>
          <strong>{JSON.parse(b.report_json).label}</strong>
          <p>{JSON.parse(b.report_json).testScope}</p>
          <small>
            User reported · artifact not inspected · design revision{" "}
            {version.revision}
          </small>
        </div>
      ))}
    </section>
  );
}
