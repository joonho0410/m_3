"""data.json 로드 및 필터 스키마 검증."""

import json
import os
import re

from normalize import normalize_label

DATA_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


def natural_sort_key(pattern_key):
    m = re.match(r"size_(\d+)_(\d+)", pattern_key)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (10**9, pattern_key)


def load_data(json_path=DATA_JSON_PATH):
    """data.json을 읽어 (data, error_message) 형태로 반환한다. 성공 시 error_message는 None."""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"data.json 파일을 찾을 수 없습니다: {json_path}"
    except json.JSONDecodeError as e:
        return None, f"data.json 파싱 오류: {e}"


def load_filters(filters_raw):
    """size(int) -> {'Cross': grid, 'X': grid} 형태로 정규화하여 반환."""
    filters = {}
    for size_key, sub in filters_raw.items():
        m = re.match(r"size_(\d+)", size_key)
        if not m or not isinstance(sub, dict):
            print(f"✗ {size_key} 필터 스키마 오류: 키 형식이 size_N 이 아니거나 값이 올바르지 않습니다")
            continue
        n = int(m.group(1))
        normalized = {}
        for label_key, grid in sub.items():
            label = normalize_label(label_key)
            if label is None:
                print(f"✗ size_{n} 필터 라벨 오류: 알 수 없는 라벨 '{label_key}'")
                continue
            if len(grid) != n or any(len(row) != n for row in grid):
                print(f"✗ size_{n} 필터({label_key}) 크기 오류: {n}x{n} 이 아닙니다")
                continue
            normalized[label] = grid
        if normalized:
            filters[n] = normalized
            print(f"✓ size_{n:<3}필터 로드 완료 ({', '.join(sorted(normalized.keys()))})")
    return filters
