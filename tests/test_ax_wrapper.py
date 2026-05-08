import unittest

from weixin_automation.ax import AXError, AXNode, dump_tree_lines


class FakeBackend:
    def __init__(self):
        self.values = {}
        self.set_calls = []
        self.action_calls = []

    def get_attribute(self, element, attribute):
        key = (element, attribute)
        if key not in self.values:
            raise AXError(25205, attribute)
        return self.values[key]

    def set_attribute(self, element, attribute, value):
        self.set_calls.append((element, attribute, value))

    def perform_action(self, element, action):
        self.action_calls.append((element, action))


class AXWrapperTests(unittest.TestCase):
    def test_axnode_returns_none_when_attribute_is_missing(self):
        backend = FakeBackend()
        node = AXNode("input", backend)

        self.assertIsNone(node.get("AXTitle"))

    def test_axnode_sets_value_and_marks_focus(self):
        backend = FakeBackend()
        node = AXNode("input", backend)

        node.focus()
        node.set_value("hello")

        self.assertEqual(
            backend.set_calls,
            [
                ("input", "AXFocused", True),
                ("input", "AXValue", "hello"),
            ],
        )

    def test_dump_tree_includes_role_title_value_and_children(self):
        backend = FakeBackend()
        backend.values[("root", "AXRole")] = "AXWindow"
        backend.values[("root", "AXTitle")] = "WeChat"
        backend.values[("root", "AXValue")] = None
        backend.values[("root", "AXChildren")] = ["child"]
        backend.values[("child", "AXRole")] = "AXTextArea"
        backend.values[("child", "AXTitle")] = ""
        backend.values[("child", "AXValue")] = "last message"
        backend.values[("child", "AXChildren")] = []

        lines = dump_tree_lines(AXNode("root", backend), max_depth=3)

        self.assertEqual(
            lines,
            [
                "AXWindow title='WeChat'",
                "  AXTextArea value='last message'",
            ],
        )


if __name__ == "__main__":
    unittest.main()
