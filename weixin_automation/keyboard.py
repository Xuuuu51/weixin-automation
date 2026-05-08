from __future__ import annotations

import time
import subprocess


KEY_CODES = {
    "a": 0x00,
    "f": 0x03,
    "v": 0x09,
    "enter": 0x24,
    "return": 0x24,
    "delete": 0x33,
}


MODIFIER_FLAGS = {
    "cmd": 1 << 20,
    "command": 1 << 20,
    "shift": 1 << 17,
    "alt": 1 << 19,
    "option": 1 << 19,
    "ctrl": 1 << 18,
    "control": 1 << 18,
}


class MacKeyboard:
    def __init__(self, delay: float = 0.12):
        self.delay = delay
        try:
            from AppKit import NSPasteboard, NSStringPboardType  # type: ignore
            from Quartz import (  # type: ignore
                CGEventCreateKeyboardEvent,
                CGEventPost,
                CGEventSetFlags,
                kCGHIDEventTap,
            )
        except ImportError as exc:
            raise RuntimeError("PyObjC AppKit and Quartz are required. Run: uv sync") from exc

        self._pasteboard = NSPasteboard.generalPasteboard()
        self._pasteboard_type = NSStringPboardType
        self._create_keyboard_event = CGEventCreateKeyboardEvent
        self._post_event = CGEventPost
        self._set_flags = CGEventSetFlags
        self._event_tap = kCGHIDEventTap

    def hotkey(self, value: str) -> None:
        parts = [part.strip().lower() for part in value.split("+")]
        key = parts[-1]
        modifiers = parts[:-1]
        self.press_key(key, modifiers=modifiers)

    def press_key(self, key: str, modifiers: list[str] | None = None) -> None:
        key_code = KEY_CODES[key.lower()]
        flags = 0
        for modifier in modifiers or []:
            flags |= MODIFIER_FLAGS[modifier.lower()]

        down = self._create_keyboard_event(None, key_code, True)
        up = self._create_keyboard_event(None, key_code, False)
        if flags:
            self._set_flags(down, flags)
            self._set_flags(up, flags)
        self._post_event(self._event_tap, down)
        self._post_event(self._event_tap, up)
        time.sleep(self.delay)

    def type_text(self, text: str) -> None:
        self._pasteboard.clearContents()
        self._pasteboard.setString_forType_(text, self._pasteboard_type)
        self.hotkey("cmd+v")


def send_return_with_system_events() -> None:
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to key code 36',
        ],
        check=True,
    )


def send_hotkey_with_system_events(shortcut: str) -> None:
    parts = [part.strip().lower() for part in shortcut.split("+")]
    key = parts[-1]
    modifiers = parts[:-1]
    modifier_clause = _applescript_modifier_clause(modifiers)
    if key in ("enter", "return"):
        command = f'tell application "System Events" to key code 36{modifier_clause}'
    else:
        command = f'tell application "System Events" to keystroke "{key}"{modifier_clause}'
    subprocess.run(["osascript", "-e", command], check=True)


def activate_app(app_name: str) -> None:
    try:
        from AppKit import NSWorkspace  # type: ignore
    except ImportError as exc:
        raise RuntimeError("PyObjC AppKit is required. Run: uv sync") from exc

    if not NSWorkspace.sharedWorkspace().launchApplication_(app_name):
        raise RuntimeError(f"Could not activate {app_name}")
    time.sleep(0.5)


def _applescript_modifier_clause(modifiers: list[str]) -> str:
    if not modifiers:
        return ""
    names = {
        "cmd": "command down",
        "command": "command down",
        "shift": "shift down",
        "alt": "option down",
        "option": "option down",
        "ctrl": "control down",
        "control": "control down",
    }
    values = [names[modifier] for modifier in modifiers]
    return " using {" + ", ".join(values) + "}"
