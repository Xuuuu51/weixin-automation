import unittest

from weixin_automation.wechat_flow import build_contact_message_steps


class WeChatFlowTests(unittest.TestCase):
    def test_build_contact_message_steps_defaults_to_draft_only(self):
        steps = build_contact_message_steps("张三", "我晚点到")

        self.assertEqual(
            [step.kind for step in steps],
            [
                "activate",
                "hotkey",
                "text",
                "key",
                "wait",
                "text",
            ],
        )
        self.assertEqual(steps[1].value, "cmd+f")
        self.assertEqual(steps[2].value, "张三")
        self.assertEqual(steps[5].value, "我晚点到")

    def test_build_contact_message_steps_sends_with_applescript_enter_by_default(self):
        steps = build_contact_message_steps("张三", "测试", send=True)

        self.assertEqual(steps[-2].kind, "wait")
        self.assertEqual(steps[-1].kind, "send_key")
        self.assertEqual(steps[-1].value, "enter")

    def test_build_contact_message_steps_can_override_send_shortcut(self):
        steps = build_contact_message_steps("张三", "测试", send=True, send_shortcut="enter")

        self.assertEqual(steps[-1].kind, "send_key")
        self.assertEqual(steps[-1].value, "enter")

    def test_build_contact_message_steps_can_override_send_hotkey(self):
        steps = build_contact_message_steps("张三", "测试", send=True, send_shortcut="cmd+enter")

        self.assertEqual(steps[-1].kind, "send_hotkey")
        self.assertEqual(steps[-1].value, "cmd+enter")


if __name__ == "__main__":
    unittest.main()
