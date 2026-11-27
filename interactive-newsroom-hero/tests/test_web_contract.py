import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class WebContractTests(unittest.TestCase):
    def test_static_document_has_completed_title_and_native_fallback_geometry(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        expected_points = (
            "395,217 304,300 386,314 471,229",
            "734,190 553,188 548,223 735,225",
            "970,297 856,220 785,238 896,318",
            "980,478 1065,375 974,350 883,448",
            "566,543 817,563 823,499 584,481",
            "278,398 403,493 491,455 363,365",
        )

        self.assertIn("<title>智媒编辑部 · 六工位互动新闻编辑部</title>", html)
        self.assertEqual(
            re.findall(r'<polygon\b[^>]*\bpoints="([^"]+)"', html),
            list(expected_points),
        )
        for points_text in expected_points:
            points = [
                tuple(map(int, point.split(",")))
                for point in points_text.split()
            ]
            twice_area = abs(sum(
                points[index][0] * points[(index + 1) % 4][1]
                - points[(index + 1) % 4][0] * points[index][1]
                for index in range(4)
            ))
            self.assertGreaterEqual(twice_area, 4000)

        app = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.assertNotIn('polygon.setAttribute("points"', app)

    def test_scene_contains_six_native_links_and_configured_destinations(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        config = (ROOT / "web/scene-data.js").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r'data-desk-id="a[1-6]"', html)), 6)
        for index, slug in enumerate(
            ("topics", "collection", "writing", "review", "channels", "insights"),
            start=1,
        ):
            destination = f"../../demo/pages/m{index}-{slug}.html"
            self.assertIn(destination, html)
            self.assertIn(destination, config)
            self.assertTrue((ROOT / "web" / destination).resolve().is_file())

    def test_each_hit_link_owns_a_polygon_and_highlight(self):
        html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        links = re.findall(
            r'<a\b[^>]*data-desk-id="(a[1-6])"[^>]*>([\s\S]*?)</a>',
            html,
        )
        self.assertEqual([desk_id for desk_id, _ in links], [
            f"a{index}" for index in range(1, 7)
        ])
        for index, (desk_id, contents) in enumerate(links, start=1):
            self.assertEqual(desk_id, f"a{index}")
            self.assertEqual(
                len(re.findall(
                    rf'<polygon\b[^>]*data-hit-id="{desk_id}"[^>]*>',
                    contents,
                )),
                1,
            )
            self.assertNotRegex(contents, r'data-hit-id="a(?!%d\b)[1-6]"' % index)
            self.assertIn(f'data-highlight-id="a{index}"', html)


if __name__ == "__main__":
    unittest.main()
