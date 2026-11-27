import subprocess
import sys
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

import verify_frame_content


ROOT = Path(__file__).parents[1]


class FrameContentValidationTests(unittest.TestCase):
    def test_rejects_frame_seventy_transient_response_panel(self):
        neighbor = Image.new("RGB", (100, 100), "white")
        leaked = neighbor.copy()
        ImageDraw.Draw(leaked).rectangle((30, 30, 69, 69), fill=(20, 30, 40))

        errors = verify_frame_content.validate_no_transient_motifs(
            neighbor, leaked, neighbor
        )

        self.assertTrue(any("response motif" in error for error in errors))
        self.assertEqual(
            verify_frame_content.validate_no_transient_motifs(
                neighbor, neighbor, neighbor
            ),
            [],
        )

    def test_requires_white_start_and_progressive_entry_content(self):
        frames = {}
        for frame, extent in ((1, 0), (5, 12), (10, 24), (15, 36), (20, 48)):
            image = Image.new("RGB", (100, 100), "white")
            if extent:
                ImageDraw.Draw(image).rectangle(
                    (10, 20, 10 + extent, 80), fill=(100, 100, 100)
                )
            frames[frame] = image

        self.assertEqual(verify_frame_content.validate_entry_progression(frames), [])

        invalid = dict(frames)
        invalid[1] = invalid[20]
        self.assertTrue(
            any(
                "frame 1 must begin in white space" in error
                for error in verify_frame_content.validate_entry_progression(invalid)
            )
        )

    def test_accepts_stable_idle_seam(self):
        idle = Image.new("RGB", (100, 100), (220, 220, 220))
        changed = idle.copy()
        changed.putpixel((50, 50), (219, 219, 219))

        self.assertEqual(
            verify_frame_content.validate_idle_seam(changed, idle, changed),
            [],
        )

    def test_current_generated_sequence_passes_frame_content_cli(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "src" / "verify_frame_content.py"),
                str(ROOT / "output" / "newsroom-frames"),
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("newsroom frame-content verification passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
