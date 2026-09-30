"""International English entry point. powered by hcok."""
from main import main


def start(page):
    main(page, language="en")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from macro.diagnostics import self_test
        raise SystemExit(self_test(sys.argv[2], language='en'))
    from app_launcher import run
    run(start)
