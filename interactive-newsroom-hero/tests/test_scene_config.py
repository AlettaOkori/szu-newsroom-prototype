import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from scene_config import (
    A1_ROLE,
    DESKS,
    NEWSROOM_OUTPUT_NAMES,
    OUTPUT_NAMES,
    RenderSpec,
    rgba_hex,
    validate_desks,
)


EXPECTED = [
    ("a1", "A1 智能选题", "策划编辑", "#c8102eff",
     "../../demo/pages/m1-topics.html"),
    ("a2", "A2 智能采集", "记者", "#e87524ff",
     "../../demo/pages/m2-collection.html"),
    ("a3", "A3 智能写作", "文字编辑", "#2d8c5aff",
     "../../demo/pages/m3-writing.html"),
    ("a4", "A4 智能审校", "审校编辑", "#a83274ff",
     "../../demo/pages/m4-review.html"),
    ("a5", "A5 全渠道分发", "运营编辑", "#d4a514ff",
     "../../demo/pages/m5-channels.html"),
    ("a6", "A6 效果洞察", "数据分析师", "#1596a5ff",
     "../../demo/pages/m6-insights.html"),
]


class RenderSpecTests(unittest.TestCase):
    def test_sample_is_exactly_five_seconds(self):
        spec = RenderSpec()
        self.assertEqual(spec.fps, 24)
        self.assertEqual(spec.frame_start, 1)
        self.assertEqual(spec.frame_end, 120)
        self.assertEqual(spec.duration_seconds, 5.0)

    def test_sample_uses_hd_canvas(self):
        spec = RenderSpec()
        self.assertEqual((spec.width, spec.height), (1280, 720))

    def test_a1_role_contract(self):
        self.assertEqual(A1_ROLE["module"], "A1 智能选题")
        self.assertEqual(A1_ROLE["role"], "策划编辑")
        self.assertEqual(rgba_hex(A1_ROLE["color"]), "#c8102eff")

    def test_required_outputs_are_named(self):
        self.assertEqual(
            OUTPUT_NAMES,
            {
                "video": "sample.mp4",
                "cover": "sample-cover.png",
                "highlight": "sample-highlight.png",
            },
        )

    def test_six_desk_contract(self):
        actual = [
            (desk.id, desk.module, desk.role, rgba_hex(desk.color), desk.destination)
            for desk in DESKS
        ]
        self.assertEqual(actual, EXPECTED)
        self.assertEqual(validate_desks(DESKS), [])

    def test_each_desk_has_role_specific_action_and_props(self):
        self.assertEqual(
            [desk.action for desk in DESKS],
            [
                "查看热点屏、移动选题卡",
                "戴耳机、整理采访素材",
                "敲键盘、查看稿件",
                "标记文本、确认问题",
                "切换多块平台屏幕",
                "查看图表和传播信号",
            ],
        )
        self.assertTrue(all(len(desk.props) >= 2 for desk in DESKS))

    def test_newsroom_outputs_do_not_replace_sample_outputs(self):
        self.assertEqual(OUTPUT_NAMES["video"], "sample.mp4")
        self.assertEqual(NEWSROOM_OUTPUT_NAMES["video"], "newsroom.mp4")
        self.assertEqual(
            NEWSROOM_OUTPUT_NAMES["highlights"],
            {desk.id: f"newsroom-{desk.id}-highlight.png" for desk in DESKS},
        )


if __name__ == "__main__":
    unittest.main()
