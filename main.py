"""Mini NPU Simulator - MAC(Multiply-Accumulate) 기반 패턴 판별기 (진입점)."""

from modes import mode_json_analysis, mode_user_input


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
    if choice == "2":
        mode_json_analysis()


if __name__ == "__main__":
    main()
