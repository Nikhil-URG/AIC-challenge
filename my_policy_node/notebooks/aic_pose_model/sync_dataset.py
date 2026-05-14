from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import shutil

from PIL import Image, ImageFile


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
IMAGES_TRAIN_DIR = DATA_DIR / "images" / "train"
LABELS_DIR = ROOT / "labels"
DATA_LABELS_LINK = DATA_DIR / "labels"
TRAIN_TXT = ROOT / "train.txt"
VAL_TXT = ROOT / "val.txt"
SUPPORTED_SUFFIXES = {".ppm", ".png", ".jpg", ".jpeg"}
VAL_FRACTION = 0.2

ImageFile.LOAD_TRUNCATED_IMAGES = True


def ensure_symlink(link_path: Path, target: Path) -> None:
    if link_path.is_symlink():
        if link_path.resolve() == target.resolve():
            return
        link_path.unlink()
    elif link_path.exists():
        raise RuntimeError(f"Cannot create symlink {link_path}: path already exists and is not a symlink.")

    link_path.parent.mkdir(parents=True, exist_ok=True)
    link_path.symlink_to(target)


def ensure_clean_dir(dir_path: Path) -> None:
    if dir_path.is_symlink() or dir_path.is_file():
        dir_path.unlink()
    elif dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)


def iter_subject_dirs() -> list[Path]:
    return sorted(
        path
        for path in DATA_DIR.iterdir()
        if path.is_dir() and path.name not in {"images", "labels"}
    )


def convert_image(src_path: Path, dst_path: Path) -> tuple[tuple[int, int], tuple[int, int]]:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src_path) as src_image:
        src_size = src_image.size
        src_image.save(dst_path, format="PNG")

    with Image.open(dst_path) as dst_image:
        dst_size = dst_image.size

    if src_size != dst_size:
        raise RuntimeError(f"Size mismatch after conversion: {src_path.relative_to(ROOT)} -> {dst_path.relative_to(ROOT)}")

    return src_size, dst_size


def convert_images(subject_dirs: list[Path]) -> tuple[list[Path], int]:
    ensure_clean_dir(IMAGES_TRAIN_DIR)
    converted_paths: list[Path] = []
    converted_count = 0

    for subject_dir in subject_dirs:
        for image_path in sorted(subject_dir.rglob("*")):
            if not image_path.is_file() or image_path.suffix.lower() not in SUPPORTED_SUFFIXES:
                continue

            relative_path = image_path.relative_to(DATA_DIR).with_suffix(".png")
            dst_path = IMAGES_TRAIN_DIR / relative_path
            convert_image(image_path, dst_path)
            converted_paths.append(dst_path)
            converted_count += 1

    return converted_paths, converted_count


def collect_pairs(
    converted_paths: list[Path],
) -> tuple[list[tuple[str, int]], Counter[int], Counter[int]]:
    pairs: list[tuple[str, int]] = []
    class_counts: Counter[int] = Counter()
    keypoint_counts: Counter[int] = Counter()

    for image_path in converted_paths:
        relative_path = image_path.relative_to(IMAGES_TRAIN_DIR)
        label_path = LABELS_DIR / "train" / relative_path.with_suffix(".txt")
        if not label_path.exists():
            raise RuntimeError(f"Missing label for image: {relative_path}")

        label_lines = label_path.read_text().splitlines()
        class_ids: list[int] = []
        for raw_line in label_lines:
            line = raw_line.strip()
            if not line:
                continue
            values = line.split()
            class_id = int(values[0])
            class_ids.append(class_id)
            class_counts[class_id] += 1
            keypoint_counts[(len(values) - 5) // 3] += 1

        if not class_ids:
            raise RuntimeError(f"Empty label file: {label_path.relative_to(ROOT)}")

        pairs.append((f"data/images/train/{relative_path.as_posix()}", class_ids[0]))

    return pairs, class_counts, keypoint_counts


def split_dataset(pairs: list[tuple[str, int]]) -> tuple[list[str], list[str]]:
    by_class: dict[int, list[str]] = defaultdict(list)
    for image_line, class_id in pairs:
        by_class[class_id].append(image_line)

    train_lines: list[str] = []
    val_lines: list[str] = []
    for _, image_lines in sorted(by_class.items()):
        image_lines = sorted(image_lines)
        val_count = max(1, round(len(image_lines) * VAL_FRACTION)) if len(image_lines) > 1 else 0
        val_subset = image_lines[:: max(1, len(image_lines) // val_count)][:val_count] if val_count else []
        val_set = set(val_subset)
        val_lines.extend(val_subset)
        train_lines.extend(line for line in image_lines if line not in val_set)

    return sorted(train_lines), sorted(val_lines)


def validate_label_coverage(subject_dirs: list[Path]) -> None:
    image_keys = {
        path.relative_to(DATA_DIR).with_suffix("")
        for subject_dir in subject_dirs
        for path in subject_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    }
    label_keys = {
        path.relative_to(LABELS_DIR / "train").with_suffix("")
        for path in (LABELS_DIR / "train").rglob("*.txt")
    }

    missing_labels = sorted(image_keys - label_keys)
    missing_images = sorted(label_keys - image_keys)
    if missing_labels or missing_images:
        details = []
        if missing_labels:
            details.append(f"missing labels: {missing_labels[:10]}")
        if missing_images:
            details.append(f"missing images: {missing_images[:10]}")
        raise RuntimeError("Dataset mismatch detected: " + "; ".join(details))


def main() -> None:
    subject_dirs = iter_subject_dirs()
    if not subject_dirs:
        raise RuntimeError("No subject directories found under data/.")

    ensure_symlink(DATA_LABELS_LINK, Path("../labels"))
    validate_label_coverage(subject_dirs)

    converted_paths, converted_count = convert_images(subject_dirs)
    pairs, class_counts, keypoint_counts = collect_pairs(converted_paths)
    train_lines, val_lines = split_dataset(pairs)
    TRAIN_TXT.write_text("\n".join(train_lines) + "\n")
    VAL_TXT.write_text("\n".join(val_lines) + "\n")

    print(f"subjects: {[path.name for path in subject_dirs]}")
    print(f"source images: {converted_count}")
    print(f"converted png images: {len(converted_paths)}")
    print(f"train images: {len(train_lines)}")
    print(f"val images: {len(val_lines)}")
    print(f"class counts: {dict(sorted(class_counts.items()))}")
    print(f"keypoints per object: {dict(sorted(keypoint_counts.items()))}")
    print(f"wrote: {TRAIN_TXT}")
    print(f"wrote: {VAL_TXT}")


if __name__ == "__main__":
    main()
