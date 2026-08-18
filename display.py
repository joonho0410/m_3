"""콘솔 출력 유틸."""


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
