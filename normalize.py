"""라벨 정규화 및 점수 비교(판정) 로직."""

EPSILON = 1e-9

LABEL_ALIASES = {
    "+": "Cross",
    "cross": "Cross",
    "x": "X",
}


def normalize_label(raw):
    """'+' / 'cross' -> 'Cross', 'x' -> 'X'. 알 수 없는 값이면 None."""
    if raw is None:
        return None
    key = str(raw).strip().lower()
    return LABEL_ALIASES.get(key)


def judge(scored_labels):
    """[[label, score], ...] 형태의 n개 결과 중 최고점 라벨을 판정한다.

    최고점이 여러 개(epsilon 이내로 동점)면 'UNDECIDED'를 반환한다.
    """
    best_score = max(score for _, score in scored_labels)
    winners = [label for label, score in scored_labels if abs(score - best_score) < EPSILON]
    return "UNDECIDED" if len(winners) > 1 else winners[0]
