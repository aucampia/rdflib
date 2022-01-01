import logging
import os.path
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Collection,
    Dict,
    Iterable,
    MutableSet,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

from _pytest.mark.structures import Mark, MarkDecorator, ParameterSet
import pytest


@dataclass(order=True)
class MultiVariantFile:
    """
    Represents a file with multiple variants in different formats.
    """

    directory: Path
    stem: str
    variants: MutableSet[Path]

    # def filter_variants(
    #     self,
    #     include_suffixes: Optional[Set[str]] = None,
    #     exclude_suffixes: Optional[Set[str]] = None,
    # ) -> Iterable[Path]:
    #     for variant in self.variants:
    #         if include_suffixes is not None:
    #             for suffix in include_suffixes:
    #                 if not variant.name.endswith(suffix):
    #                     continue
    #         if exclude_suffixes is not None:
    #             for suffix in exclude_suffixes:
    #                 if variant.name.endswith(suffix):
    #                     continue
    #         yield variant

    def pytest_param(
        self,
        marks: Optional[
            Union[MarkDecorator, Collection[Union[MarkDecorator, Mark]]]
        ] = None,
    ) -> ParameterSet:
        if marks is None:
            marks = cast(Tuple[MarkDecorator], tuple())
        return pytest.param(self, id=self.stem, marks=marks)

    #     marks: Union[MarkDecorator, Collection[Union[MarkDecorator, Mark]]] = field(
    #         default_factory=lambda: cast(Tuple[MarkDecorator], tuple())
    #     )

    #     def __post_init__(self) -> None:
    #         n3_file: Optional[Path] = None
    #         self.other_files: List[Path] = []
    #         for variant in self.variant_file.variants:
    #             if variant.name.endswith(".n3"):
    #                 n3_file = variant
    #             else:
    #                 self.other_files.append(variant)

    #         if n3_file is None:
    #             raise ValueError(
    #                 f"Need at least one n3 file and none found for {self.variant_file}"
    #             )

    #         self.n3_file = n3_file

    #     def pytest_param(self) -> ParameterSet:
    #         return pytest.param(self, id=self.variant_file.stem, marks=self.marks)

    @classmethod
    def from_path(cls, file: Path) -> "MultiVariantFile":
        stem, extension = os.path.splitext(file.name)
        return MultiVariantFile(file.parent, stem, {file})

    @classmethod
    def for_directory(cls, directory: Path) -> Iterable["MultiVariantFile"]:
        files: Dict[str, MultiVariantFile] = {}
        for file_path in directory.glob("**/*"):
            if not file_path.is_file():
                continue
            file_key, _ = os.path.splitext(file_path.relative_to(directory))
            logging.error("file_key = %s", file_key)
            if file_key not in files:
                file = files[file_key] = MultiVariantFile.from_path(file_path)
            else:
                file = files[file_key]
                file.variants.add(file_path)
        return files.values()
