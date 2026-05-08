import argparse
from pathlib import Path

from weixin_automation.ax import (
    PyObjCBackend,
    app_windows,
    dump_tree_lines,
    find_first_by_role,
    find_pid,
    is_accessibility_trusted,
)
from weixin_automation.ocr import recognize_text_in_image
from weixin_automation.screen import (
    capture_window_to_png,
    choose_largest_window,
    list_on_screen_windows,
)
from weixin_automation.wechat_flow import build_contact_message_steps, run_steps


TEXT_INPUT_ROLES = ("AXTextArea", "AXTextField")


def inspect_wechat_ax() -> int:
    if not is_accessibility_trusted(prompt=True):
        print("Accessibility permission is not granted yet.")
        print("Open System Settings -> Privacy & Security -> Accessibility.")
        print("Grant access to your terminal app or Python, then run this again.")
        return 1

    pid = find_pid("WeChat")
    backend = PyObjCBackend()
    app = backend.application(pid)
    windows = app_windows(app)

    print(f"WeChat pid: {pid}")
    print(f"Windows: {len(windows)}")

    for index, window in enumerate(windows):
        print(f"\n# Window {index}")
        for line in dump_tree_lines(window, max_depth=6):
            print(line)

    return 0


def fill_wechat_draft() -> int:
    parser = argparse.ArgumentParser(
        description="Fill the visible WeChat text input with a draft reply."
    )
    parser.add_argument("text", help="Draft text to place in the WeChat input box.")
    args = parser.parse_args()

    if not is_accessibility_trusted(prompt=True):
        print("Accessibility permission is not granted yet.")
        return 1

    backend = PyObjCBackend()
    app = backend.application(find_pid("WeChat"))
    text_input = _find_text_input(app_windows(app))
    if text_input is None:
        print("Could not find a WeChat text input via Accessibility.")
        print("Open a chat window and try wechat-inspect-ax to inspect roles.")
        return 2

    text_input.focus()
    text_input.set_value(args.text)
    print("Draft filled. Review it in WeChat before sending.")
    return 0


def ocr_wechat_window() -> int:
    parser = argparse.ArgumentParser(
        description="Capture the largest WeChat window and run macOS Vision OCR."
    )
    parser.add_argument(
        "--output",
        default="artifacts/wechat-window.png",
        help="Path where the captured WeChat window PNG is saved.",
    )
    parser.add_argument(
        "--lang",
        action="append",
        dest="languages",
        help="Recognition language, for example zh-Hans or en-US. Can be repeated.",
    )
    args = parser.parse_args()

    pid = find_pid("WeChat")
    window = choose_largest_window(list_on_screen_windows(), owner_pid=pid)
    if window is None:
        print("Could not find an on-screen WeChat window.")
        return 2

    output_path = capture_window_to_png(window, Path(args.output))
    lines = recognize_text_in_image(output_path, languages=args.languages or ["zh-Hans", "en-US"])

    print(f"Screenshot: {output_path}")
    print(f"Recognized lines: {len(lines)}")
    for line in lines:
        print(line)

    return 0


def message_contact() -> int:
    parser = argparse.ArgumentParser(
        description="Search a WeChat contact, open the chat, and fill or send a message."
    )
    parser.add_argument("contact", help="Contact name to search, for example 张三.")
    parser.add_argument("message", help="Message text to type into the chat.")
    parser.add_argument(
        "--send",
        action="store_true",
        help="Press Enter after typing the message. Without this flag, only a draft is filled.",
    )
    parser.add_argument(
        "--send-shortcut",
        default="enter",
        help="Shortcut used when --send is set. Defaults to enter; use cmd+enter if your WeChat is configured that way.",
    )
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=0.8,
        help="Seconds to wait after opening the contact before typing the message.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned keyboard actions without controlling WeChat.",
    )
    parser.add_argument(
        "--send-wait-seconds",
        type=float,
        default=0.3,
        help="Seconds to wait after typing before sending.",
    )
    args = parser.parse_args()

    steps = build_contact_message_steps(
        args.contact,
        args.message,
        send=args.send,
        settle_seconds=args.settle_seconds,
        send_shortcut=args.send_shortcut,
        send_wait_seconds=args.send_wait_seconds,
    )
    if args.dry_run:
        for step in steps:
            detail = f" {step.value}" if step.value else ""
            wait = f" ({step.seconds:.1f}s)" if step.kind == "wait" else ""
            print(f"{step.kind}{detail}{wait}")
        return 0

    run_steps(steps)
    if args.send:
        print("Message sent.")
    else:
        print("Draft filled. Review it in WeChat before sending.")
    return 0


def _find_text_input(windows):
    for window in windows:
        for role in TEXT_INPUT_ROLES:
            match = find_first_by_role(window, role, max_depth=10)
            if match is not None:
                return match
    return None
