"""A dependency-free validator for the subset of JSON Schema this project uses.

Supports: type, enum, properties, required, additionalProperties (bool or
schema), items, minItems, maxItems, minimum, maximum, minLength, maxLength,
pattern, propertyNames.pattern, anyOf. An empty schema `{}` accepts anything.

It exists because the target environment has no `jsonschema` package, and
because the error strings need to be good enough to hand straight back to a
model as a repair instruction.
"""

from __future__ import annotations

import re
from typing import Any

_TYPE_MAP: dict[str, tuple] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "object": (dict,),
    "array": (list,),
    "null": (type(None),),
}


def _type_ok(value: Any, expected: str) -> bool:
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    py = _TYPE_MAP.get(expected)
    if py is None:
        return True
    return isinstance(value, py)


def validate(instance: Any, schema: dict, path: str = "") -> list[str]:
    """Return a list of human-readable violations. Empty list == valid."""
    errors: list[str] = []
    if not schema:
        return errors
    here = path or "<root>"

    if "anyOf" in schema:
        branches = [validate(instance, sub, path) for sub in schema["anyOf"]]
        if all(branch for branch in branches):
            errors.append(f"{here}: matches none of the {len(branches)} permitted shapes")
        return errors

    expected = schema.get("type")
    if expected is not None:
        options = expected if isinstance(expected, list) else [expected]
        if not any(_type_ok(instance, opt) for opt in options):
            got = type(instance).__name__
            errors.append(f"{here}: expected type {'|'.join(options)}, got {got}")
            return errors

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{here}: {instance!r} is not one of {schema['enum']}")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{here}: string shorter than {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{here}: string longer than {schema['maxLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{here}: {instance!r} does not match /{schema['pattern']}/")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{here}: {instance} < minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{here}: {instance} > maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{here}: needs at least {schema['minItems']} items, has {len(instance)}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{here}: has more than {schema['maxItems']} items")
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(instance):
                errors.extend(validate(item, item_schema, f"{path}[{i}]"))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{here}: missing required property {key!r}")

        props: dict = schema.get("properties", {})
        name_pattern = schema.get("propertyNames", {}).get("pattern")
        additional = schema.get("additionalProperties", True)

        for key, value in instance.items():
            child = f"{path}.{key}" if path else key
            if key in props:
                errors.extend(validate(value, props[key], child))
                continue
            if name_pattern and not re.search(name_pattern, key):
                errors.append(f"{child}: key {key!r} does not match /{name_pattern}/")
            if additional is False:
                errors.append(f"{child}: property {key!r} is not permitted here")
            elif isinstance(additional, dict):
                errors.extend(validate(value, additional, child))

    return errors
