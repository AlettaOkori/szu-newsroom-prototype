$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "output"
$frames = Join-Path $output "frames"
$webAssets = Join-Path $root "web\assets"
$cover = Join-Path $output "sample-cover.png"
$highlight = Join-Path $output "sample-highlight.png"
$video = Join-Path $output "sample.mp4"

$blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" -ErrorAction SilentlyContinue |
  Sort-Object FullName |
  Select-Object -Last 1 -ExpandProperty FullName
if (-not $blender) {
  throw "Blender was not found under Program Files."
}

New-Item -ItemType Directory -Force -Path $output, $frames, $webAssets | Out-Null
Remove-Item (Join-Path $frames "frame_*.png") -Force -ErrorAction SilentlyContinue
Remove-Item $cover, $highlight, $video -Force -ErrorAction SilentlyContinue

& $blender --background --python (Join-Path $root "src\build_scene.py") -- $output
if ($LASTEXITCODE -ne 0) {
  throw "Blender render failed."
}

$renderedFrames = @(Get-ChildItem $frames -Filter "frame_*.png" -File)
$missingFrames = @(
  1..120 | ForEach-Object {
    $frame = Join-Path $frames ("frame_{0:D4}.png" -f $_)
    if (-not (Test-Path $frame -PathType Leaf)) { $frame }
  }
)
if ($renderedFrames.Count -ne 120 -or $missingFrames.Count -ne 0) {
  throw "Blender render did not produce the expected 120 frames."
}
foreach ($still in @($cover, $highlight)) {
  if (-not (Test-Path $still -PathType Leaf) -or (Get-Item $still).Length -eq 0) {
    throw "Blender render did not produce expected artifact: $still"
  }
}

ffmpeg -y -framerate 24 -i (Join-Path $frames "frame_%04d.png") `
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart `
  $video
if ($LASTEXITCODE -ne 0) {
  throw "FFmpeg encoding failed."
}

python (Join-Path $root "src\verify_outputs.py") $output
if ($LASTEXITCODE -ne 0) {
  throw "Output verification failed."
}

Copy-Item $video $webAssets -Force
Copy-Item $cover $webAssets -Force
Copy-Item $highlight $webAssets -Force
Write-Output "RENDER_PIPELINE_COMPLETE"
