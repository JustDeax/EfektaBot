import pytest
from bot import find_chrome_executable


def get_browser_launch_kwargs(**extra):
    """Returns cross-platform browser launch options for patchright."""
    kwargs = {"headless": True, **extra}
    chrome_path = find_chrome_executable()
    if chrome_path:
        kwargs["executable_path"] = chrome_path
    else:
        kwargs["channel"] = "chrome"
    return kwargs
