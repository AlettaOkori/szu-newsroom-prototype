# Interactive Newsroom Hero

This isolated prototype includes the approved A1 sample pipeline and a
render-cost-aware pipeline for the complete six-desk newsroom.

## Requirements

- Windows 10 or later
- Python 3.11+
- Blender with Eevee (tested with Blender 5.2.0 LTS; the scene script detects the
  `BLENDER_EEVEE_NEXT` and `BLENDER_EEVEE` runtime identifiers)
- FFmpeg and FFprobe (tested with 8.1.1)
- Pillow for Python
- Node.js with built-in `fetch` and `WebSocket` (tested with 24.14.1)
- Microsoft Edge for the browser smoke test

## Approved sample render

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-sample.ps1
```

`scripts/render-sample.ps1` remains the approved sample command. It renders and
verifies:

- `output/frames/frame_0001.png` through `frame_0120.png`
- `output/sample.mp4`
- `output/sample-cover.png`
- `output/sample-highlight.png`
- `output/sample.blend`

The MP4, cover, and highlight are synchronized to `web/assets/`.

## Six-desk render cost controls

Blender 5.2.0 LTS is installed and is the tested complete-scene renderer.
Always run the mandatory preview before authorizing a full render:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -PreviewOnly
```

Preview renders only four base frames plus seven stills (one cover and six
highlights). It also generates the projection JSON, `web/scene-data.js`, and
`output/newsroom.blend`; it does not encode an MP4. A successful run ends with
`NEWSROOM_PREVIEW_COMPLETE`.

The full command is intentionally expensive:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1
```

It renders 120 base frames plus seven stills, encodes and verifies
`output/newsroom.mp4`, and synchronizes the video, cover, and six highlights to
`web/assets/`. A successful run ends with `NEWSROOM_PIPELINE_COMPLETE`.

After one successful complete 120-frame render, use `-SkipRender` for
encoding, verifier, and browser iteration without paying the Blender frame
render cost again:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -SkipRender
```

The complete-scene outputs are:

- `output/newsroom-frames/frame_0001.png` through `frame_0120.png`
- `output/newsroom.mp4`
- `output/newsroom-cover.png`
- `output/newsroom-a1-highlight.png` through `newsroom-a6-highlight.png`
- `output/newsroom-hit-regions.json`
- `output/newsroom.blend`
- `web/scene-data.js`

The six desk destinations are:

- `demo/pages/m1-topics.html`
- `demo/pages/m2-collection.html`
- `demo/pages/m3-writing.html`
- `demo/pages/m4-review.html`
- `demo/pages/m5-channels.html`
- `demo/pages/m6-insights.html`

## Browser preview

From this project directory, serve the parent directory so both the viewer and
all six existing destinations are available:

```powershell
python -m http.server 4173 --directory ..
```

Open `http://localhost:4173/interactive-newsroom-hero/web/`.

## Completion Gate checks

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
python src/verify_outputs.py output --newsroom --preview
python src/verify_outputs.py output
python src/verify_outputs.py output --newsroom
node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
node .superpowers/sdd/task4-browser-smoke.mjs
```

After the final full render, run the direct media probe:

```powershell
ffprobe -v error -count_frames -select_streams v:0 `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames:format=duration `
  -of json output/newsroom.mp4
```

Run both browser smoke commands while the parent-directory preview server is
running:

```powershell
$env:EDGE_EXECUTABLE = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$env:EDGE_DEBUG_PORT = "9333"
node .superpowers/sdd/task4-browser-smoke.mjs
$env:EDGE_DEBUG_PORT = "9334"
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Run complete-scene verification only after a full render or a `-SkipRender`
iteration. Run the browser smoke command while the preview server is running.

## Final six-desk acceptance

The fresh complete pipeline was accepted on 2026-07-19. It produced the
five-second H.264/yuv420p newsroom video, cover, Blend source, projected hit
regions, six transparent highlights, generated browser configuration, and
hash-matched web assets. The final run ended with
`NEWSROOM_PIPELINE_COMPLETE`.

Final automated commands:

```powershell
python -m unittest discover -s tests -v
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py src/verify_frame_content.py
python src/verify_outputs.py output
python src/verify_outputs.py output --newsroom
python src/verify_frame_content.py output/newsroom-frames
node --check web/scene-data.js
node --check web/app.js
node --check web/sample/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames:format=duration -of json output/newsroom.mp4
$env:EDGE_DEBUG_PORT = "9333"
node .superpowers/sdd/task4-browser-smoke.mjs
$env:EDGE_DEBUG_PORT = "9334"
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Automated checks passed. Visual review confirmed all six unified role figures,
role colors and props, stable idle endpoints, aligned non-overlapping hit
regions and highlights, restrained miniature lighting, readable opposite-side
cards, and working six-destination navigation and fallback behavior. The
preserved one-desk regression viewer is available at `web/sample/`.

The post-review production repair did not run the full renderer again. It used
the bounded commands below, followed by the documented `-SkipRender` encode:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -RepairFrames "1-20,70"
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -ArtifactsOnly
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -SkipRender
python src/verify_frame_content.py output/newsroom-frames
```

`-RepairFrames` overwrites only the explicitly selected base frames.
`-ArtifactsOnly` regenerates the cover, six highlights, hit-region JSON, Blend
source, and generated browser configuration without rendering any base frame.
