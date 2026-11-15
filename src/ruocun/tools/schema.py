"""在内置工具使用的 JSON Schema 子集上校验调用参数，生成交给模型的工具参数结构。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def toJsonSchema(schema: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(schema)
    result.pop("$schema", None)
    return result


def objectSchema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required,
            "additionalProperties": False}


def parseSchema(schema: dict[str, Any], args: Any) -> dict[str, Any]:
    """校验并返回工具参数，供后续审批和处理器共用。"""
    _validate(schema, args, "(root)")
    if not isinstance(args, dict):
        raise ValueError("参数需要 object")
    return {name: _normalize(schema.get("properties", {}).get(name, {}), value)
            for name, value in args.items()}


def _normalize(schema: dict[str, Any], value: Any) -> Any:
    if schema.get("type") == "integer":
        return int(value)
    if isinstance(value, dict):
        return {name: _normalize(schema.get("properties", {}).get(name, {}), item)
                for name, item in value.items()}
    if isinstance(value, list):
        return [_normalize(schema.get("items", {}), item) for item in value]
    return value


def _kind(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, list):
        return "array"
    return "object"


def _validate(schema: dict[str, Any], value: Any, field: str) -> None:
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                _validate(branch, value, field)
            except ValueError:
                continue
            break
        else:
            raise ValueError(f"参数「{field}」不符合允许的类型")
    expected = schema.get("type")
    valid = {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "boolean": isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": (isinstance(value, int) and not isinstance(value, bool))
        or (isinstance(value, float) and value.is_integer()),
    }
    if expected and not valid.get(expected, False):
        raise ValueError(f"参数「{field}」需要 {expected},收到 {_kind(value)}")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"参数「{field}」校验失败:必须是 {schema['enum']}")
    if isinstance(value, str):
        length = len(value.encode("utf-16-le", errors="surrogatepass")) // 2
        if "minLength" in schema and length < schema["minLength"]:
            raise ValueError(f"参数「{field}」校验失败:最小长度 {schema['minLength']}")
        if "maxLength" in schema and length > schema["maxLength"]:
            raise ValueError(f"参数「{field}」校验失败:最大长度 {schema['maxLength']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                raise ValueError(f"缺少必填参数「{name}」({props.get(name, {}).get('type', 'any')})")
        unknown = [name for name in value if name not in props]
        if unknown and schema.get("additionalProperties") is False:
            raise ValueError(f"不接受参数 [{', '.join(unknown)}]——这些字段不在它的 schema 里")
        for name, item in value.items():
            if name in props:
                _validate(props[name], item, name if field == "(root)" else f"{field}.{name}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise ValueError(f"参数「{field}」校验失败:最少 {schema['minItems']} 项")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise ValueError(f"参数「{field}」校验失败:最多 {schema['maxItems']} 项")
        for index, item in enumerate(value):
            _validate(schema.get("items", {}), item, f"{field}.{index}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise ValueError(f"参数「{field}」校验失败:最小值 {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            raise ValueError(f"参数「{field}」校验失败:最大值 {schema['maximum']}")
