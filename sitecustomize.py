import sys


if sys.platform.startswith("win"):
    import platform

    platform.machine = lambda: "AMD64"
