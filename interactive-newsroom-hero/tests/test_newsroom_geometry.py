import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from build_newsroom import (
    entry_window,
    parse_frame_selection,
    project_quad,
    role_emission,
    role_render_color,
)
from scene_config import DESKS, rgba_hex


class NewsroomGeometryTests(unittest.TestCase):
    def test_a2_render_material_compensates_without_changing_config_color(self):
        desk = next(desk for desk in DESKS if desk.id == "a2")
        render_color = role_render_color(desk)

        self.assertEqual(rgba_hex(desk.color), "#e87524ff")
        self.assertGreater(render_color[0], desk.color[0])
        self.assertLess(render_color[1], desk.color[1])
        self.assertLess(render_color[2], desk.color[2])
        self.assertEqual(render_color[2], 0.0)
        self.assertEqual(render_color[3], desk.color[3])
        emission = role_emission(desk)
        self.assertGreater(emission[0], emission[1] * 4)
        self.assertEqual(emission[2], 0.0)
        self.assertEqual(emission[3], 1.0)
        self.assertTrue(all(
            role_emission(other) is None
            for other in DESKS
            if other.id != "a2"
        ))

    def test_project_quad_rounds_four_camera_points(self):
        projected = iter(((0.25, 0.75), (0.50, 0.75), (0.55, 0.40), (0.20, 0.40)))
        self.assertEqual(
            project_quad(lambda _corner: next(projected), range(4)),
            [[320, 180], [640, 180], [704, 432], [256, 432]],
        )

    def test_project_quad_rejects_off_canvas_points(self):
        with self.assertRaisesRegex(ValueError, "outside the 1280x720 canvas"):
            project_quad(lambda _corner: (-0.01, 0.5), range(4))

    def test_repair_frame_selection_accepts_only_bounded_unique_frames(self):
        self.assertEqual(
            parse_frame_selection("1-20,70"),
            tuple(range(1, 21)) + (70,),
        )
        with self.assertRaisesRegex(ValueError, "frame selection"):
            parse_frame_selection("20-1")
        with self.assertRaisesRegex(ValueError, "frame selection"):
            parse_frame_selection("0,121")

    def test_entry_windows_stage_three_desk_pairs_before_frame_twenty(self):
        self.assertEqual(entry_window("a2"), (2, 8))
        self.assertEqual(entry_window("a5"), (2, 8))
        self.assertEqual(entry_window("a1"), (7, 13))
        self.assertEqual(entry_window("a4"), (7, 13))
        self.assertEqual(entry_window("a3"), (12, 18))
        self.assertEqual(entry_window("a6"), (12, 18))


if __name__ == "__main__":
    unittest.main()
