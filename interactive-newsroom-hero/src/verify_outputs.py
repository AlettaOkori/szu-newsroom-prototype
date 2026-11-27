import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from scene_config import DESKS, NEWSROOM_OUTPUT_NAMES, OUTPUT_NAMES, RenderSpec

REPRESENTATIVE_FRAMES = (1, 21, 70, 120)


def validate_probe(probe: dict) -> list[str]:
    stream = probe["streams"][0]
    spec = RenderSpec()
    errors = []
    if stream["codec_name"] != "h264":
        errors.append("codec must be h264")
    if stream["pix_fmt"] != "yuv420p":
        errors.append("pixel format must be yuv420p")
    if (stream["width"], stream["height"]) != (spec.width, spec.height):
        errors.append("resolution must be 1280x720")
    if float(Fraction(stream["r_frame_rate"])) != spec.fps:
        errors.append("frame rate must be 24 fps")
    if int(stream["nb_read_frames"]) != spec.frame_end:
        errors.append("decoded frame count must be 120")
    if abs(float(probe["format"]["duration"]) - spec.duration_seconds) > 0.05:
        errors.append("duration must be 5.0 seconds")
    return errors


def validate_cover(image: Image.Image) -> list[str]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    errors = []
    background_points = [
        (x, y)
        for x in (0.02, 0.05, 0.10, 0.90, 0.95, 0.98)
        for y in (0.03, 0.08, 0.13)
    ] + [(0.5, 0.03)]
    background_samples = [
        rgb.getpixel((round(width * x), round(height * y)))
        for x, y in background_points
    ]
    if any(min(pixel) < 235 for pixel in background_samples):
        errors.append("cover background samples must be near-white")

    pixels = rgb.get_flattened_data()
    shadow_count = sum(
        80 <= sum(pixel) / 3 <= 220 and max(pixel) - min(pixel) < 24
        for pixel in pixels
    )
    if shadow_count < 500:
        errors.append("cover must contain visible shadow pixels")

    red_count = sum(
        red >= 150 and red > green * 1.4 and red > blue * 1.15
        for red, green, blue in pixels
    )
    if red_count < 1000:
        errors.append("cover must contain visible red clothing pixels")
    return errors


def validate_highlight(image: Image.Image) -> list[str]:
    if image.mode != "RGBA":
        return ["highlight must use RGBA color mode"]
    alpha_min, alpha_max = image.getchannel("A").getextrema()
    errors = []
    if alpha_min != 0:
        errors.append("highlight must contain transparent pixels")
    if alpha_max == 0:
        errors.append("highlight must contain visible pixels")
    return errors


def validate_hit_regions(payload: dict) -> list[str]:
    if not isinstance(payload, dict):
        return ["hit-region payload must be an object"]

    errors = []
    if payload.get("viewBox") != [0, 0, 1280, 720]:
        errors.append("hit-region viewBox must be 1280x720")
    regions = payload.get("regions", {})
    if not isinstance(regions, dict):
        errors.append("hit regions must be an object")
        return errors
    if list(regions) != [f"a{index}" for index in range(1, 7)]:
        errors.append("hit regions must be ordered a1 through a6")
        return errors
    polygons = []
    for desk_id, points in regions.items():
        if not isinstance(points, list) or len(points) != 4:
            errors.append(f"{desk_id} hit region must contain four points")
            continue
        if any(
            not isinstance(point, list)
            or len(point) != 2
            or any(not isinstance(coordinate, int) or isinstance(coordinate, bool)
                   for coordinate in point)
            for point in points
        ):
            errors.append(
                f"{desk_id} hit region must contain integer coordinate pairs"
            )
            continue
        if any(not 0 <= point[0] <= 1280 or not 0 <= point[1] <= 720
               for point in points):
            errors.append(f"{desk_id} hit region must stay inside 1280x720")
        twice_area = abs(sum(
            points[index][0] * points[(index + 1) % 4][1]
            - points[(index + 1) % 4][0] * points[index][1]
            for index in range(4)
        ))
        if twice_area < 4000:
            errors.append(f"{desk_id} hit region is too small")
        polygons.append(tuple(tuple(point) for point in points))
    if len(set(polygons)) != len(polygons):
        errors.append("hit-region polygons must be distinct")
    return errors


def validate_newsroom_highlights(
    images: dict[str, Image.Image],
    regions: dict[str, list[list[int]]],
) -> list[str]:
    errors = []
    digests = []
    for desk in DESKS:
        desk_id = desk.id
        image = images.get(desk_id)
        if image is None:
            errors.append(f"missing highlight: {desk_id}")
            continue
        if image.size != (1280, 720) or image.mode != "RGBA":
            errors.append(f"{desk_id} highlight must be 1280x720 RGBA")
            continue
        alpha_min, alpha_max = image.getchannel("A").getextrema()
        if alpha_min != 0:
            errors.append(f"{desk_id} highlight must contain transparent pixels")
        if alpha_max == 0:
            errors.append(f"{desk_id} highlight must contain visible pixels")
            continue

        alpha = image.getchannel("A")
        normalized = image.copy()
        transparent_mask = alpha.point(
            lambda value: 255 if value == 0 else 0
        )
        normalized.paste((0, 0, 0, 0), mask=transparent_mask)
        digests.append(hashlib.sha256(normalized.tobytes()).digest())
        bounds = alpha.getbbox()
        target = tuple(round(channel * 255) for channel in desk.color[:3])
        color_count = sum(
            alpha_value > 0
            and sum(
                (channel - expected) ** 2
                for channel, expected in zip(pixel[:3], target)
            ) <= 65 ** 2
            for pixel in image.crop(bounds).get_flattened_data()
            for alpha_value in (pixel[3],)
        )
        if color_count < 100:
            errors.append(
                f"{desk_id} highlight must contain configured clothing-color evidence"
            )

        points = regions.get(desk_id)
        if (
            not isinstance(points, list)
            or len(points) != 4
            or any(
                not isinstance(point, list)
                or len(point) != 2
                or any(not isinstance(value, int) for value in point)
                for point in points
            )
        ):
            continue
        polygon_mask = Image.new("L", image.size, 0)
        ImageDraw.Draw(polygon_mask).polygon(
            [tuple(point) for point in points],
            fill=255,
        )
        polygon_pixels = polygon_mask.histogram()[255]
        visible_alpha = alpha.point(lambda value: 255 if value > 0 else 0)
        covered_pixels = ImageChops.multiply(
            polygon_mask,
            visible_alpha,
        ).histogram()[255]
        if polygon_pixels == 0 or covered_pixels / polygon_pixels < 0.8:
            errors.append(
                f"{desk_id} highlight must substantially cover its projected desk polygon"
            )
        centroid = (
            round(sum(point[0] for point in points) / len(points)),
            round(sum(point[1] for point in points) / len(points)),
        )
        if alpha.getpixel(centroid) < 200:
            errors.append(
                f"{desk_id} highlight must be visible and opaque at its desk centroid"
            )
    if len(set(digests)) != len(digests):
        errors.append("highlight contents must be pairwise distinct")
    return errors


def _validate_newsroom_cover(image: Image.Image) -> list[str]:
    rgb = image.convert("RGB")
    width, height = rgb.size
    errors = []
    background_points = [
        (x, y)
        for x in (0.02, 0.05, 0.10, 0.90, 0.95, 0.98)
        for y in (0.03, 0.08, 0.13)
    ] + [(0.5, 0.03)]
    background_samples = [
        rgb.getpixel((round(width * x), round(height * y)))
        for x, y in background_points
    ]
    if any(min(pixel) < 235 for pixel in background_samples):
        errors.append("background samples must be near-white")

    pixels = list(rgb.get_flattened_data())
    shadow_count = sum(
        80 <= sum(pixel) / 3 <= 220 and max(pixel) - min(pixel) < 24
        for pixel in pixels
    )
    if shadow_count < 500:
        errors.append("must contain visible contact-shadow pixels")

    for desk in DESKS:
        target = tuple(round(channel * 255) for channel in desk.color[:3])
        color_count = sum(
            sum((channel - expected) ** 2
                for channel, expected in zip(pixel, target)) <= 65 ** 2
            for pixel in pixels
        )
        if color_count < 100:
            errors.append(f"{desk.id}: cover must contain visible clothing-color evidence")
    return errors


def probe_video(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-select_streams",
            "v:0",
            "-show_entries",
            (
                "stream=codec_name,pix_fmt,width,height,r_frame_rate,"
                "nb_read_frames:format=duration"
            ),
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def validate_newsroom(root: Path, *, preview: bool = False) -> list[str]:
    errors = []
    video = root / NEWSROOM_OUTPUT_NAMES["video"]
    cover = root / NEWSROOM_OUTPUT_NAMES["cover"]
    hit_regions = root / NEWSROOM_OUTPUT_NAMES["hit_regions"]
    hit_region_payload = None
    hit_region_errors = []
    if not hit_regions.exists():
        hit_region_errors.append(f"{hit_regions.name}: missing output")
    else:
        with hit_regions.open(encoding="utf-8") as handle:
            hit_region_payload = json.load(handle)
        hit_region_errors.extend(
            f"{hit_regions.name}: {error}"
            for error in validate_hit_regions(hit_region_payload)
        )

    if not preview:
        if not video.exists():
            errors.append(f"{video.name}: missing output")
        else:
            errors.extend(
                f"{video.name}: {error}"
                for error in validate_probe(probe_video(video))
            )

    if not cover.exists():
        errors.append(f"{cover.name}: missing output")
    else:
        with Image.open(cover) as image:
            if image.size != (1280, 720):
                errors.append(f"{cover.name}: cover must be 1280x720")
            errors.extend(
                f"{cover.name}: {error}"
                for error in _validate_newsroom_cover(image)
            )

    highlight_images = {}
    for desk_id, filename in NEWSROOM_OUTPUT_NAMES["highlights"].items():
        path = root / filename
        if not path.exists():
            continue
        with Image.open(path) as image:
            highlight_images[desk_id] = image.copy()
    regions = (
        hit_region_payload.get("regions", {})
        if isinstance(hit_region_payload, dict)
        else {}
    )
    for error in validate_newsroom_highlights(highlight_images, regions):
        if error.startswith("missing highlight: "):
            desk_id = error.removeprefix("missing highlight: ")
            errors.append(f"{desk_id}: missing highlight")
        else:
            errors.append(error)

    errors.extend(hit_region_errors)

    frame_directory = "newsroom-preview" if preview else "newsroom-frames"
    for frame_number in REPRESENTATIVE_FRAMES:
        relative_frame = (
            Path(frame_directory) / f"frame_{frame_number:04d}.png"
        )
        frame = root / relative_frame
        frame_label = relative_frame.as_posix()
        if not frame.exists():
            errors.append(f"{frame_label}: missing representative frame")
            continue
        with Image.open(frame) as image:
            if image.size != (1280, 720):
                errors.append(f"{frame_label}: frame must be 1280x720")
            if frame_number != RenderSpec().frame_start:
                errors.extend(
                    f"{frame_label}: {error}"
                    for error in _validate_newsroom_cover(image)
                )
    return errors


def verify(root: Path) -> list[str]:
    spec = RenderSpec()
    errors = []
    video = root / OUTPUT_NAMES["video"]
    cover = root / OUTPUT_NAMES["cover"]
    highlight = root / OUTPUT_NAMES["highlight"]
    for path in (video, cover, highlight):
        if not path.exists():
            errors.append(f"missing output: {path.name}")
    if errors:
        return errors
    errors.extend(validate_probe(probe_video(video)))
    with Image.open(cover) as image:
        if image.size != (spec.width, spec.height):
            errors.append("cover must be 1280x720")
        errors.extend(validate_cover(image))
    with Image.open(highlight) as image:
        if image.size != (spec.width, spec.height):
            errors.append("highlight must be 1280x720")
        errors.extend(validate_highlight(image))
    for frame_number in REPRESENTATIVE_FRAMES:
        frame = root / "frames" / f"frame_{frame_number:04d}.png"
        if not frame.exists():
            errors.append(f"missing representative frame: {frame.name}")
            continue
        with Image.open(frame) as image:
            for error in validate_cover(image):
                errors.append(f"{frame.name}: {error}")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--newsroom", action="store_true")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    if args.preview and not args.newsroom:
        parser.error("--preview requires --newsroom")
    problems = (
        validate_newsroom(args.root, preview=args.preview)
        if args.newsroom
        else verify(args.root)
    )
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit(1)
    if args.newsroom and args.preview:
        print("newsroom preview verification passed")
    elif args.newsroom:
        print("newsroom media verification passed")
    else:
        print("media verification passed")
