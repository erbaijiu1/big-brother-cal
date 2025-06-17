import json
import re
from datetime import datetime


def is_valid_json(string):
    """检查字符串是否为有效的 JSON 格式"""
    try:
        json.loads(string)
    except json.JSONDecodeError:
        return False
    return True


def escape_special_characters(input_string):
    """手动转义特殊字符"""
    return input_string.replace('\\', '\\\\') \
                       .replace('"', '\\"') \
                       .replace('\n', '\\n') \
                       .replace('\t', '\\t')


def add_key_value_to_json(json_str, key, value):
    """向 JSON 字符串中添加键值对"""
    event_data = json.loads(json_str)
    event_data[key] = value  # 根据需要设置为 True 或 False
    return json.dumps(event_data, ensure_ascii=False)


def set_stream_key_value(json_str, key, value):
    """为流式 JSON 数据设置键值对"""
    try:
        if not json_str:
            return json_str

        event = json_str.decode("utf-8").strip()  # 显式转换为字符串
        if event.startswith("data:"):
            event = event[5:]

        if is_valid_json(event):
            json_val = add_key_value_to_json(event, key, value)
            return f"data: {json_val}\n\n"
        else:
            return event
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        print(f"Error in set_stream_key_value: {str(e)}")
        return json_str


def safe_nested_get(data, *keys, default=None):
    """安全获取嵌套字典值"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return default
    return data if data is not None else default


def replace_think_tags(text):
    """使用正则表达式替换 <think> 标签及其内容"""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)


def get_milliseconds():
    """获取当前时间的毫秒部分"""
    now = datetime.now()
    milliseconds = now.microsecond // 1000  # 使用整数除法
    return now.replace(microsecond=milliseconds * 1000)


def strip_markdown_json(content):
    if not isinstance(content, str):
        return ""

    # 去掉 Markdown JSON 格式的标记
    if content.startswith("```json"):
        content = content[len("```json"):].strip()
        if content.endswith("```"):
            content = content[:-len("```")].strip()
        return content
    return content


def is_valid_structured_json_array(json_str, field_spec_str):
    """检查 JSON 数组是否符合指定的字段和类型规范"""
    try:
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        data = json.loads(json_str)
        if not isinstance(data, list):
            return False

        for item in data:
            if not isinstance(item, dict):
                return False

            if field_spec_str:
                field_spec = json.loads(field_spec_str)
                for field, type_name in field_spec.items():
                    if field not in item:
                        return False
                    expected_type = type_mapping.get(type_name)
                    if expected_type is None:
                        raise ValueError(f"Unsupported type: {type_name}")

                    if not isinstance(item[field], expected_type):
                        return False

        return True
    except (json.JSONDecodeError, KeyError, TypeError):
        return False