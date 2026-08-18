"""실행 모드: 사용자 입력(3x3) / data.json 분석."""

import re

from data_loader import DATA_JSON_PATH, load_data, load_filters, natural_sort_key
from display import print_header, print_perf_table
from grid import generate_pattern
from mac import REPEAT, mac, timed_mac
from normalize import EPSILON, judge, normalize_label


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
    verdict = judge([["A", score_a], ["B", score_b]])

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
    verdict = judge([["Cross", score_cross], ["X", score_x]])
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
    data, error = load_data(json_path)
    if error:
        print(f"✗ {error}")
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
