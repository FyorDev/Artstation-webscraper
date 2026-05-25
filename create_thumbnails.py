from __future__ import annotations

import argparse
import random
from pathlib import Path

from PIL import Image, ImageOps


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def list_image_files(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    files.sort(key=lambda p: p.name.lower())
    return [p for p in files if p.name != "thumbnail_grid.jpg"]


def choose_images(files: list[Path], max_images: int = 9) -> list[Path]:
    if not files:
        return []

    half_count = max(1, len(files) // 2)
    candidates = files[:half_count]
    sample_size = min(max_images, len(candidates))
    if sample_size == len(candidates):
        return candidates
    return random.sample(candidates, sample_size)


def build_grid(image_paths: list[Path], output_path: Path, cell_size: int, gap: int, background=(18, 18, 18)) -> None:
    if not image_paths:
        return

    cols = 3
    rows = 3
    grid_w = cols * cell_size + (cols - 1) * gap
    grid_h = rows * cell_size + (rows - 1) * gap
    canvas = Image.new("RGB", (grid_w, grid_h), background)

    for index, image_path in enumerate(image_paths[: cols * rows]):
        row = index // cols
        col = index % cols
        x = col * (cell_size + gap)
        y = row * (cell_size + gap)

        try:
            with Image.open(image_path) as img:
                img = ImageOps.exif_transpose(img)
                thumb = ImageOps.fit(img.convert("RGB"), (cell_size, cell_size), method=Image.Resampling.LANCZOS)
                canvas.paste(thumb, (x, y))
        except Exception as exc:
            print(f"  [WARN] Skipping {image_path.name}: {exc}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=92)


def process_folder(folder: Path, root: Path, cell_size: int, gap: int, seed: int | None) -> bool:
    files = list_image_files(folder)
    if not files:
        print(f"Skipping {folder.name}: no image files found")
        return False

    if seed is not None:
        random.seed(seed + hash(folder.name))

    chosen = choose_images(files, max_images=9)
    if not chosen:
        print(f"Skipping {folder.name}: no usable images found")
        return False

    output_path = root / f"{folder.name}.jpg"
    build_grid(chosen, output_path, cell_size=cell_size, gap=gap)
    print(f"Created {output_path} from {len(chosen)} image(s)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a 3x3 thumbnail grid for each subfolder inside Downloaded/."
    )
    parser.add_argument("--root", default="Downloaded", help="Root folder containing artist folders")
    parser.add_argument("--cell-size", type=int, default=320, help="Size of each grid cell in pixels")
    parser.add_argument("--gap", type=int, default=12, help="Gap between images in pixels")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible thumbnails")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Root folder not found: {root}")
        return 1

    folders = [p for p in root.iterdir() if p.is_dir()]
    if not folders:
        print(f"No subfolders found in {root}")
        return 0

    created = 0
    skipped = 0

    for folder in sorted(folders, key=lambda p: p.name.lower()):
        if process_folder(folder, root, cell_size=args.cell_size, gap=args.gap, seed=args.seed):
            created += 1
        else:
            skipped += 1

    print(f"Done. Created {created} thumbnail(s), skipped {skipped} folder(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
