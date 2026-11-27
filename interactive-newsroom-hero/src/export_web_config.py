import json
import sys
from pathlib import Path

from scene_config import DESKS, rgba_hex
from verify_outputs import validate_hit_regions


def load_hit_regions(path: Path) -> dict[str, list[list[int]]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    errors = validate_hit_regions(payload)
    if errors:
        raise ValueError("\n".join(errors))
    return payload["regions"]


def build_web_config(regions: dict[str, list[list[int]]]) -> list[dict]:
    records = [
        {
            "id": desk.id,
            "module": desk.module,
            "title": desk.title,
            "english": desk.english,
            "role": desk.role,
            "responsibility": desk.responsibility,
            "color": rgba_hex(desk.color)[:7],
            "action": desk.action,
            "destination": desk.destination,
            "highlight": f"assets/newsroom-{desk.id}-highlight.png",
            "points": " ".join(f"{x},{y}" for x, y in regions[desk.id]),
            "cardSide": desk.card_side,
        }
        for desk in DESKS
    ]
    return records


def write_web_config(output_path: Path, desks: list[dict]) -> None:
    serialized = json.dumps(desks, ensure_ascii=False, indent=2)
    output_path.write_text(
        f"window.NEWSROOM_DESKS = Object.freeze({serialized});\n",
        encoding="utf-8",
    )


def main(input_path: Path, output_path: Path) -> None:
    regions = load_hit_regions(input_path)
    write_web_config(output_path, build_web_config(regions))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
