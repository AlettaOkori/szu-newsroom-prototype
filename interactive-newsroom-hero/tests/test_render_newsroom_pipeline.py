import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render-newsroom.ps1"


class RenderNewsroomPipelineTests(unittest.TestCase):
    def fake_blender_environment(self, root: Path, behavior: str):
        runner = root / "fake-blender.py"
        log = root / "fake-blender.log"
        runner.write_text(
            "\n".join([
                "import os",
                "import sys",
                "from pathlib import Path",
                "Path(os.environ['FAKE_BLENDER_LOG']).write_text(",
                "    'FAKE_BLENDER_RUNNER_INVOKED\\n' + ' '.join(sys.argv),",
                "    encoding='utf-8',",
                ")",
                "print('FAKE_BLENDER_RUNNER_INVOKED')",
                "separator = sys.argv.index('--')",
                "output = Path(sys.argv[separator + 1])",
                "mode = sys.argv[sys.argv.index('--mode') + 1]",
                "behavior = os.environ['FAKE_BLENDER_BEHAVIOR']",
                "if behavior in {'preview-success', 'preview-traceback'}:",
                "    preview = output / 'newsroom-preview'",
                "    preview.mkdir(parents=True, exist_ok=True)",
                "    for frame in (1, 21, 70, 120):",
                "        (preview / f'frame_{frame:04d}.png').write_bytes(b'fake frame')",
                "if behavior == 'preview-success':",
                "    for name in ['newsroom-cover.png', 'newsroom-hit-regions.json',",
                "                 'newsroom.blend'] + [",
                "        f'newsroom-a{i}-highlight.png' for i in range(1, 7)",
                "    ]:",
                "        (output / name).write_bytes(b'fake artifact')",
                "if behavior == 'preview-traceback':",
                "    print('Traceback (most recent call last): intentional fake failure')",
                "    raise SystemExit(1)",
                "if behavior not in {'preview-success', 'no-write'}:",
                "    raise SystemExit(f'unknown fake behavior: {behavior}')",
                "print(f'FAKE_BLENDER_{mode.upper()}_COMPLETE')",
            ]) + "\n",
            encoding="utf-8",
        )
        trap = (
            root / "program-files" / "Blender Foundation"
            / "Blender Trap" / "blender.exe"
        )
        trap.parent.mkdir(parents=True, exist_ok=True)
        trap.write_bytes(b"installed Blender trap must never execute")
        return {
            **os.environ,
            "BLENDER_EXECUTABLE": str(runner),
            "FAKE_BLENDER_BEHAVIOR": behavior,
            "FAKE_BLENDER_LOG": str(log),
            "ProgramFiles": str(root / "program-files"),
            "PYTHONIOENCODING": "utf-8",
        }, log

    def make_stub_project(self, root: Path):
        scripts = root / "scripts"
        source = root / "src"
        output = root / "output"
        frames = output / "newsroom-frames"
        web = root / "web"
        scripts.mkdir()
        source.mkdir()
        frames.mkdir(parents=True)
        web.mkdir()
        shutil.copy2(SCRIPT, scripts / SCRIPT.name)
        (source / "build_newsroom.py").write_text(
            "print('stub blender completed without writing outputs')\n",
            encoding="utf-8",
        )
        (source / "export_web_config.py").write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "Path(sys.argv[2]).write_text('window.NEWSROOM_DESKS = [];\\n')\n",
            encoding="utf-8",
        )
        for frame_number in range(1, 121):
            (frames / f"frame_{frame_number:04d}.png").write_bytes(b"stale frame")
        artifacts = [
            output / "newsroom-cover.png",
            output / "newsroom-hit-regions.json",
            output / "newsroom.blend",
            output / "newsroom.blend1",
            web / "scene-data.js",
        ] + [
            output / f"newsroom-a{index}-highlight.png"
            for index in range(1, 7)
        ]
        for artifact in artifacts:
            artifact.write_bytes(b"stale artifact")
        return scripts / SCRIPT.name, frames, artifacts

    def test_pipeline_contract_is_present(self):
        script = SCRIPT.read_text(encoding="utf-8")

        for required in (
            "[switch]$PreviewOnly",
            "[switch]$SkipRender",
            "[string]$RepairFrames",
            "[switch]$ArtifactsOnly",
            "PreviewOnly and SkipRender cannot be combined.",
            "RepairFrames cannot be combined with PreviewOnly or SkipRender.",
            "$env:BLENDER_EXECUTABLE",
            "--python-exit-code 1",
            r"Traceback \(most recent call last\)",
            'Invoke-Blender "preview"',
            'Invoke-Blender "full"',
            'Invoke-Blender "repair" $RepairFrames',
            'Invoke-Blender "artifacts"',
            "frame_%04d.png",
            "-c:v libx264",
            "-preset slow",
            "-crf 18",
            "-pix_fmt yuv420p",
            "-movflags +faststart",
            "src\\verify_outputs.py",
            "--newsroom",
            "src\\verify_frame_content.py",
            "Get-FileHash",
            "Remove-Item -Path $blend, $blendBackup, $sceneData",
            "NEWSROOM_PREVIEW_COMPLETE",
            "NEWSROOM_PIPELINE_COMPLETE",
        ):
            with self.subTest(required=required):
                self.assertIn(required, script)

    def test_failing_frame_content_gate_prevents_success_sentinel(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script, _, _ = self.make_stub_project(root)
            output = root / "output"
            (output / "newsroom.mp4").write_bytes(b"stale video")
            commands = root / "commands"
            commands.mkdir()
            for name in ("ffmpeg", "ffprobe", "node"):
                (commands / f"{name}.cmd").write_text(
                    "@echo off\r\nexit /b 0\r\n",
                    encoding="ascii",
                )
            (commands / "python.cmd").write_text(
                "@echo off\r\n"
                "echo %* | findstr /C:\"verify_frame_content.py\" >nul\r\n"
                "if %errorlevel%==0 (\r\n"
                "  echo intentional frame-content failure 1>&2\r\n"
                "  exit /b 9\r\n"
                ")\r\n"
                "exit /b 0\r\n",
                encoding="ascii",
            )
            environment, _ = self.fake_blender_environment(root, "no-write")
            environment = {
                **environment,
                "PATH": str(commands) + os.pathsep + os.environ["PATH"],
            }

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-SkipRender",
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )

        output_text = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("intentional frame-content failure", output_text)
        self.assertNotIn("NEWSROOM_PIPELINE_COMPLETE", output_text)

    def test_repair_deletes_only_requested_frames_before_blender(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script, frames, _ = self.make_stub_project(root)
            environment, _ = self.fake_blender_environment(root, "no-write")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-RepairFrames",
                    "5,70",
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((frames / "frame_0005.png").exists())
            self.assertFalse((frames / "frame_0070.png").exists())
            self.assertEqual(
                (frames / "frame_0006.png").read_bytes(),
                b"stale frame",
            )

    def test_artifacts_mode_rejects_stale_outputs_when_blender_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script, frames, artifacts = self.make_stub_project(root)
            environment, _ = self.fake_blender_environment(root, "no-write")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-ArtifactsOnly",
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(all(not artifact.exists() for artifact in artifacts))
            self.assertEqual(
                (frames / "frame_0001.png").read_bytes(),
                b"stale frame",
            )

    def test_preview_uses_fake_blender_override_not_installed_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script, _, _ = self.make_stub_project(root)
            environment, log = self.fake_blender_environment(
                root,
                "preview-success",
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                    "-PreviewOnly",
                ],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )

            output_text = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output_text)
            self.assertIn("FAKE_BLENDER_RUNNER_INVOKED", output_text)
            self.assertIn("NEWSROOM_PREVIEW_COMPLETE", output_text)
            self.assertIn("FAKE_BLENDER_RUNNER_INVOKED", log.read_text())
            self.assertNotIn("Blender Foundation", log.read_text())

    def test_mutually_exclusive_modes_fail_before_dependency_checks(self):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPT),
                "-PreviewOnly",
                "-SkipRender",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "PreviewOnly and SkipRender cannot be combined.",
            result.stdout + result.stderr,
        )

    def test_repair_mode_is_mutually_exclusive_before_dependency_checks(self):
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPT),
                "-PreviewOnly",
                "-RepairFrames",
                "1-20,70",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "RepairFrames cannot be combined with PreviewOnly or SkipRender.",
            result.stdout + result.stderr,
        )

    def test_ignore_rules_cover_only_newsroom_generated_assets(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

        self.assertTrue({
            "output/newsroom-frames/",
            "output/newsroom-preview/",
            "output/newsroom-*",
            "web/assets/newsroom-*",
        }.issubset(rules))
        self.assertIn("output/frames/", rules)
        self.assertIn("output/newsroom.blend1", rules)

    def test_blender_traceback_fails_without_accepting_stale_preview_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scripts = root / "scripts"
            source = root / "src"
            output = root / "output"
            preview = output / "newsroom-preview"
            sample_frames = output / "frames"
            web = root / "web"
            scripts.mkdir()
            source.mkdir()
            preview.mkdir(parents=True)
            sample_frames.mkdir()
            web.mkdir()
            shutil.copy2(SCRIPT, scripts / SCRIPT.name)
            (source / "build_newsroom.py").write_text(
                "\n".join([
                    "import sys",
                    "from pathlib import Path",
                    "args = sys.argv[sys.argv.index('--') + 1:]",
                    "output = Path(args[0])",
                    "preview = output / 'newsroom-preview'",
                    "preview.mkdir(parents=True, exist_ok=True)",
                    "for frame in (1, 21, 70, 120):",
                    "    (preview / f'frame_{frame:04d}.png').write_bytes(b'new')",
                    "raise RuntimeError('intentional pipeline test failure')",
                ]),
                encoding="utf-8",
            )
            (source / "export_web_config.py").write_text(
                "from pathlib import Path\n"
                "import sys\n"
                "Path(sys.argv[2]).write_text('window.NEWSROOM_DESKS = [];\\n')\n",
                encoding="utf-8",
            )
            stale = [
                output / "newsroom-cover.png",
                output / "newsroom-hit-regions.json",
                output / "newsroom.blend",
                output / "newsroom.blend1",
                web / "scene-data.js",
            ] + [
                output / f"newsroom-a{index}-highlight.png"
                for index in range(1, 7)
            ]
            for path in stale:
                path.write_bytes(b"stale")
            sample = output / "sample.mp4"
            sample.write_bytes(b"preserve sample")
            sample_frame = sample_frames / "frame_0001.png"
            sample_frame.write_bytes(b"preserve frame")

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(scripts / SCRIPT.name),
                    "-PreviewOnly",
                ],
                cwd=root,
                env=self.fake_blender_environment(
                    root,
                    "preview-traceback",
                )[0],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=30,
            )

            output_text = result.stdout + result.stderr
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Traceback", output_text)
            self.assertNotIn("NEWSROOM_PREVIEW_COMPLETE", output_text)
            self.assertTrue(all(not path.exists() for path in stale))
            self.assertEqual(sample.read_bytes(), b"preserve sample")
            self.assertEqual(sample_frame.read_bytes(), b"preserve frame")

    def test_readme_documents_cost_controls_and_destinations(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for required in (
            "scripts/render-sample.ps1",
            "Blender 5.2.0 LTS",
            "scripts/render-newsroom.ps1 -PreviewOnly",
            "four base frames plus seven stills",
            "120 base frames plus seven stills",
            "-SkipRender",
            "m1-topics.html",
            "m2-collection.html",
            "m3-writing.html",
            "m4-review.html",
            "m5-channels.html",
            "m6-insights.html",
            (
                "python -m py_compile src/scene_config.py src/build_scene.py "
                "src/build_newsroom.py src/export_web_config.py "
                "src/verify_outputs.py"
            ),
            "node --check .superpowers/sdd/six-desk-browser-smoke.mjs",
            "node .superpowers/sdd/six-desk-browser-smoke.mjs",
            "ffprobe -v error -count_frames -select_streams v:0",
            (
                "-show_entries stream=codec_name,pix_fmt,width,height,"
                "r_frame_rate,nb_read_frames:format=duration"
            ),
            "-of json output/newsroom.mp4",
        ):
            with self.subTest(required=required):
                self.assertIn(required, readme)


if __name__ == "__main__":
    unittest.main()
