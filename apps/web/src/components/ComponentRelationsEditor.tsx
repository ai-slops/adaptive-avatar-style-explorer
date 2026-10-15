import type { Spec } from "../types";
import { human } from "../ui";
export function ComponentRelationsEditor({
  value,
  onChange,
}: {
  value: Spec["componentRelations"];
  onChange: (value: Spec["componentRelations"]) => void;
}) {
  function update(
    index: number,
    patch: Partial<Spec["componentRelations"][number]>,
  ) {
    onChange(
      value.map((relation, i) =>
        i === index ? { ...relation, ...patch } : relation,
      ),
    );
  }
  return (
    <fieldset className="component-relations-editor">
      <legend>Component relationships</legend>
      <p>
        Describe intended attachments, layers and symmetry. Keep unseen
        construction proposed or unspecified until you choose it. Left and right
        refer to the character.
      </p>
      {value.map((relation, index) => (
        <fieldset className="component-relation" key={index}>
          <legend>Relationship {index + 1}</legend>
          <div className="inline-inputs">
            <label>
              Component
              <input
                aria-label={`Relationship ${index + 1} component`}
                required
                maxLength={120}
                value={relation.component}
                onChange={(e) => update(index, { component: e.target.value })}
                placeholder="hair ornament"
              />
            </label>
            <label>
              Relationship
              <select
                aria-label={`Relationship ${index + 1} relation`}
                value={relation.relation}
                onChange={(e) =>
                  update(index, {
                    relation: e.target.value as typeof relation.relation,
                  })
                }
              >
                {[
                  "attached_to",
                  "layered_over",
                  "connected_to",
                  "symmetric_with",
                ].map((item) => (
                  <option key={item} value={item}>
                    {human(item)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Target
              <input
                aria-label={`Relationship ${index + 1} target`}
                required
                maxLength={120}
                value={relation.target}
                onChange={(e) => update(index, { target: e.target.value })}
                placeholder="character-left hair"
              />
            </label>
          </div>
          <label>
            Intent state
            <select
              aria-label={`Relationship ${index + 1} state`}
              value={relation.state}
              onChange={(e) =>
                update(index, {
                  state: e.target.value as typeof relation.state,
                })
              }
            >
              {["unspecified", "proposed", "inferred", "user_confirmed"].map(
                (item) => (
                  <option key={item} value={item}>
                    {human(item)}
                  </option>
                ),
              )}
            </select>
          </label>
          <button
            type="button"
            onClick={() => onChange(value.filter((_, i) => i !== index))}
          >
            Remove relationship {index + 1}
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        onClick={() =>
          onChange([
            ...value,
            {
              component: "",
              relation: "attached_to",
              target: "",
              state: "proposed",
            },
          ])
        }
      >
        Add component relationship
      </button>
    </fieldset>
  );
}
