import { useEffect, useState } from "react";
import type { Evidence, Property, Spec, Version } from "../types";
import { api } from "../api";
import {
  CanonicalPropertyEditor,
  PropertyDetails,
  type SourceChoice,
} from "./CanonicalPropertyEditor";
import { ComponentRelationsEditor } from "./ComponentRelationsEditor";
import { emptySpec, property, human } from "../ui";

export function DesignEditor({
  current,
  projectId,
  branchId,
  evidence,
  onClose,
  onSave,
}: {
  current: Version | null;
  projectId: string;
  branchId: string;
  evidence: { label: string; evidence: Evidence }[];
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
  const [unresolved, setUnresolved] = useState(
    spec.unresolvedDecisions.join("\n"),
  );
  const [events, setEvents] = useState<SourceChoice[]>([]);
  const [sourceError, setSourceError] = useState("");
  useEffect(() => {
    let active = true;
    void api<{ event_id: string; sequence: number; action: string }[]>(
      `/projects/${projectId}/events?branchId=${branchId}`,
    )
      .then((rows) => {
        if (active)
          setEvents(
            rows.map((event) => ({
              id: event.event_id,
              label: `#${event.sequence} · ${human(event.action)}`,
            })),
          );
      })
      .catch((error) => {
        if (active) setSourceError(error.message);
      });
    return () => {
      active = false;
    };
  }, [projectId, branchId]);
  const imageSources = [
    ...new Map(
      evidence.flatMap((item) =>
        item.evidence.links.map(
          (link) =>
            [
              link.link_id,
              {
                id: link.link_id,
                label: `${item.label} · ${human(link.observations[0]?.observedPresentation.view ?? "unreviewed")} · ${link.status}`,
              },
            ] as const,
        ),
      ),
    ).values(),
  ];
  function updateProperty(key: string, value: Property) {
    setSpec((current) => ({
      ...current,
      properties: { ...current.properties, [key]: value },
    }));
  }
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
                    "design.description": {
                      ...(spec.properties["design.description"] ??
                        property("")),
                      value: e.target.value || null,
                      state:
                        spec.properties["design.description"]?.state ===
                          "unspecified" ||
                        !spec.properties["design.description"]
                          ? e.target.value
                            ? "proposed"
                            : "unspecified"
                          : spec.properties["design.description"].state,
                    },
                  },
                })
              }
              placeholder="A rounded silhouette, layered travel clothes, silver hair…"
            />
          </label>
          {spec.properties["design.description"] && (
            <PropertyDetails
              name="design.description"
              value={spec.properties["design.description"]}
              onChange={(value) => updateProperty("design.description", value)}
              imageSources={imageSources}
              eventSources={events}
            />
          )}
          {sourceError && (
            <p role="alert">
              Supporting decisions could not be loaded: {sourceError}. Existing
              sources will be preserved.
            </p>
          )}
          <div className="property-list canonical-properties">
            {Object.entries(spec.properties)
              .filter(([key]) => key !== "design.description")
              .map(([key, value]) => (
                <CanonicalPropertyEditor
                  key={key}
                  name={key}
                  value={value}
                  onChange={(value) => updateProperty(key, value)}
                  imageSources={imageSources}
                  eventSources={events}
                  onRemove={() =>
                    setSpec((current) => ({
                      ...current,
                      properties: Object.fromEntries(
                        Object.entries(current.properties).filter(
                          ([name]) => name !== key,
                        ),
                      ),
                    }))
                  }
                />
              ))}
          </div>
          <div className="inline-inputs">
            <label>
              Property name
              <input
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="hair.ornament_side"
                maxLength={120}
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
              disabled={
                !key.trim() || Object.hasOwn(spec.properties, key.trim())
              }
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
          {Object.hasOwn(spec.properties, key.trim()) && (
            <p className="muted">
              This property already exists. Edit it above.
            </p>
          )}
          <ComponentRelationsEditor
            value={spec.componentRelations}
            onChange={(componentRelations) =>
              setSpec({ ...spec, componentRelations })
            }
          />
          <label>
            Unresolved design decisions{" "}
            <small>One per line. Unknown is a useful state.</small>
            <textarea
              value={unresolved}
              onChange={(e) => {
                setUnresolved(e.target.value);
                setSpec({
                  ...spec,
                  unresolvedDecisions: e.target.value
                    .split("\n")
                    .map((value) => value.trim())
                    .filter(Boolean),
                });
              }}
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
