from __future__ import annotations

import time
from dataclasses import dataclass

from weixin_automation.keyboard import (
    MacKeyboard,
    activate_app,
    send_hotkey_with_system_events,
    send_return_with_system_events,
)


@dataclass(frozen=True)
class AutomationStep:
    kind: str
    value: str
    seconds: float = 0.0


def build_contact_message_steps(
    contact: str,
    message: str,
    send: bool = False,
    settle_seconds: float = 0.8,
    send_shortcut: str = "enter",
    send_wait_seconds: float = 0.3,
) -> list[AutomationStep]:
    steps = [
        AutomationStep("activate", "WeChat"),
        AutomationStep("hotkey", "cmd+f"),
        AutomationStep("text", contact),
        AutomationStep("key", "enter"),
        AutomationStep("wait", "", seconds=settle_seconds),
        AutomationStep("text", message),
    ]
    if send:
        steps.append(AutomationStep("wait", "", seconds=send_wait_seconds))
        kind = "send_hotkey" if "+" in send_shortcut else "send_key"
        steps.append(AutomationStep(kind, send_shortcut))
    return steps


def run_steps(steps: list[AutomationStep], keyboard: MacKeyboard | None = None) -> None:
    keyboard = keyboard or MacKeyboard()
    for step in steps:
        if step.kind == "activate":
            activate_app(step.value)
        elif step.kind == "hotkey":
            keyboard.hotkey(step.value)
        elif step.kind == "text":
            keyboard.type_text(step.value)
        elif step.kind == "key":
            keyboard.press_key(step.value)
        elif step.kind == "send_key" and step.value in ("enter", "return"):
            send_return_with_system_events()
        elif step.kind == "send_key":
            keyboard.press_key(step.value)
        elif step.kind == "send_hotkey":
            send_hotkey_with_system_events(step.value)
        elif step.kind == "wait":
            time.sleep(step.seconds)
        else:
            raise RuntimeError(f"Unknown automation step: {step.kind}")
