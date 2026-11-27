param(
  [switch]$PreviewOnly,
  [switch]$SkipRender,
  [string]$RepairFrames,
  [switch]$RegenerateArtifacts,
  [switch]$ArtifactsOnly
)

$ErrorActionPreference = "Stop"
if ($PreviewOnly -and $SkipRender) {
  throw "PreviewOnly and SkipRender cannot be combined."
}
if ($RepairFrames -and ($PreviewOnly -or $SkipRender)) {
  throw "RepairFrames cannot be combined with PreviewOnly or SkipRender."
}
if ($RegenerateArtifacts -and -not $RepairFrames) {
  throw "RegenerateArtifacts requires RepairFrames."
}
if ($ArtifactsOnly -and ($PreviewOnly -or $SkipRender -or $RepairFrames)) {
  throw "ArtifactsOnly cannot be combined with other render modes."
}

$root = Split-Path -Parent $PSScriptRoot
$output = Join-Path $root "output"
$newsroomFrames = Join-Path $output "newsroom-frames"
$newsroomPreview = Join-Path $output "newsroom-preview"
$webAssets = Join-Path $root "web\assets"
$sceneData = Join-Path $root "web\scene-data.js"
$video = Join-Path $output "newsroom.mp4"
$cover = Join-Path $output "newsroom-cover.png"
$hitRegions = Join-Path $output "newsroom-hit-regions.json"
$blend = Join-Path $output "newsroom.blend"
$blendBackup = Join-Path $output "newsroom.blend1"
$highlights = 1..6 | ForEach-Object {
  Join-Path $output ("newsroom-a{0}-highlight.png" -f $_)
}

$blenderIsPythonRunner = $false
if ($env:BLENDER_EXECUTABLE) {
  if (-not (Test-Path $env:BLENDER_EXECUTABLE -PathType Leaf)) {
    throw "BLENDER_EXECUTABLE does not name an existing file."
  }
  $blender = (Resolve-Path $env:BLENDER_EXECUTABLE).Path
  $blenderIsPythonRunner = [IO.Path]::GetExtension($blender) -eq ".py"
} else {
  $blender = Get-ChildItem "$env:ProgramFiles\Blender Foundation\Blender *\blender.exe" -ErrorAction SilentlyContinue |
    Sort-Object FullName |
    Select-Object -Last 1 -ExpandProperty FullName
  if (-not $blender) {
    throw "Blender was not found under Program Files."
  }
}

$commands = @{}
foreach ($name in @("ffmpeg", "ffprobe", "python", "node")) {
  $command = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $command) {
    throw "Required command was not found: $name"
  }
  $commands[$name] = $command.Source
}

New-Item -ItemType Directory -Force -Path `
  $output, $newsroomFrames, $newsroomPreview, $webAssets | Out-Null

function Assert-CommandSucceeded([string]$description) {
  if ($LASTEXITCODE -ne 0) {
    throw "$description failed with exit code $LASTEXITCODE."
  }
}

function Assert-NonemptyFile([string]$path) {
  if (-not (Test-Path $path -PathType Leaf) -or (Get-Item $path).Length -eq 0) {
    throw "Expected nonempty artifact was not produced: $path"
  }
}

function Assert-Frames([string]$directory, [int[]]$frameNumbers) {
  $renderedFrames = @(Get-ChildItem $directory -Filter "frame_*.png" -File)
  $missingFrames = @(
    $frameNumbers | ForEach-Object {
      $frame = Join-Path $directory ("frame_{0:D4}.png" -f $_)
      if (-not (Test-Path $frame -PathType Leaf)) { $frame }
    }
  )
  if ($renderedFrames.Count -ne $frameNumbers.Count -or $missingFrames.Count -ne 0) {
    throw "Expected $($frameNumbers.Count) contiguous newsroom frames in $directory."
  }
}

function Assert-SceneArtifacts {
  foreach ($artifact in @($cover, $hitRegions, $blend) + $highlights) {
    Assert-NonemptyFile $artifact
  }
}

function Remove-SceneArtifacts {
  Remove-Item -Path (@($cover, $hitRegions, $blend, $blendBackup, $sceneData) + $highlights) `
    -Force -ErrorAction SilentlyContinue
}

function Get-RequestedFrameNumbers([string]$selection) {
  $selected = @()
  foreach ($token in $selection.Split(",")) {
    if ($token -match "^\d+$") {
      $selected += [int]$token
    } elseif ($token -match "^(\d+)-(\d+)$") {
      $start = [int]$Matches[1]
      $end = [int]$Matches[2]
      if ($end -lt $start) {
        throw "Invalid frame selection: $selection"
      }
      $selected += $start..$end
    } else {
      throw "Invalid frame selection: $selection"
    }
  }
  if (
    $selected.Count -eq 0 -or
    @($selected | Select-Object -Unique).Count -ne $selected.Count -or
    @($selected | Where-Object { $_ -lt 1 -or $_ -gt 120 }).Count -ne 0
  ) {
    throw "Invalid frame selection: $selection"
  }
  return [int[]]$selected
}

function Invoke-Blender(
  [string]$mode,
  [string]$frames = "",
  [switch]$regenerateArtifacts
) {
  $sceneBuilder = Join-Path $root "src\build_newsroom.py"
  $startInfo = New-Object System.Diagnostics.ProcessStartInfo
  $arguments = (
    "--background --python-exit-code 1 --python `"$sceneBuilder`" " +
    "-- `"$output`" --mode $mode"
  )
  if ($frames) {
    $arguments += " --frames `"$frames`""
  }
  if ($regenerateArtifacts) {
    $arguments += " --regenerate-artifacts"
  }
  if ($blenderIsPythonRunner) {
    $startInfo.FileName = $commands["python"]
    $arguments = "`"$blender`" " + $arguments
  } else {
    $startInfo.FileName = $blender
  }
  $startInfo.Arguments = $arguments
  $startInfo.UseShellExecute = $false
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true
  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = $startInfo
  [void]$process.Start()
  $stdout = $process.StandardOutput.ReadToEndAsync()
  $stderr = $process.StandardError.ReadToEndAsync()
  $process.WaitForExit()
  $outputText = $stdout.Result + $stderr.Result
  Write-Output $outputText
  if (
    $process.ExitCode -ne 0 -or
    $outputText -match "Traceback \(most recent call last\)"
  ) {
    throw "Blender newsroom $mode render failed with exit code $($process.ExitCode)."
  }
}

function Export-SceneData {
  & $commands["python"] (Join-Path $root "src\export_web_config.py") $hitRegions $sceneData
  Assert-CommandSucceeded "Newsroom web-config generation"
  & $commands["node"] --check $sceneData
  Assert-CommandSucceeded "Newsroom JavaScript syntax check"
}

if ($PreviewOnly) {
  Remove-SceneArtifacts
  Remove-Item (Join-Path $newsroomPreview "frame_*.png") -Force -ErrorAction SilentlyContinue
  Invoke-Blender "preview"
  Assert-Frames $newsroomPreview @(1, 21, 70, 120)
  Assert-SceneArtifacts
  Export-SceneData
  Write-Output "NEWSROOM_PREVIEW_COMPLETE"
  exit 0
}

if ($RepairFrames) {
  $requestedFrames = Get-RequestedFrameNumbers $RepairFrames
  foreach ($frameNumber in $requestedFrames) {
    Remove-Item (Join-Path $newsroomFrames ("frame_{0:D4}.png" -f $frameNumber)) `
      -Force -ErrorAction SilentlyContinue
  }
  if ($RegenerateArtifacts) {
    Remove-SceneArtifacts
  }
  Invoke-Blender "repair" $RepairFrames -regenerateArtifacts:$RegenerateArtifacts
  foreach ($frameNumber in $requestedFrames) {
    Assert-NonemptyFile (Join-Path $newsroomFrames ("frame_{0:D4}.png" -f $frameNumber))
  }
  Assert-Frames $newsroomFrames (1..120)
  if ($RegenerateArtifacts) {
    Assert-SceneArtifacts
    Export-SceneData
  }
  exit 0
}

if ($ArtifactsOnly) {
  Remove-SceneArtifacts
  Invoke-Blender "artifacts"
  Assert-SceneArtifacts
  Export-SceneData
  exit 0
}

if (-not $SkipRender) {
  Get-ChildItem $output -Filter "newsroom-*" -File -ErrorAction SilentlyContinue |
    Remove-Item -Force
  Remove-Item -Path $blend, $blendBackup, $sceneData -Force -ErrorAction SilentlyContinue
  Remove-Item (Join-Path $newsroomFrames "frame_*.png") -Force -ErrorAction SilentlyContinue
  Invoke-Blender "full"
}

Assert-Frames $newsroomFrames (1..120)
Assert-SceneArtifacts

& $commands["ffmpeg"] -y -framerate 24 `
  -i (Join-Path $newsroomFrames "frame_%04d.png") `
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart `
  $video
Assert-CommandSucceeded "FFmpeg newsroom encoding"

Export-SceneData

& $commands["python"] (Join-Path $root "src\verify_outputs.py") $output --newsroom
Assert-CommandSucceeded "Complete newsroom output verification"

& $commands["python"] (Join-Path $root "src\verify_frame_content.py") $newsroomFrames
Assert-CommandSucceeded "Newsroom frame-content verification"

$syncPairs = @(
  @{ Source = $video; Destination = Join-Path $webAssets "newsroom.mp4" }
  @{ Source = $cover; Destination = Join-Path $webAssets "newsroom-cover.png" }
)
for ($index = 1; $index -le 6; $index++) {
  $syncPairs += @{
    Source = Join-Path $output ("newsroom-a{0}-highlight.png" -f $index)
    Destination = Join-Path $webAssets ("newsroom-a{0}-highlight.png" -f $index)
  }
}

foreach ($pair in $syncPairs) {
  Copy-Item $pair.Source $pair.Destination -Force
  $sourceHash = (Get-FileHash $pair.Source -Algorithm SHA256).Hash
  $destinationHash = (Get-FileHash $pair.Destination -Algorithm SHA256).Hash
  if ($sourceHash -ne $destinationHash) {
    throw "Web synchronization hash mismatch: $($pair.Destination)"
  }
}

Write-Output "NEWSROOM_PIPELINE_COMPLETE"
