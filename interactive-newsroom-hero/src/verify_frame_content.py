import argparse
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


ENTRY_FRAMES = (1, 5, 10, 15, 20)


def _changed_mask(center, neighbor_a, neighbor_b, threshold=20):
    center_pixels = center.convert("RGB").get_flattened_data()
    a_pixels = neighbor_a.convert("RGB").get_flattened_data()
    b_pixels = neighbor_b.convert("RGB").get_flattened_data()
    return [
        max(abs(channel - other) for channel, other in zip(pixel, a_pixel))
        >= threshold
        and max(abs(channel - other) for channel, other in zip(pixel, b_pixel))
        >= threshold
        and max(abs(channel - other) for channel, other in zip(a_pixel, b_pixel))
        < threshold // 2
        for pixel, a_pixel, b_pixel in zip(center_pixels, a_pixels, b_pixels)
    ]


def _largest_component(mask, size):
    width, height = size
    remaining = {index for index, changed in enumerate(mask) if changed}
    largest = 0
    while remaining:
        pending = [remaining.pop()]
        component_size = 0
        while pending:
            index = pending.pop()
            component_size += 1
            x, y = index % width, index // width
            for neighbor in (
                index - 1 if x else None,
                index + 1 if x + 1 < width else None,
                index - width if y else None,
                index + width if y + 1 < height else None,
            ):
                if neighbor is not None and neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
        largest = max(largest, component_size)
    return largest


def validate_no_transient_motifs(frame_69, frame_70, frame_71):
    if not (frame_69.size == frame_70.size == frame_71.size):
        return ["motif comparison frames must have matching dimensions"]
    largest = _largest_component(
        _changed_mask(frame_70, frame_69, frame_71),
        frame_70.size,
    )
    maximum = max(64, round(frame_70.width * frame_70.height * 0.001))
    if largest > maximum:
        return [
            "frame 70 contains a transient response motif "
            f"({largest} connected pixels; maximum {maximum})"
        ]
    return []


def _content_pixels(image):
    return sum(min(pixel) < 230 for pixel in image.convert("RGB").get_flattened_data())


def validate_entry_progression(frames):
    missing = [frame for frame in ENTRY_FRAMES if frame not in frames]
    if missing:
        return [f"missing entry frames: {missing}"]
    total = frames[1].width * frames[1].height
    counts = [_content_pixels(frames[frame]) for frame in ENTRY_FRAMES]
    errors = []
    frame_one_stats = ImageStat.Stat(frames[1].convert("RGB"))
    if (
        min(frame_one_stats.mean) < 245
        or max(frame_one_stats.stddev) > 3
        or counts[0] > total * 0.02
    ):
        errors.append(
            "frame 1 must begin in white space "
            f"(mean {frame_one_stats.mean}; deviation {frame_one_stats.stddev}; "
            f"{counts[0]} dark pixels)"
        )
    if any(current <= previous for previous, current in zip(counts, counts[1:])):
        errors.append(f"entry content must progress at frames 1/5/10/15/20: {counts}")
    return errors


def _mean_absolute_difference(left, right):
    difference = ImageChops.difference(
        left.convert("RGB"),
        right.convert("RGB"),
    )
    return sum(ImageStat.Stat(difference).mean) / 3


def validate_idle_seam(frame_20, frame_21, frame_120):
    errors = []
    for label, left, right in (
        ("20/21", frame_20, frame_21),
        ("21/120", frame_21, frame_120),
    ):
        difference = _mean_absolute_difference(left, right)
        if difference > 0.5:
            errors.append(
                f"idle seam {label} mean absolute RGB difference is {difference:.3f}"
            )
    return errors


def load_frame(directory, frame):
    return Image.open(directory / f"frame_{frame:04d}.png").convert("RGB")


def verify(directory):
    frames = {
        frame: load_frame(directory, frame)
        for frame in (*ENTRY_FRAMES, 21, 69, 70, 71, 120)
    }
    errors = []
    errors.extend(validate_entry_progression(frames))
    errors.extend(validate_no_transient_motifs(frames[69], frames[70], frames[71]))
    errors.extend(validate_idle_seam(frames[20], frames[21], frames[120]))
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("frame_directory", type=Path)
    args = parser.parse_args()
    try:
        errors = verify(args.frame_directory)
    except (FileNotFoundError, OSError) as error:
        errors = [str(error)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("newsroom frame-content verification passed")


if __name__ == "__main__":
    main()
