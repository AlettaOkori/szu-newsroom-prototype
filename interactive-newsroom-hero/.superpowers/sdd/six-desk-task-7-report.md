# Six-Desk Newsroom — Task 7 Completion Report

## Result

**DONE**

The mandatory preview passed before the reserved complete render. The expensive
pipeline was then run exactly once and ended with
`NEWSROOM_PIPELINE_COMPLETE`. A later production review correctly rejected the
original visual acceptance because frame 70 leaked hover-response motifs, the
entry did not stage desk visibility, and reduced-motion loaded response
highlights. The authoritative repair evidence appended below supersedes those
original visual claims and records the corrected passing gate.

No Git repository was initialized and no commit was created.

## Expensive-render accounting

The complete Blender render command was invoked exactly once:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1
```

Elapsed: **711.798 seconds**. It produced 120 contiguous base frames, one cover,
six highlights, the Blend source, projected hit-region JSON, generated browser
configuration, H.264 MP4, synchronized web assets, verifier success, and the
final sentinel:

```text
newsroom media verification passed
NEWSROOM_PIPELINE_COMPLETE
```

No second full render was run. The later correction used only bounded partial
frame repair, artifacts-only regeneration, and `-SkipRender` re-encoding.

## Commands and elapsed times

### Preserved sample baseline

```powershell
Get-FileHash output/sample.mp4, output/sample-cover.png,
  output/sample-highlight.png, output/sample.blend -Algorithm SHA256
Get-ChildItem output/frames -Filter frame_*.png -File
```

Elapsed: **0.087 seconds**. All four files existed and the preserved sample
frame count was 120.

### Preflight

```powershell
python -m unittest discover -s tests -v
```

Elapsed: **62.439 seconds**; 38 tests passed.

```powershell
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
```

Elapsed, respectively: **0.133, 0.072, 0.058, 0.058, and 0.055
seconds**. Every command exited 0 without syntax output.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -PreviewOnly
```

Elapsed: **70.731 seconds**. Four preview base frames and seven stills were
rendered, configuration was generated, and output ended with
`NEWSROOM_PREVIEW_COMPLETE`.

### Post-render media and regression checks

```powershell
python -m unittest discover -s tests -v
```

Elapsed: **69.022 seconds**; 38 tests passed.

```powershell
python src/verify_outputs.py output
python src/verify_outputs.py output --newsroom
```

Elapsed: **2.015 and 14.142 seconds**. Results:

```text
media verification passed
newsroom media verification passed
```

```powershell
ffprobe -v error -count_frames -select_streams v:0 `
  -show_entries stream=codec_name,pix_fmt,width,height,r_frame_rate,nb_read_frames:format=duration `
  -of json output/newsroom.mp4
```

Elapsed: **0.134 seconds**. FFprobe returned H.264, yuv420p, 1280×720,
24/1 fps, 120 decoded frames, and 5.000000 seconds.

```powershell
python -m py_compile src/scene_config.py src/build_scene.py src/build_newsroom.py src/export_web_config.py src/verify_outputs.py
node --check web/scene-data.js
node --check web/app.js
node --check .superpowers/sdd/task4-browser-smoke.mjs
node --check .superpowers/sdd/six-desk-browser-smoke.mjs
```

Post-render elapsed, respectively: **0.123, 0.051, 0.044, 0.046, and
0.047 seconds**. All exited 0. IDE diagnostics reported no lint errors.

### Browser checks

The already-running required server responded with HTTP 200:

```powershell
python -m http.server 4173 --directory ..
```

The first legacy smoke attempt correctly failed in **1.188 seconds** because
the six-desk expansion had replaced the only route expected by the preserved
one-desk harness. The failure was not accepted or hidden.

The approved one-desk viewer was restored at `web/sample/`; only the harness
URL changed, while all original behavioral assertions remained unchanged.
No generated media or render source was touched. Then:

```powershell
$env:EDGE_EXECUTABLE = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
$env:EDGE_DEBUG_PORT = "9333"
node .superpowers/sdd/task4-browser-smoke.mjs
```

Elapsed: **8.879 seconds**. It passed native-link semantics, accessibility
visibility, 1280×720/5-second media, natural loop, color evidence, hover,
100 ms highlight transition, exact card copy, keyboard/Escape, two-tap touch,
A1 navigation, blocked-MP4 fallback, reduced motion, autoplay recovery, and
the 20/24-second restart.

```powershell
$env:EDGE_DEBUG_PORT = "9334"
node .superpowers/sdd/six-desk-browser-smoke.mjs
```

Elapsed: **24.074 seconds**. All 15 PASS lines were emitted, covering six
distinct native links, exact card/color state within 100 ms, one-at-a-time
selection, all keyboard and real-touch destinations, video and individual
highlight failures, reduced motion, low performance, missing target, autoplay
recovery, natural playback, and media dimensions/duration.

## Output inventory and SHA-256

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `output/newsroom.mp4` | 354378 | `F37148B28647F0DFFA165102966AE2E629B215580030C2D9A5681AA672B8B7C9` |
| `output/newsroom-cover.png` | 1040909 | `839FF4205D743FEE1FA4D98A21CC8F629E47168684236CD00360C49B7819CFC0` |
| `output/newsroom.blend` | 307545 | `E2CBAA580C0860669F7D90A2A9AA701482C7A3F18233124816F5ADD4FF2D792B` |
| `output/newsroom-hit-regions.json` | 1307 | `D441A679070D3F7FE26241E0BD7855439C6B8885B2DE85F978580B9AA428221F` |
| `output/newsroom-a1-highlight.png` | 290431 | `36BE38580C66D5139E0FE6625BEED126416659257BC450A488894BFA8DC79539` |
| `output/newsroom-a2-highlight.png` | 264990 | `A84A266AE873295F94EA52EEF376BC1C8F0AA5AE254055C37D0E0C40284B066F` |
| `output/newsroom-a3-highlight.png` | 282000 | `628BA084AC4F00672ECA96CF0CD4077D7AB55C2A6E2C954DDAA196E0AC1FB46C` |
| `output/newsroom-a4-highlight.png` | 307946 | `012EEF1B27F84DF6F111412AF79556346DEC3E98002076A8AFD83D7B3FAA5872` |
| `output/newsroom-a5-highlight.png` | 327443 | `9CC3E8D2F1E65F823324B8BCA82EA181EF27E554730068A243E98F52E4252783` |
| `output/newsroom-a6-highlight.png` | 308627 | `03FF8F76BC932C87A6D1076C4EC6168C1F15CD1B9A1A31951A475F1C019F9EF3` |
| `web/scene-data.js` | 3058 | `1330A00B42D22F5BAB3C117A6957DEEA3A3F1F3D95CFACAF75E775D5772A43B4` |

The newsroom base-frame directory contains exactly 120 files. Each MP4,
cover, and highlight output hash exactly matches its corresponding
`web/assets` hash.

## Programmatic image evidence

All six highlights are 1280×720 RGBA with alpha extrema 0–255. Their visible
pixel counts are 30,599; 25,296; 29,991; 38,889; 52,184; and 40,662.

Projected desktop-region coverage by the matching highlight:

- A1: 7,849 / 7,878 pixels; centroid alpha 255
- A2: 6,417 / 6,481 pixels; centroid alpha 255
- A3: 7,941 / 7,983 pixels; centroid alpha 255
- A4: 11,865 / 11,992 pixels; centroid alpha 255
- A5: 15,642 / 15,744 pixels; centroid alpha 255
- A6: 12,388 / 12,621 pixels; centroid alpha 255

Every pairwise hit-region intersection was zero pixels. This confirms distinct
desktop ownership and no obvious cross-activation area.

The idle loop comparison between frames 21 and 120 differed by only two pixels
out of 921,600, with zero rounded mean absolute RGB and luminance difference.
This supports the observed seamless 20/24-second restart. Frame 1 intentionally
differs because it is the entry-camera pose.

## Visual acceptance checklist

Representative entry, idle-start, mid-idle, endpoint, cover, and all six
transparent highlights were inspected.

1. **Entry and seam:** PASS. Entry moves from a wider diagonal composition to
   the stable idle camera. Idle start and endpoint show no camera jump or
   brightness flash.
2. **Unified figures:** PASS. Six visible characters use the same rounded,
   faceless miniature role shape and remain readable throughout.
3. **Roles, colors, actions, props:** PASS. A1 red has trend screen/cards; A2
   orange has headphones/interview material; A3 green has keyboard/manuscript
   screen; A4 magenta has annotation pen/issue screen; A5 yellow has multiple
   platform screens/publish control; A6 cyan has chart screen/signal columns.
4. **Desktop perspective and boundaries:** PASS. Each four-point quad follows
   its own visible desktop; zero pairwise pixel overlap was measured.
5. **Highlight alignment and feedback:** PASS. Each isolated highlight follows
   its base figure, desk, screen, props, and colored floor ring. Browser
   activation passed within 100 ms.
6. **Cards:** PASS. Configured sides are right for A1/A2/A6 and left for
   A3/A4/A5; smoke verified exact card state and the visual layout keeps cards
   opposite the selected role.
7. **Physical input:** PASS. Real CDP touch required selection then navigation;
   keyboard focus, Enter, and Escape passed for all desks.
8. **Playback and constrained modes:** PASS. Normal playback completed
   naturally; reduced-motion and two-core low-performance modes stayed fully
   navigable.
9. **Failure modes:** PASS. Blocked main video, blocked A3 highlight, autoplay
   rejection, and missing A6 target each produced the specified isolated
   fallback without disabling other desks.
10. **Originality and preservation:** PASS. The scene uses the approved
    project-specific miniature newsroom language; no copied Marvis visual or
    source element was observed.

## Sample preservation

Before and after Task 7, the preserved sample values were:

| Artifact | SHA-256 |
|---|---|
| `output/sample.mp4` | `F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB` |
| `output/sample-cover.png` | `2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8` |
| `output/sample-highlight.png` | `EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46` |
| `output/sample.blend` | `ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627` |

All hashes match the baseline and all 120 preserved sample frames remain.
The approved `scripts/render-sample.ps1` command remains documented and
reproducible. The restored one-desk web regression uses those unchanged assets.

## Concerns

- Blender 5.2 emits deprecation warnings for `World.use_nodes` and
  `Material.use_nodes`, which are scheduled for removal in Blender 6.0. They do
  not affect Blender 5.2 output or this gate.
- The legacy smoke needed a route-only correction because the six-desk page had
  replaced its original URL. Its behavioral assertions were not weakened or
  rewritten.

## Completion Gate

- Python tests, compilation, JavaScript syntax, and lint: **PASS**
- One-desk verifier and behavioral browser regression: **PASS**
- H.264/yuv420p/1280×720/24 fps/120 frames/5 seconds: **PASS**
- White background, contact shadows, six clothing colors: **PASS**
- Six transparent/visible RGBA highlights: **PASS**
- Six bounded, distinct, aligned, non-overlapping projected regions: **PASS**
- Six destinations and all interaction/degradation modes: **PASS**
- Manual miniature shape, lighting, camera, motion, and interaction review:
  **PASS**
- Original sample artifacts and command preserved: **PASS**
- No Git initialization or commit: **PASS**

**Explicit Completion Gate result: PASS — DONE.**

## Authoritative production visual fix — supersedes prior acceptance

This section supersedes the original entry, frame-70, reduced-motion, visual
acceptance, hash, and Completion Gate claims above. Production review correctly
found that the original frame 70 contained all six hover-response panels, all
six desks were already visible at 92% scale in frame 1, and reduced-motion
loaded and displayed highlight imagery.

### Root causes and source corrections

- `add_response_motif()` keyframed every motif to full scale at frame 70, and
  base rendering never changed `hide_render`. Base, preview, repair, and cover
  contexts now call `set_response_motif_visibility(desks)` so no motif can
  render. Highlight rendering temporarily enables only the selected desk's
  motif.
- `animate_desk()` previously held every root at scale `0.92` from frame 1.
  Roots now begin at `0.001` in three staged pairs: A2/A5 frames 2–8, A1/A4
  frames 7–13, and A3/A6 frames 12–18. A Blender 5.2 compositor fades from
  white during frames 1–6. Frames 20, 21, and 120 retain the stable scene.
- Reduced-motion now enters `static-selection`, assigns no highlight `src`,
  hides the highlight stack, forces highlight opacity to zero, and uses only
  the cover, SVG/CSS selected ring, card, and immediate navigation.
- `src/verify_frame_content.py` and four unit tests now reject a frame-70
  one-frame response panel, require white/progressive frames 1/5/10/15/20, and
  enforce the 20/21 and 21/120 seams.
- `scripts/render-newsroom.ps1` now exposes bounded `-RepairFrames` and
  `-ArtifactsOnly` modes. Neither can enter the full-render cleanup/render path.

### Red evidence

Before source or frame changes:

```powershell
python -m unittest tests.test_frame_content -v
```

The generated-sequence test failed with:

```text
frame 1 must begin in white space (921600 non-white pixels; maximum 18432)
entry content must progress at frames 1/5/10/15/20:
  [921600, 921600, 921600, 921600, 921600]
frame 70 contains a transient response motif
  (7157 connected pixels; maximum 922)
```

The strengthened reduced-motion Edge smoke also failed before the web fix:

```text
stack:"block"
sources:["assets/newsroom-a1-highlight.png", ...]
opacity:["1","0","0","0","0","0"]
highlightRequests:6
```

### Partial-render commands and accounting

Pre-repair SHA-256 aggregate:

```text
affected frames 1-20 and 70:
0FD98D4A4606AF341AC9C5B07C7A9BC0E2142104FC7197EFF1F7EEB274080FC8
unaffected frames 21-69 and 71-120:
72183BCBA0ACE9B425EC2F7C017C56FEE72764325484E621BC7F96B882967D5C
```

The first bounded command failed in 2.443 seconds before rendering because the
Blender 5 compositor RGB output socket is named `Color`, not `Image`. No frame
was changed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 `
  -RepairFrames "1-20,70" -RegenerateArtifacts
```

After correcting that API use, the same command exited 0 in **124.827
seconds** and emitted exactly:

```text
frame_0001.png through frame_0020.png
frame_0070.png
NEWSROOM_REPAIR_COMPLETE 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,70
```

The first white constant was still gray after AgX. The minimum necessary entry
rerun changed only frames 1–20 and exited 0 in **107.918 seconds**:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 `
  -RepairFrames "1-20"
```

The regenerated highlights initially inherited the white compositor and became
opaque. Highlight rendering was isolated from that compositor. Because a
preimplementation negative PowerShell contract check had entered the old
preview cleanup path before failing, cover/highlight/hit-region artifacts had
to be regenerated. No base frame was included:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 `
  -ArtifactsOnly
```

The first artifacts-only attempt produced all seven stills and the Blend but
then Blender exited 11 in Intel `igxelpicd64.dll`; it was not accepted. The
identical bounded retry exited 0 in **20.034 seconds** with
`NEWSROOM_ARTIFACT_REPAIR_COMPLETE`.

The first `-SkipRender` encode correctly failed verification on the then-opaque
highlights and the obsolete assumption that entry frame 1 contained all desks.
After those defects were corrected, this command exited 0 in **12.650
seconds**:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/render-newsroom.ps1 -SkipRender
```

It ended with:

```text
newsroom media verification passed
NEWSROOM_PIPELINE_COMPLETE
```

No second full render command was invoked. The final unaffected-frame aggregate
is still exactly
`72183BCBA0ACE9B425EC2F7C017C56FEE72764325484E621BC7F96B882967D5C`.
Only frames 1–20 and 70 differ from the pre-repair sequence. Their final
aggregate is
`88D7716B9C83F054284B6D72F3C5872BA620466569C39302F48F41CE3A2F2BA3`.

### Authoritative visual and programmatic evidence

Manual inspection of frames 1, 5, 10, 15, 20, and 70 confirms:

- frame 1 is empty white space;
- frame 5 visibly contains only the first staged desk pair;
- frame 10 adds the second pair while the third remains absent;
- frame 15 adds the final pair progressively;
- frame 20 is the complete stable newsroom;
- frame 70 contains the six normal roles/desks/props and no floating
  hover-response panels.

Programmatic measurements:

```text
frame 1:  dark pixels 0;      mean 254.920; standard deviation 0.272
frame 5:  dark pixels 51,416; mean 238.244; standard deviation 5.317
frame 10: dark pixels 699,090; mean 210.014; standard deviation 34.621
frame 15: dark pixels 721,484; mean 206.091; standard deviation 39.482
frame 20: dark pixels 725,858; mean 202.935; standard deviation 42.877
frame 70 largest transient motif component: 0 pixels; maximum allowed 922
frame 20/21 seam: 8 changed pixels; mean absolute RGB 0.000003
frame 21/120 seam: 2 changed pixels; mean absolute RGB 0.000001
```

All six regenerated highlights have alpha extrema 0–255 and respectively
30,599; 25,296; 29,991; 38,889; 52,184; and 40,662 visible pixels.

### Final repaired outputs

```text
newsroom.mp4
  329004 bytes
  41D951C6A1C2DC66710F7BB62E379D40C81F15597FDDDEBA32561F4B418E9515
newsroom-cover.png
  1041055 bytes
  22D719966EE557330885594468F79994E2500BBE95D6FED9F29F5BD5E21C0A9F
newsroom.blend
  300163 bytes
  C5177B6C49F049D4F1921E5926656E3D1FAE9253710558EA4C6412D165C14135
newsroom-hit-regions.json
  1307 bytes
  D441A679070D3F7FE26241E0BD7855439C6B8885B2DE85F978580B9AA428221F
newsroom-a1-highlight.png
  9D7A7B04F4DBC9F1F584998EBE9817C8B58DB29D234206A6874B9CB313D60DEC
newsroom-a2-highlight.png
  6001E0A9858AF4359BC9BFD57A35805EFA8A86B54420022F2925D3D2F6067926
newsroom-a3-highlight.png
  46953C6279E603FE76C66B785ED21E3602C0F3CBDBE5D1D8828F102F252D05E2
newsroom-a4-highlight.png
  BA3126C254EEBFC38730F957FD9773D785E19E919941910CF0BE1A92C8D64349
newsroom-a5-highlight.png
  730CE0378D0E4C878F116AF92EEDD1AFCF7081658C2788E23C073202BF904BE9
newsroom-a6-highlight.png
  E1DCCE32C3B55AC63F9AB2A01946FD4BA244AA9BD0D632FA8BE44B898CBD9E9F
```

All eight web media hashes match their output sources.

### Final repaired verification

```powershell
python -m unittest discover -s tests -v
```

Result: **45 tests passed** in 101.734 seconds; command elapsed 102.149
seconds.

```powershell
python src/verify_outputs.py output
python src/verify_outputs.py output --newsroom
python src/verify_frame_content.py output/newsroom-frames
```

Results:

```text
media verification passed
newsroom media verification passed
newsroom frame-content verification passed
```

Python compilation, all JavaScript syntax checks, FFprobe, and IDE diagnostics
passed. FFprobe reports H.264, yuv420p, 1280×720, 24/1 fps, 120 decoded frames,
and 5.000000 seconds.

The one-desk Edge regression passed all original behavior assertions at
`web/sample/`. The URL adjustment is the required compatibility route after
Task 5 intentionally made `web/index.html` the six-desk product shell; moving
the product root back would be a regression. The original command remains
unchanged. The six-desk smoke passed all 15 checks, with PASS 10 now proving
that reduced-motion requests zero highlights, has no highlight sources or
display, uses the cover plus SVG/card selection, and navigates immediately.

The four preserved sample hashes remain exactly:

```text
sample.mp4
F38BAC8366C715AD1B5C38E8BA57A918C7E4C430020B3F1699170A055F2124BB
sample-cover.png
2A518399E74A6C71FED2E49FF33AFEA2D00F2D45C9D7831F09FFEC8990AA71C8
sample-highlight.png
EFC0F2574918828AAEF0F743B8DB11E5845A56D28D3DE64B93FEADB601D84C46
sample.blend
ECFCA96D56248EA75F478DA4AD8D4FCE2352CB884A3B1E3BA84EFE9DF9F93627
```

No `.git` directory exists.

### Authoritative Completion Gate result

All corrected source, partial-render, media, frame-content, browser, lint,
sample-preservation, synchronization, and visual criteria pass.

**PASS — DONE.**

Remaining concern: Blender 5.2 still emits the existing material/world
deprecation warnings, and one bounded artifacts-only attempt hit a transient
Intel graphics-driver shutdown crash before the identical retry passed. Neither
affects the verified final assets.
