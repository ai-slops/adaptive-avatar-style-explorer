"""Strict native transport for reasoning; dynamic maps stay application-validated."""

from copy import deepcopy

from ..common import require
from ..contracts import ReasoningOutput
from ..learning.reference import CATEGORIES, NUMERIC


def reasoning_schema():
    schema = ReasoningOutput.model_json_schema()
    # Native structured output requires closed object properties. Transport sparse
    # attribute maps as key/value rows, then restore the fixed application contract.
    variants = []
    for key in (*NUMERIC, *CATEGORIES):
        attribute = deepcopy(schema["$defs"]["Attribute"])
        value_schema = (
            {"type": "number", "minimum": NUMERIC[key][0], "maximum": NUMERIC[key][1]}
            if key in NUMERIC
            else {"type": "string", "enum": list(CATEGORIES[key])}
        )
        attribute["properties"]["value"] = {"anyOf": [value_schema, {"type": "null"}]}
        variants.append(
            {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "key": {"type": "string", "enum": [key]},
                    "attribute": attribute,
                },
                "required": ["key", "attribute"],
            }
        )
    schema["$defs"]["Observation"]["properties"]["attributes"] = {
        "type": "array",
        "maxItems": len(variants),
        "items": {"anyOf": variants},
    }

    def close(node):
        if isinstance(node, dict):
            node.pop("default", None)
            if node.get("type") == "object":
                node["required"] = list(node.get("properties", {}))
                node["additionalProperties"] = False
            for value in node.values():
                close(value)
        elif isinstance(node, list):
            for value in node:
                close(value)

    close(schema)
    return schema


def validate_reasoning(payload):
    require(isinstance(payload, dict), "Codex reasoning output must be an object", 502)
    for suggestion in payload.get("observations", []):
        rows = suggestion["observation"]["attributes"]
        require(isinstance(rows, list), "Codex attribute rows must be a list", 502)
        require(
            all(
                isinstance(row, dict) and set(row) == {"key", "attribute"}
                for row in rows
            ),
            "Invalid Codex attribute row",
            502,
        )
        require(
            len({row["key"] for row in rows}) == len(rows),
            "Duplicate Codex attribute keys",
            502,
        )
        suggestion["observation"]["attributes"] = {
            row["key"]: row["attribute"] for row in rows
        }
    return ReasoningOutput.model_validate(payload).model_dump()
