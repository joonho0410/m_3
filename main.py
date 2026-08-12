"""Mini NPU Simulator - MAC(Multiply-Accumulate) 기반 패턴 판별기."""

import json
import os
import re
import time

EPSILON = 1e-9
REPEAT = 10
DATA_JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")


# ---------------------------------------------------------------------------
# 데이터 구조
# ---------------------------------------------------------------------------

def make_grid(n, fill=0.0):
    return [[fill] * n for _ in range(n)]


def get_value(grid, row, col):
    return grid[row][col]


def set_value(grid, row, col, value):
    grid[row][col] = value


def generate_pattern(n, kind):
    """크기 N의 십자가(cross)/X 패턴을 생성한다 (성능 측정용 샘플 데이터로도 사용)."""
    grid = make_grid(n, 0.0)
    mid = n // 2
    if kind == "cross":
        for i in range(n):
            grid[i][mid] = 1.0
            grid[mid][i] = 1.0
    else:
        for i in range(n):
            grid[i][i] = 1.0
            grid[i][n - 1 - i] = 1.0
    return grid


# ---------------------------------------------------------------------------
# MAC 연산 (반복문 직접 구현, 외부 라이브러리 금지)
# ---------------------------------------------------------------------------

def mac(pattern, filt):
    total = 0.0
    for i in range(len(pattern)):
        row_p = pattern[i]
        row_f = filt[i]
        for j in range(len(row_p)):
            total += row_p[j] * row_f[j]
    return total


def timed_mac(pattern, filt, repeat=REPEAT):
    """MAC 연산을 repeat회 반복 실행하고 평균 시간(ms)과 마지막 점수를 반환한다."""
    start = time.perf_counter()
    score = 0.0
    for _ in range(repeat):
        score = mac(pattern, filt)
    elapsed_ms = (time.perf_counter() - start) / repeat * 1000
    return elapsed_ms, score


# ---------------------------------------------------------------------------
# 라벨 정규화
# ---------------------------------------------------------------------------

def normalize_label(raw):
    """'+' / 'cross' -> 'Cross', 'x' -> 'X'. 알 수 없는 값이면 None."""
    if raw is None:
        return None
    key = str(raw).strip().lower()
    if key in ("+", "cross"):
        return "Cross"
    if key == "x":
        return "X"
    return None


def judge_cross_x(score_cross, score_x):
    if abs(score_cross - score_x) < EPSILON:
        return "UNDECIDED"
    return "Cross" if score_cross > score_x else "X"


def judge_ab(score_a, score_b):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"
    return "A" if score_a > score_b else "B"


# ---------------------------------------------------------------------------
# 출력 유틸
# ---------------------------------------------------------------------------

def print_header(title):
    bar = "#" + "-" * 40
    print(f"\n{bar}")
    print(f"# {title}")
    print(bar)


def print_perf_table(rows):
    print(f"{'크기':<10}{'평균 시간(ms)':<16}{'연산 횟수'}")
    print("-" * 37)
    for n, avg_ms in rows:
        label = f"{n}×{n}"
        print(f"{label:<10}{avg_ms:<16.3f}{n * n}")


# ---------------------------------------------------------------------------
# 모드 1: 사용자 입력 (3x3)
# ---------------------------------------------------------------------------

def read_grid(n, header):
    print(header)
    grid = []
    while len(grid) < n:
        raw = input()
        parts = raw.strip().split()
        if len(parts) != n:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        try:
            row = [float(p) for p in parts]
        except ValueError:
            print(f"입력 형식 오류: 각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요.")
            continue
        grid.append(row)
    return grid


def mode_user_input():
    n = 3

    print_header("[1] 필터 입력")
    filter_a = read_grid(n, "필터 A (3줄 입력, 공백 구분)")
    filter_b = read_grid(n, "\n필터 B (3줄 입력, 공백 구분)")
    print("\n✓ 필터 A, B 저장 완료")

    print_header("[2] 패턴 입력")
    pattern = read_grid(n, "패턴 (3줄 입력, 공백 구분)")

    print_header("[3] MAC 결과")
    avg_ms_a, score_a = timed_mac(pattern, filter_a)
    avg_ms_b, score_b = timed_mac(pattern, filter_b)
    verdict = judge_ab(score_a, score_b)

    print(f"A 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간(평균/{REPEAT}회): {(avg_ms_a + avg_ms_b) / 2:.3f} ms")
    if verdict == "UNDECIDED":
        print(f"판정: 판정 불가 (|A-B| < {EPSILON})")
    else:
        print(f"판정: {verdict}")

    print_header("[4] 성능 분석 (3x3)")
    print_perf_table([(n, (avg_ms_a + avg_ms_b) / 2)])


# ---------------------------------------------------------------------------
# 모드 2: data.json 분석
# ---------------------------------------------------------------------------

def natural_sort_key(pattern_key):
    m = re.match(r"size_(\d+)_(\d+)", pattern_key)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    return (10**9, pattern_key)


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


def analyze_pattern(pattern_key, item, filters):
    """단일 패턴 케이스를 분석. 반환: (passed: bool, reason: str|None)"""
    print(f"--- {pattern_key} ---")

    m = re.match(r"size_(\d+)_", pattern_key)
    if not m:
        print("✗ 스키마 오류: 키에서 크기(N)를 추출할 수 없습니다")
        return False, "키 형식 오류 (size_N_idx 아님)"
    n = int(m.group(1))

    inp = item.get("input")
    expected_raw = item.get("expected")
    if inp is None or expected_raw is None:
        print("✗ 스키마 오류: input 또는 expected 필드가 누락되었습니다")
        return False, "input/expected 필드 누락"

    if n not in filters:
        print(f"✗ 필터 없음: size_{n} 필터가 정의되어 있지 않습니다")
        return False, f"size_{n} 필터 없음"

    if len(inp) != n or any(len(row) != n for row in inp):
        print(f"✗ 크기 불일치: 패턴 크기가 {n}x{n} 이 아닙니다")
        return False, "필터-패턴 크기 불일치"

    filt = filters[n]
    if "Cross" not in filt or "X" not in filt:
        print("✗ 필터 라벨 오류: Cross/X 필터가 모두 준비되어 있지 않습니다")
        return False, "필터 라벨 불완전"

    expected = normalize_label(expected_raw)
    if expected is None:
        print(f"✗ 라벨 오류: expected 값을 정규화할 수 없습니다 ('{expected_raw}')")
        return False, f"알 수 없는 expected 라벨: {expected_raw}"

    score_cross = mac(inp, filt["Cross"])
    score_x = mac(inp, filt["X"])
    verdict = judge_cross_x(score_cross, score_x)
    passed = verdict == expected
    status = "PASS" if passed else "FAIL"

    print(f"Cross 점수: {score_cross}")
    print(f"X 점수: {score_x}")
    if verdict == "UNDECIDED":
        print(f"판정: UNDECIDED | expected: {expected} | {status} (동점 규칙)")
        reason = None if passed else "동점(UNDECIDED) 처리 규칙에 따라 FAIL"
    else:
        print(f"판정: {verdict} | expected: {expected} | {status}")
        reason = None if passed else f"판정({verdict}) != expected({expected})"

    return passed, reason


def measure_performance(filters, patterns_raw):
    perf_rows = []

    generated_pattern = generate_pattern(3, "cross")
    generated_filter = generate_pattern(3, "cross")
    avg_ms, _ = timed_mac(generated_pattern, generated_filter)
    perf_rows.append((3, avg_ms))

    for n in sorted(filters.keys()):
        filt = filters[n]
        sample_pattern = None
        for pattern_key, item in patterns_raw.items():
            if pattern_key.startswith(f"size_{n}_") and item.get("input"):
                sample_pattern = item["input"]
                break
        sample_filter = filt.get("Cross") or filt.get("X")
        if sample_pattern is None:
            sample_pattern = sample_filter
        if sample_pattern is None or sample_filter is None:
            continue
        avg_ms, _ = timed_mac(sample_pattern, sample_filter)
        perf_rows.append((n, avg_ms))

    return perf_rows


def mode_json_analysis(json_path=DATA_JSON_PATH):
    print_header("[1] 필터 로드")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ data.json 파일을 찾을 수 없습니다: {json_path}")
        return
    except json.JSONDecodeError as e:
        print(f"✗ data.json 파싱 오류: {e}")
        return

    filters_raw = data.get("filters", {})
    patterns_raw = data.get("patterns", {})
    filters = load_filters(filters_raw)

    print_header("[2] 패턴 분석 (라벨 정규화 적용)")
    results = []
    for pattern_key in sorted(patterns_raw.keys(), key=natural_sort_key):
        item = patterns_raw[pattern_key]
        passed, reason = analyze_pattern(pattern_key, item, filters)
        results.append((pattern_key, passed, reason))

    print_header("[3] 성능 분석 (평균/10회)")
    print_perf_table(measure_performance(filters, patterns_raw))

    print_header("[4] 결과 요약")
    total = len(results)
    passed_count = sum(1 for _, passed, _ in results if passed)
    failed = [(key, reason) for key, passed, reason in results if not passed]

    print(f"총 테스트: {total}개")
    print(f"통과: {passed_count}개")
    print(f"실패: {len(failed)}개")
    if failed:
        print("\n실패 케이스:")
        for key, reason in failed:
            print(f"- {key}: {reason}")


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------

def main():
    print("=== Mini NPU Simulator ===\n")
    print("[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        choice = input("선택: ").strip()
        if choice in ("1", "2"):
            break
        print("잘못된 입력입니다. 1 또는 2를 입력하세요.")

    if choice == "1":
        mode_user_input()
    else:
        mode_json_analysis()


if __name__ == "__main__":
    main()
