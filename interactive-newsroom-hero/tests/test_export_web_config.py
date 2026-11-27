import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))

from export_web_config import (
    build_web_config,
    load_hit_regions,
    write_web_config,
)


class WebConfigExportTests(unittest.TestCase):
    def test_load_hit_regions_returns_validated_regions(self):
        path = ROOT / "output" / "newsroom-hit-regions.json"
        payload = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(load_hit_regions(path), payload["regions"])

    def test_load_hit_regions_rejects_invalid_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "regions.json"
            path.write_text(
                json.dumps({"viewBox": [0, 0, 640, 360], "regions": {}}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "viewBox"):
                load_hit_regions(path)

    def test_generated_config_is_deterministic_and_matches_projection(self):
        projection_path = ROOT / "output" / "newsroom-hit-regions.json"
        regions = load_hit_regions(projection_path)
        records = build_web_config(regions)

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.js"
            second = Path(directory) / "second.js"
            write_web_config(first, records)
            write_web_config(second, records)
            first_text = first.read_text(encoding="utf-8")
            second_text = second.read_text(encoding="utf-8")

        self.assertEqual(first_text, second_text)
        self.assertEqual(
            [record["points"] for record in records],
            [
                " ".join(f"{x},{y}" for x, y in regions[record["id"]])
                for record in records
            ],
        )
        self.assertEqual(
            first_text,
            (ROOT / "web" / "scene-data.js").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
