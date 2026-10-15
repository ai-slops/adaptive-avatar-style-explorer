import { useState } from "react";
import type { Property, Spec, Version } from "../types";
import { emptySpec, property, human } from "../ui";

export function DesignEditor({
  current,
  onClose,
  onSave,
}: {
  current: Version | null;
  onClose: () => void;
  onSave: (title: string, spec: Spec, reason: string) => Promise<void>;
}) {
  const [name, setName] = useState(""),
    [spec, setSpec] = useState<Spec>(
      current ? structuredClone(current.spec) : emptySpec(),
    ),
    [key, setKey] = useState(""),
    [value, setValue] = useState(""),
    [reason, setReason] = useState("");
  return (
    <div className="modal-scrim">
      <section
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="design-editor-title"
      >
        <button className="close" onClick={onClose} aria-label="Close">
          ×
        </button>
        <p className="eyebrow">
          {current ? "PUBLISH AN IMMUTABLE REVISION" : "A NEW DIRECTION"}
        </p>
        <h2 id="design-editor-title">
          {current ? "Refine the character." : "What could this character be?"}
        </h2>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            void onSave(name, spec, reason);
          }}
        >
          {!current && (
            <label>
              Design name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                maxLength={120}
                placeholder="The quiet astronomer"
              />
            </label>
          )}
          <label>
            Character structure
            <select
              value={spec.morphology}
              onChange={(e) =>
                setSpec({
                  ...spec,
                  morphology: e.target.value as Spec["morphology"],
                })
              }
            >
              <option value="unspecified">Still open</option>
              <option value="humanoid">Humanoid</option>
              <option value="non_humanoid">Non-humanoid</option>
            </select>
          </label>
          <label>
            Character idea
            <textarea
              value={String(spec.properties["design.description"]?.value ?? "")}
              onChange={(e) =>
                setSpec({
                  ...spec,
                  properties: {
                    ...spec.properties,
                    "design.description": property(e.target.value),
                  },
                })
              }
              placeholder="A rounded silhouette, layered travel clothes, silver hair…"
            />
          </label>
          <div className="property-list">
            {Object.entries(spec.properties)
              .filter(([k]) => k !== "design.description")
              .map(([k, p]) => (
                <div key={k}>
                  <strong>{human(k)}</strong>
                  <input
                    aria-label={`${k} value`}
                    value={String(p.value ?? "")}
                    onChange={(e) =>
                      setSpec({
                        ...spec,
                        properties: {
                          ...spec.properties,
                          [k]: { ...p, value: e.target.value || null },
                        },
                      })
                    }
                  />
                  <select
                    aria-label={`${k} state`}
                    value={p.state}
                    onChange={(e) =>
                      setSpec({
                        ...spec,
                        properties: {
                          ...spec.properties,
                          [k]: {
                            ...p,
                            state: e.target.value as Property["state"],
                            value:
                              e.target.value === "unspecified" ? null : p.value,
                          },
                        },
                      })
                    }
                  >
                    {[
                      "unspecified",
                      "proposed",
                      "inferred",
                      "user_confirmed",
                    ].map((s) => (
                      <option key={s}>{s}</option>
                    ))}
                  </select>
                </div>
              ))}
          </div>
          <div className="inline-inputs">
            <label>
              Property name
              <input
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="hair.ornament_side"
              />
            </label>
            <label>
              Proposed value
              <input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="character-left"
              />
            </label>
            <button
              type="button"
              disabled={!key.trim()}
              onClick={() => {
                setSpec({
                  ...spec,
                  properties: {
                    ...spec.properties,
                    [key.trim()]: property(value),
                  },
                });
                setKey("");
                setValue("");
              }}
            >
              Add
            </button>
          </div>
          <label>
            Unresolved design decisions{" "}
            <small>One per line. Unknown is a useful state.</small>
            <textarea
              value={spec.unresolvedDecisions.join("\n")}
              onChange={(e) =>
                setSpec({
                  ...spec,
                  unresolvedDecisions: e.target.value
                    .split("\n")
                    .filter(Boolean),
                })
              }
              placeholder="Back construction of the jacket\nHair ornament attachment"
            />
          </label>
          {current && (
            <label>
              Why this design changes
              <input
                required
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
          )}
          <p className="muted">
            A new view belongs to the same version. A permanent design change
            creates a new revision.
          </p>
          <button className="primary">
            {current ? "Publish new revision" : "Create design direction"} ↗
          </button>
        </form>
      </section>
    </div>
  );
}
