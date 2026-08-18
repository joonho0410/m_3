"""MAC(Multiply-Accumulate) 연산 (반복문 직접 구현, 외부 라이브러리 금지)."""

import time

REPEAT = 10


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
