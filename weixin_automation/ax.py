from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Any, Iterable, Protocol


AX_WINDOWS = "AXWindows"
AX_CHILDREN = "AXChildren"
AX_ROLE = "AXRole"
AX_TITLE = "AXTitle"
AX_VALUE = "AXValue"
AX_FOCUSED = "AXFocused"
AX_PRESS = "AXPress"


class AXError(RuntimeError):
    def __init__(self, code: int, operation: str):
        super().__init__(f"Accessibility operation failed: {operation} returned {code}")
        self.code = code
        self.operation = operation


class AXBackend(Protocol):
    def get_attribute(self, element: Any, attribute: str) -> Any:
        raise NotImplementedError

    def set_attribute(self, element: Any, attribute: str, value: Any) -> None:
        raise NotImplementedError

    def perform_action(self, element: Any, action: str) -> None:
        raise NotImplementedError


@dataclass(frozen=True)
class AXNode:
    element: Any
    backend: AXBackend

    def get(self, attribute: str, default: Any = None) -> Any:
        try:
            value = self.backend.get_attribute(self.element, attribute)
        except AXError:
            return default
        return default if value is None else value

    def children(self) -> list["AXNode"]:
        values = self.get(AX_CHILDREN, [])
        return [AXNode(child, self.backend) for child in values]

    def focus(self) -> None:
        self.backend.set_attribute(self.element, AX_FOCUSED, True)

    def set_value(self, value: str) -> None:
        self.backend.set_attribute(self.element, AX_VALUE, value)

    def press(self) -> None:
        self.backend.perform_action(self.element, AX_PRESS)


class PyObjCBackend:
    def __init__(self):
        try:
            from ApplicationServices import (  # type: ignore
                AXUIElementCopyAttributeValue,
                AXUIElementCreateApplication,
                AXUIElementPerformAction,
                AXUIElementSetAttributeValue,
            )
        except ImportError as exc:
            raise RuntimeError(
                "PyObjC is required. Install it with: python3 -m pip install pyobjc"
            ) from exc

        self._copy_attribute = AXUIElementCopyAttributeValue
        self._create_application = AXUIElementCreateApplication
        self._perform_action = AXUIElementPerformAction
        self._set_attribute = AXUIElementSetAttributeValue

    def application(self, pid: int) -> AXNode:
        return AXNode(self._create_application(pid), self)

    def get_attribute(self, element: Any, attribute: str) -> Any:
        err, value = self._copy_attribute(element, attribute, None)
        if err != 0:
            raise AXError(err, attribute)
        return value

    def set_attribute(self, element: Any, attribute: str, value: Any) -> None:
        err = self._set_attribute(element, attribute, value)
        if err != 0:
            raise AXError(err, attribute)

    def perform_action(self, element: Any, action: str) -> None:
        err = self._perform_action(element, action)
        if err != 0:
            raise AXError(err, action)


def is_accessibility_trusted(prompt: bool = True) -> bool:
    try:
        from ApplicationServices import AXIsProcessTrustedWithOptions  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "PyObjC is required. Install it with: python3 -m pip install pyobjc"
        ) from exc

    return bool(AXIsProcessTrustedWithOptions({"AXTrustedCheckOptionPrompt": prompt}))


def find_pid(process_name: str) -> int:
    output = subprocess.check_output(["pgrep", "-x", process_name], text=True).strip()
    if not output:
        raise RuntimeError(f"{process_name} is not running")
    return int(output.splitlines()[0])


def app_windows(app: AXNode) -> list[AXNode]:
    return [AXNode(window, app.backend) for window in app.get(AX_WINDOWS, [])]


def walk(node: AXNode, max_depth: int, depth: int = 0) -> Iterable[tuple[int, AXNode]]:
    if depth > max_depth:
        return
    yield depth, node
    if depth == max_depth:
        return
    for child in node.children():
        yield from walk(child, max_depth=max_depth, depth=depth + 1)


def dump_tree_lines(node: AXNode, max_depth: int = 5) -> list[str]:
    lines = []
    for depth, current in walk(node, max_depth=max_depth):
        role = current.get(AX_ROLE, "unknown")
        title = current.get(AX_TITLE)
        value = current.get(AX_VALUE)
        parts = [str(role)]
        if title:
            parts.append(f"title={title!r}")
        if value:
            parts.append(f"value={str(value)[:120]!r}")
        lines.append(f"{'  ' * depth}{' '.join(parts)}")
    return lines


def find_first_by_role(node: AXNode, role: str, max_depth: int = 8) -> AXNode | None:
    for _, current in walk(node, max_depth=max_depth):
        if current.get(AX_ROLE) == role:
            return current
    return None
