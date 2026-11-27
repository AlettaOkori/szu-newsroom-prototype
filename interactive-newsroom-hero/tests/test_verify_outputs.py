import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from scene_config import DESKS, NEWSROOM_OUTPUT_NAMES
from verify_outputs import (
    validate_cover,
    validate_highlight,
    validate_hit_regions,
    validate_newsroom,
    validate_newsroom_highlights,
    validate_probe,
)


def valid_probe():
    return {
        "streams": [{
            "codec_name": "h264",
            "pix_fmt": "yuv420p",
            "width": 1280,
            "height": 720,
            "r_frame_rate": "24/1",
            "nb_read_frames": "120",
        }],
        "format": {"duration": "5.000000"},
    }


def valid_regions():
    return {
        "viewBox": [0, 0, 1280, 720],
        "regions": {
            f"a{index}": [[100 * index, 100], [100 * index + 80, 105],
                         [100 * index + 70, 180], [100 * index - 5, 175]]
            for index in range(1, 7)
        },
    }


def valid_newsroom_image():
    image = Image.new("RGB", (1280, 720), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((200, 300, 229, 319), fill=(150, 150, 150))
    for index, desk in enumerate(DESKS):
        color = tuple(round(channel * 255) for channel in desk.color[:3])
        x = 300 + index * 20
        draw.rectangle((x, 300, x + 9, 309), fill=color)
    return image


def valid_highlights(regions=None):
    regions = regions or valid_regions()["regions"]
    images = {}
    for desk in DESKS:
        image = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        color = tuple(round(channel * 255) for channel in desk.color[:3]) + (255,)
        ImageDraw.Draw(image).polygon(regions[desk.id], fill=color)
        images[desk.id] = image
    return images


class ProbeValidationTests(unittest.TestCase):
    def test_accepts_expected_video(self):
        self.assertEqual(validate_probe(valid_probe()), [])

    def test_reports_wrong_duration_and_size(self):
        probe = {
            "streams": [{
                "codec_name": "h264",
                "pix_fmt": "yuv420p",
                "width": 640,
                "height": 360,
                "r_frame_rate": "30/1",
                "nb_read_frames": "120",
            }],
            "format": {"duration": "4.250000"},
        }
        errors = validate_probe(probe)
        self.assertIn("resolution must be 1280x720", errors)
        self.assertIn("frame rate must be 24 fps", errors)
        self.assertIn("duration must be 5.0 seconds", errors)

    def test_reports_wrong_codec_pixel_format_and_decoded_frame_count(self):
        probe = {
            "streams": [{
                "codec_name": "vp9",
                "pix_fmt": "yuv444p",
                "width": 1280,
                "height": 720,
                "r_frame_rate": "24/1",
                "nb_read_frames": "119",
            }],
            "format": {"duration": "5.000000"},
        }
        errors = validate_probe(probe)
        self.assertIn("codec must be h264", errors)
        self.assertIn("pixel format must be yuv420p", errors)
        self.assertIn("decoded frame count must be 120", errors)


class ImageValidationTests(unittest.TestCase):
    def test_highlight_requires_transparent_and_visible_pixels(self):
        transparent = Image.new("RGBA", (4, 4), (255, 0, 0, 0))
        opaque = Image.new("RGBA", (4, 4), (255, 0, 0, 255))
        self.assertIn(
            "highlight must contain visible pixels",
            validate_highlight(transparent),
        )
        self.assertIn(
            "highlight must contain transparent pixels",
            validate_highlight(opaque),
        )

    def test_cover_rejects_dark_background_and_missing_scene_evidence(self):
        image = Image.new("RGB", (1280, 720), (50, 50, 50))
        errors = validate_cover(image)
        self.assertIn("cover background samples must be near-white", errors)
        self.assertIn("cover must contain visible shadow pixels", errors)
        self.assertIn("cover must contain visible red clothing pixels", errors)

    def test_hit_regions_require_six_distinct_in_bounds_quads(self):
        valid = valid_regions()
        self.assertEqual(validate_hit_regions(valid), [])
        valid["regions"]["a6"] = valid["regions"]["a5"]
        self.assertIn(
            "hit-region polygons must be distinct",
            validate_hit_regions(valid),
        )

    def test_hit_regions_reject_wrong_order(self):
        payload = valid_regions()
        payload["regions"] = dict(reversed(payload["regions"].items()))
        self.assertIn(
            "hit regions must be ordered a1 through a6",
            validate_hit_regions(payload),
        )

    def test_hit_regions_reject_out_of_bounds_points(self):
        payload = valid_regions()
        payload["regions"]["a1"][0] = [1281, 100]
        self.assertIn(
            "a1 hit region must stay inside 1280x720",
            validate_hit_regions(payload),
        )

    def test_hit_regions_reject_too_small_polygons(self):
        payload = valid_regions()
        payload["regions"]["a1"] = [
            [100, 100], [110, 100], [110, 110], [100, 110],
        ]
        self.assertIn(
            "a1 hit region is too small",
            validate_hit_regions(payload),
        )

    def test_hit_regions_return_errors_for_malformed_types(self):
        malformed = [
            None,
            {"viewBox": [0, 0, 1280, 720], "regions": []},
            {
                **valid_regions(),
                "regions": {**valid_regions()["regions"], "a1": 7},
            },
            {
                **valid_regions(),
                "regions": {
                    **valid_regions()["regions"],
                    "a1": [[100, 100], ["bad", 105], [170, 180], [95, 175]],
                },
            },
        ]
        for payload in malformed:
            with self.subTest(payload=payload):
                errors = validate_hit_regions(payload)
                self.assertTrue(errors)

    def test_newsroom_highlights_require_all_six_rgba_assets(self):
        images = {
            f"a{index}": Image.new("RGBA", (1280, 720), (255, 255, 255, 0))
            for index in range(1, 7)
        }
        images["a1"].putpixel((10, 10), (200, 20, 40, 255))
        errors = validate_newsroom_highlights(images, valid_regions()["regions"])
        self.assertIn("a2 highlight must contain visible pixels", errors)
        self.assertNotIn("a1 highlight must contain visible pixels", errors)

    def test_newsroom_highlights_reject_duplicate_contents(self):
        images = valid_highlights()
        images["a2"] = images["a1"].copy()

        errors = validate_newsroom_highlights(images, valid_regions()["regions"])

        self.assertIn("highlight contents must be pairwise distinct", errors)

    def test_newsroom_highlights_ignore_rgb_hidden_beneath_zero_alpha(self):
        images = valid_highlights()
        images["a2"] = images["a1"].copy()
        images["a2"].putpixel((0, 0), (17, 31, 47, 0))

        errors = validate_newsroom_highlights(images, valid_regions()["regions"])

        self.assertIn("highlight contents must be pairwise distinct", errors)

    def test_newsroom_highlights_reject_swapped_ids_and_clothing_colors(self):
        images = valid_highlights()
        images["a1"], images["a2"] = images["a2"], images["a1"]

        errors = validate_newsroom_highlights(images, valid_regions()["regions"])

        self.assertIn("a1 highlight must contain configured clothing-color evidence", errors)
        self.assertIn("a2 highlight must contain configured clothing-color evidence", errors)

    def test_newsroom_highlights_reject_displaced_alpha_and_centroid(self):
        images = valid_highlights()
        displaced = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        color = tuple(round(channel * 255) for channel in DESKS[0].color[:3]) + (255,)
        ImageDraw.Draw(displaced).rectangle((900, 500, 1000, 600), fill=color)
        images["a1"] = displaced

        errors = validate_newsroom_highlights(images, valid_regions()["regions"])

        self.assertIn("a1 highlight must substantially cover its projected desk polygon", errors)
        self.assertIn("a1 highlight must be visible and opaque at its desk centroid", errors)


class NewsroomValidationTests(unittest.TestCase):
    def write_valid_outputs(self, root: Path, preview: bool = True):
        (root / NEWSROOM_OUTPUT_NAMES["video"]).write_bytes(b"probe is mocked")
        image = valid_newsroom_image()
        image.save(root / NEWSROOM_OUTPUT_NAMES["cover"])
        regions = valid_regions()
        for desk_id, highlight in valid_highlights(regions["regions"]).items():
            highlight.save(root / NEWSROOM_OUTPUT_NAMES["highlights"][desk_id])
        (root / NEWSROOM_OUTPUT_NAMES["hit_regions"]).write_text(
            json.dumps(regions),
            encoding="utf-8",
        )
        frame_dir = root / ("newsroom-preview" if preview else "newsroom-frames")
        frame_dir.mkdir()
        for frame_number in (1, 21, 70, 120):
            image.save(frame_dir / f"frame_{frame_number:04d}.png")

    def test_default_never_uses_preserved_sample_frames(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sample_frames = root / "frames"
            sample_frames.mkdir()
            image = valid_newsroom_image()
            for frame_number in (1, 21, 70, 120):
                image.save(sample_frames / f"frame_{frame_number:04d}.png")

            errors = validate_newsroom(root)

        self.assertIn(
            "newsroom-frames/frame_0001.png: missing representative frame",
            errors,
        )

    @patch("verify_outputs.probe_video", return_value=valid_probe())
    def test_preview_validation_integrates_all_artifacts(self, _probe):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_outputs(root)

            errors = validate_newsroom(root, preview=True)

        self.assertEqual(errors, [])

    def test_preview_validation_does_not_require_encoded_video(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_outputs(root)
            (root / NEWSROOM_OUTPUT_NAMES["video"]).unlink()

            errors = validate_newsroom(root, preview=True)

        self.assertEqual(errors, [])

    def test_missing_outputs_have_artifact_prefixes(self):
        with tempfile.TemporaryDirectory() as directory:
            errors = validate_newsroom(Path(directory), preview=True)

        self.assertNotIn("newsroom.mp4: missing output", errors)
        self.assertIn("newsroom-cover.png: missing output", errors)
        self.assertIn("a1: missing highlight", errors)
        self.assertIn("newsroom-hit-regions.json: missing output", errors)
        self.assertIn(
            "newsroom-preview/frame_0001.png: missing representative frame",
            errors,
        )

    def test_newsroom_cli_selects_complete_scene_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parents[1] / "src" / "verify_outputs.py"),
                    directory,
                    "--newsroom",
                ],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("newsroom.mp4: missing output", result.stderr)
        self.assertNotIn("missing output: sample.mp4", result.stderr)

    def test_newsroom_preview_cli_selects_preview_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_outputs(root)
            (root / NEWSROOM_OUTPUT_NAMES["video"]).unlink()
            result = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).parents[1] / "src" / "verify_outputs.py"),
                    directory,
                    "--newsroom",
                    "--preview",
                ],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("newsroom preview verification passed", result.stdout)

    @patch("verify_outputs.probe_video")
    def test_validation_prefixes_video_cover_and_highlight_errors(self, probe):
        invalid_probe = valid_probe()
        invalid_probe["streams"][0]["codec_name"] = "vp9"
        probe.return_value = invalid_probe
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_outputs(root, preview=False)
            Image.new("RGB", (1280, 720), (30, 30, 30)).save(
                root / NEWSROOM_OUTPUT_NAMES["cover"]
            )
            Image.new("RGB", (1280, 720), (255, 255, 255)).save(
                root / NEWSROOM_OUTPUT_NAMES["highlights"]["a1"]
            )

            errors = validate_newsroom(root)

        self.assertIn("newsroom.mp4: codec must be h264", errors)
        self.assertIn(
            "newsroom-cover.png: background samples must be near-white",
            errors,
        )
        self.assertIn("a1 highlight must be 1280x720 RGBA", errors)


if __name__ == "__main__":
    unittest.main()
