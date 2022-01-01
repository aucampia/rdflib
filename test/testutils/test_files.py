from pathlib import Path
from typing import List
from .files import MultiVariantFile


def test_nested(tmp_path: Path) -> None:
    """
    Variants in multiple levels are correctly detected.
    """
    directories = [".", "l1-d0", "l1-d1/l2-d0"]
    stems = ["f0", "f1", "f2"]
    directory_files = set()
    directory_variant_files: List[MultiVariantFile] = []
    for index, stem in enumerate(stems):
        variants = {Path(f"{stem}.{ext}") for ext in range(index + 1)}
        directory_files.update(variants)
        directory_variant_files.append(
            MultiVariantFile(Path("/placeholder"), stem, variants)
        )
    file_paths: List[Path] = []
    expected_variant_files = []
    for directory in directories:
        resolved_directory = tmp_path / directory
        extra_file_paths = [
            resolved_directory / directory_file for directory_file in directory_files
        ]
        file_paths.extend(extra_file_paths)
        extra_variant_files = [
            MultiVariantFile(
                resolved_directory,
                item.stem,
                {resolved_directory / variant.name for variant in item.variants},
            )
            for item in directory_variant_files
        ]
        expected_variant_files.extend(extra_variant_files)
    for file_path in file_paths:
        file_path.parent.mkdir(exist_ok=True, parents=True)
        file_path.write_text("blank")
    actual_variant_files = list(MultiVariantFile.for_directory(tmp_path))
    assert len(actual_variant_files) == (len(directories) * 3)
    expected_variant_files.sort()
    actual_variant_files.sort()
    assert expected_variant_files == actual_variant_files
