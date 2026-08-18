"""n×n 그리드 데이터 구조 및 패턴 생성."""


def make_grid(n, fill=0.0):
    return [[fill] * n for _ in range(n)]


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
