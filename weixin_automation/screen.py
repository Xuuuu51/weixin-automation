from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Mapping


WindowInfo = Mapping[str, Any]


def choose_largest_window(windows: list[WindowInfo], owner_pid: int) -> WindowInfo | None:
    candidates = [
        window
        for window in windows
        if window.get("kCGWindowOwnerPID") == owner_pid and _window_area(window) > 0
    ]
    if not candidates:
        return None
    return max(candidates, key=_window_area)


def list_on_screen_windows() -> list[WindowInfo]:
    try:
        from Quartz import (  # type: ignore
            CGWindowListCopyWindowInfo,
            kCGNullWindowID,
            kCGWindowListOptionOnScreenOnly,
        )
    except ImportError as exc:
        raise RuntimeError(
            "PyObjC Quartz is required. Run: uv sync"
        ) from exc

    return list(CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID))


def capture_window_to_png(window: WindowInfo, output_path: Path) -> Path:
    try:
        from CoreFoundation import NSURL  # type: ignore
        from Quartz import (  # type: ignore
            CGImageDestinationAddImage,
            CGImageDestinationCreateWithURL,
            CGImageDestinationFinalize,
            CGWindowListCreateImage,
            CGRectInfinite,
            kCGWindowImageBoundsIgnoreFraming,
            kCGWindowListOptionIncludingWindow,
        )
    except ImportError as exc:
        raise RuntimeError(
            "PyObjC Quartz and CoreFoundation are required. Run: uv sync"
        ) from exc

    window_number = window.get("kCGWindowNumber")
    if window_number is None:
        raise RuntimeError("Window info does not include kCGWindowNumber")

    image = CGWindowListCreateImage(
        CGRectInfinite,
        kCGWindowListOptionIncludingWindow,
        int(window_number),
        kCGWindowImageBoundsIgnoreFraming,
    )
    if image is None:
        return capture_window_to_png_with_screencapture(window, output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    url = NSURL.fileURLWithPath_(str(output_path))
    destination = CGImageDestinationCreateWithURL(url, "public.png", 1, None)
    if destination is None:
        raise RuntimeError(f"Could not create image destination: {output_path}")

    CGImageDestinationAddImage(destination, image, None)
    if not CGImageDestinationFinalize(destination):
        raise RuntimeError(f"Could not write screenshot: {output_path}")

    return output_path


def capture_window_to_png_with_screencapture(window: WindowInfo, output_path: Path) -> Path:
    window_number = window.get("kCGWindowNumber")
    if window_number is None:
        raise RuntimeError("Window info does not include kCGWindowNumber")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["screencapture", "-l", str(int(window_number)), str(output_path)],
        check=True,
    )
    return output_path


def _window_area(window: WindowInfo) -> float:
    bounds = window.get("kCGWindowBounds") or {}
    return float(bounds.get("Width", 0)) * float(bounds.get("Height", 0))
