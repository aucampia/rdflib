"""
Executes the RDFLib custom test suite for n3.

This test suite is somewhat implicitly defined by the files in the "n3_suite"
directory. The provenance of these files are uncertain and it seems they were
made specifically for RDFlib.

The test suite does the following:

* Round trips the file through parsing, serialization and then re-parsing,
  comparing the result from the first and second parse to confirm they are
  identical.
* If there are multiple variants of the file (e.g. a.n3 and a.rdf) then compare
  the graphs obtained by parsing each file is the same.
"""

import logging
import os.path
from dataclasses import dataclass
from pathlib import Path
from test.testutils import GraphHelper
from typing import (
    Callable,
    Collection,
    Dict,
    Iterable,
    List,
    MutableSet,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)

import pytest
from _pytest.mark.structures import Mark, MarkDecorator, ParameterSet

from rdflib.graph import ConjunctiveGraph, Graph
from rdflib.util import SUFFIX_FORMAT_MAP, guess_format

DATA_DIR = Path(__file__).parent / "n3"


@dataclass(order=True)
class MultiVariantFile:
    """
    Represents a file with multiple variants in different formats.
    """

    directory: Path
    stem: str
    variants: MutableSet[Path]

    def pytest_param(
        self,
        marks: Optional[
            Union[MarkDecorator, Collection[Union[MarkDecorator, Mark]]]
        ] = None,
    ) -> ParameterSet:
        if marks is None:
            marks = cast(Tuple[MarkDecorator], tuple())
        return pytest.param(self, id=self.stem, marks=marks)

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


def test_nested_variants(tmp_path: Path) -> None:
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


def check_parse_roundtrip(
    graph_factory: Callable[[], Graph],
    source: Path,
    format: Optional[str],
    tmp_path: Path,
    roundtrip: bool = True,
) -> Graph:
    """
    Parse the source, serializes it and reparse it, then asserts that the
    result from the first parse is equalt to the result from the second
    parse.
    """
    graph = graph_factory()
    source_text = source.read_text()
    # _, source_ext = os.path.splitext(source)
    if format is None:
        format = guess_format(source)
    assert format is not None, "could not determine format for {source}"
    logging.debug("source_text = %s", source_text)
    graph.parse(source=source, format=format)
    if roundtrip:
        # reconstitued_path = tmp_path / f"reconstitued.{source_ext}"
        # graph.serialize(destination=reconstitued_path, format=format)
        # reconstitued_text = reconstitued_path.read_text()
        reconstitued_text = graph.serialize(format=format)
        logging.debug("reconstitued_text = %s", reconstitued_text)
        reconstitued_graph = graph_factory()
        logging.debug("reconstitued_graph = %s", reconstitued_graph)
        # reconstitued_graph.parse(source=reconstitued_path, format=format)
        reconstitued_graph.parse(data=reconstitued_text, format=format)

        GraphHelper.assert_triples_equal(
            graph,
            reconstitued_graph,
            exclude_blanks=True,
        )
    return graph


def check_variant_file(
    variant_file: MultiVariantFile,
    tmp_path: Path,
    expected_extentions: Optional[Set[str]] = None,
    roundtrip: bool = True,
) -> None:
    assert len(variant_file.variants) > 0
    if expected_extentions is not None:
        found_extentions = {
            os.path.splitext(variant)[1] for variant in variant_file.variants
        }
        assert expected_extentions.issubset(found_extentions)
        # assert expected_extentions == found_extentions
    first_graph: Optional[Graph] = None
    for variant in variant_file.variants:
        graph = check_parse_roundtrip(
            ConjunctiveGraph,
            variant,
            None,
            tmp_path,
            roundtrip=roundtrip,
        )
        if first_graph is None:
            first_graph = graph
        else:
            GraphHelper.assert_triples_equal(first_graph, graph, exclude_blanks=True)


variant_files = list(MultiVariantFile.for_directory(DATA_DIR))


# def all_n3_files() -> Iterable[Tuple[str, str]]:
#     skip = {"example-lots_of_graphs.n3"}
#     for variant_file in variant_files:
#         for variant in variant_file.variants:
#             if variant.name in skip:
#                 continue
#             stem, ext = os.path.splitext(variant)
#             yield f"{variant}", SUFFIX_FORMAT_MAP[ext[1:]]
#         # n3_variant = next(
#         #     variant for variant in variant_file.variants if variant.name.endswith(".n3")
#         # )
#         # assert n3_variant is not None
#         # yield f"{n3_variant}", "n
#     # skiptests = [
#     #     "test/n3/example-lots_of_graphs.n3",  # only n3 can serialize QuotedGraph, no point in testing roundtrip
#     # ]
#     # for fpath, fmt in _get_test_files_formats():
#     #     if fpath in skiptests:
#     #         log.debug("Skipping %s, known issue" % fpath)
#     #     else:
#     #         yield fpath, fmt


def test_all_tested() -> None:
    assert len(variant_files) > 1
    assert len(variant_files) == len(list(DATA_DIR.glob("*.n3")))


@pytest.mark.parametrize(
    "variant_file",
    [variant_file.pytest_param() for variant_file in variant_files],
)
def test_variant_file(variant_file: MultiVariantFile, tmp_path: Path) -> None:
    check_variant_file(variant_file, tmp_path, expected_extentions={".n3"})
