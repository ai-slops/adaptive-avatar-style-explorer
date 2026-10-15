import { useState } from "react";
import type { Property } from "../types";
import { human } from "../ui";

export type SourceChoice = { id: string; label: string };
const states: Property["state"][] = [
  "unspecified",
  "proposed",
  "inferred",
  "user_confirmed",
];
type ValueKind = "text" | "number" | "boolean" | "list";
function valueKind(value: Property["value"]): ValueKind {
  return Array.isArray(value)
    ? "list"
    : typeof value === "number"
      ? "number"
      : typeof value === "boolean"
        ? "boolean"
        : "text";
}
export function PropertyDetails({
  name,
  value,
  onChange,
  imageSources,
  eventSources,
}: {
  name: string;
  value: Property;
  onChange: (property: Property) => void;
  imageSources: SourceChoice[];
  eventSources: SourceChoice[];
}) {
  function choices(options: SourceChoice[], selected: string[]) {
    return [
      ...options,
      ...selected
        .filter((id) => !options.some((option) => option.id === id))
        .map((id) => ({ id, label: `Historical source · ${id}` })),
    ];
  }
  return (
    <>
      <label>
        Intent state
        <select
          aria-label={`${name} state`}
          value={value.state}
          onChange={(e) =>
            onChange({
              ...value,
              state: e.target.value as Property["state"],
              value: e.target.value === "unspecified" ? null : value.value,
            })
          }
        >
          {states.map((state) => (
            <option key={state} value={state}>
              {human(state)}
            </option>
          ))}
        </select>
      </label>
      <details className="property-provenance">
        <summary>Notes & sources</summary>
        <label>
          Design notes
          <textarea
            aria-label={`${name} notes`}
            value={value.notes}
            maxLength={2000}
            onChange={(e) => onChange({ ...value, notes: e.target.value })}
          />
        </label>
        <p className="muted">
          Sources explain this design decision. They do not confirm that the
          image depicts it faithfully.
        </p>
        {(
          [
            {
              title: "Source images",
              name: `${name} source images`,
              options: imageSources,
              selected: value.sourceDepictionLinkIds,
              field: "sourceDepictionLinkIds",
            },
            {
              title: "Supporting decisions",
              name: `${name} supporting decisions`,
              options: eventSources,
              selected: value.sourceEventIds,
              field: "sourceEventIds",
            },
          ] as const
        ).map((group) => (
          <fieldset
            className="source-choices"
            key={group.field}
            aria-label={group.name}
          >
            <legend>{group.title}</legend>
            <div className="source-choice-list">
              {choices(group.options, group.selected).map((source) => (
                <label className="checkbox" key={source.id}>
                  <input
                    type="checkbox"
                    checked={group.selected.includes(source.id)}
                    onChange={(event) =>
                      onChange({
                        ...value,
                        [group.field]: event.target.checked
                          ? [...group.selected, source.id]
                          : group.selected.filter((id) => id !== source.id),
                      })
                    }
                  />
                  {source.label}
                </label>
              ))}
              {!choices(group.options, group.selected).length && (
                <p className="muted">No sources available yet.</p>
              )}
            </div>
          </fieldset>
        ))}
        {(!!value.sourceEventIds.length ||
          !!value.sourceDepictionLinkIds.length) && (
          <button
            type="button"
            onClick={() =>
              onChange({
                ...value,
                sourceEventIds: [],
                sourceDepictionLinkIds: [],
              })
            }
          >
            Clear sources for {human(name)}
          </button>
        )}
      </details>
    </>
  );
}
export function CanonicalPropertyEditor({
  name,
  value,
  onChange,
  onRemove,
  imageSources,
  eventSources,
}: {
  name: string;
  value: Property;
  onChange: (property: Property) => void;
  onRemove: () => void;
  imageSources: SourceChoice[];
  eventSources: SourceChoice[];
}) {
  const [kind, setKind] = useState<ValueKind>(() => valueKind(value.value));
  const [listText, setListText] = useState(
    Array.isArray(value.value) ? value.value.join("\n") : "",
  );
  function setValue(next: Property["value"]) {
    onChange({
      ...value,
      value: next,
      state:
        next !== null && value.state === "unspecified"
          ? "proposed"
          : value.state,
    });
  }
  return (
    <fieldset className="canonical-property">
      <legend>{human(name)}</legend>
      <label>
        Value type
        <select
          aria-label={`${name} value type`}
          value={kind}
          onChange={(e) => {
            const next = e.target.value as ValueKind;
            setKind(next);
            const replacement =
              next === "number"
                ? 0
                : next === "boolean"
                  ? false
                  : next === "list"
                    ? []
                    : "";
            setListText("");
            setValue(replacement);
          }}
        >
          <option value="text">Text</option>
          <option value="number">Number</option>
          <option value="boolean">Yes / no</option>
          <option value="list">Text list</option>
        </select>
      </label>
      <label>
        Value
        {kind === "boolean" ? (
          <select
            aria-label={`${name} value`}
            value={String(value.value ?? "")}
            onChange={(e) =>
              setValue(e.target.value === "" ? null : e.target.value === "true")
            }
          >
            <option value="">Unknown</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        ) : kind === "list" ? (
          <textarea
            aria-label={`${name} value`}
            value={listText}
            placeholder="One item per line"
            onChange={(e) => {
              setListText(e.target.value);
              setValue(
                e.target.value
                  .split("\n")
                  .map((item) => item.trim())
                  .filter(Boolean),
              );
            }}
          />
        ) : (
          <input
            aria-label={`${name} value`}
            type={kind === "number" ? "number" : "text"}
            step={kind === "number" ? "any" : undefined}
            value={value.value === null ? "" : String(value.value)}
            onChange={(e) =>
              setValue(
                e.target.value === ""
                  ? null
                  : kind === "number"
                    ? Number(e.target.value)
                    : e.target.value,
              )
            }
          />
        )}
      </label>
      <PropertyDetails
        name={name}
        value={value}
        onChange={(next) => {
          if (next.state === "unspecified") setListText("");
          onChange(next);
        }}
        imageSources={imageSources}
        eventSources={eventSources}
      />
      <button type="button" onClick={onRemove}>
        Remove {human(name)}
      </button>
    </fieldset>
  );
}
