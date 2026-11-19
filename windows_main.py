"""Entry point of the Windows panel: every launcher starts `pythonw.exe -B app\\windows_main.py`.

Python never caches the bytecode of the script it starts: it compiles it at every launch.
The panel therefore lives in windows_panel.py, imported from its cached bytecode, and this
file stays a few lines long. Imported as a module, `windows_main` is windows_panel itself
(same object), so `import windows_main` keeps working for tests, tools and old code.
"""
import sys

if __name__ == '__main__':
    from windows_panel import main
    main()
else:
    import windows_panel
    sys.modules[__name__] = windows_panel
