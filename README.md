# WeChat Desktop Automation Prototype

This prototype uses macOS Accessibility through PyObjC to inspect and control the local WeChat desktop app.

The first version is intentionally conservative: it can inspect WeChat's accessibility tree and fill a visible input box with a draft. It does not auto-send messages.

## Setup

```bash
uv sync
```

Grant Accessibility permission to the terminal or Python:

```text
System Settings -> Privacy & Security -> Accessibility
```

## Inspect WeChat

Open WeChat, open any chat, then run:

```bash
uv run wechat-inspect-ax
```

This prints the visible Accessibility tree so we can see which roles WeChat exposes on your machine.

## Fill A Draft

Open a WeChat chat window and run:

```bash
uv run wechat-fill-draft "你好，这是一条草稿。"
```

Review the draft in WeChat before sending.

## OCR The WeChat Window

If WeChat exposes too little Accessibility metadata, capture the visible WeChat window and run macOS Vision OCR:

```bash
uv run wechat-ocr-window
```

The screenshot is saved to `artifacts/wechat-window.png`.

The capture path uses Quartz first and falls back to macOS `screencapture` when Quartz cannot return an image. macOS may ask for Screen Recording permission for your terminal.

## Search A Contact And Fill A Message

Open WeChat, search a contact, enter the chat, and fill a draft:

```bash
uv run wechat-message-contact "张三" "我晚点到"
```

Print the planned keyboard actions without touching WeChat:

```bash
uv run wechat-message-contact "张三" "我晚点到" --dry-run
```

Send only when you explicitly opt in:

```bash
uv run wechat-message-contact "张三" "我晚点到" --send
```

By default, `--send` uses plain Enter through macOS System Events. If your WeChat sends with `Cmd+Enter`, use:

```bash
uv run wechat-message-contact "张三" "我晚点到" --send --send-shortcut cmd+enter
```

## Notes

WeChat may expose incomplete Accessibility metadata. If text roles are missing, the next fallback is screenshot/OCR plus controlled keyboard input.
