"""International English entry point. powered by hcok."""
import flet as ft
from main import main


def start(page):
    main(page, language="en")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from macro.diagnostics import self_test
        raise SystemExit(self_test(sys.argv[2], language='en'))
    ft.run(start)
