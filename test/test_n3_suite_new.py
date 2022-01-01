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

from dataclasses import dataclass, field
import logging
from pathlib import Path
from typing import (
    Callable,
    Collection,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    Union,
    cast,
)
from _pytest.mark.structures import Mark, MarkDecorator, ParameterSet

import pytest
from rdflib.graph import ConjunctiveGraph, Graph
from rdflib.term import Node, URIRef
from rdflib.util import guess_format
from test.testutils import GraphHelper, check_serialize_parse, crapCompare

# from test.testutils.graph import assert_isomorphic
import os.path

# from .testutils import check_serialize_parse
from .testutils.files import MultiVariantFile

DATA_DIR = Path(__file__).parent / "n3"

# def _get_test_files_formats():
#     skiptests = []
#     for f in os.listdir("test/n3"):
#         if f not in skiptests:
#             fpath = "test/n3/" + f
#             if f.endswith(".rdf"):
#                 yield fpath, "xml"
#             elif f.endswith(".n3"):
#                 yield fpath, "n3"


# def all_n3_files():
#     skiptests = [
#         "test/n3/example-lots_of_graphs.n3",  # only n3 can serialize QuotedGraph, no point in testing roundtrip
#     ]
#     for fpath, fmt in _get_test_files_formats():
#         if fpath in skiptests:
#             log.debug("Skipping %s, known issue" % fpath)
#         else:
#             yield fpath, fmt

# extention_to_format = {"rdf": "application/rdf+xml"}


# @dataclass
# class TestCase:
#     variant_file: MultiVariantFile
#     roundtrip: bool
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


# def make_test_cases() -> Iterator[TestCase]:
#     skip_roundtrip_stems = {"example-lots_of_graphs"}
#     for variant_file in MultiVariantFile.for_directory(DATA_DIR):
#         yield TestCase(
#             variant_file,
#             roundtrip=variant_file.stem not in skip_roundtrip_stems,
#         )


def parse_roundtrip(
    graph_factory: Callable[[], Graph],
    source: Path,
    format: Optional[str],
    roundtrip: bool = True,
) -> Tuple[Graph, Set[Tuple[Node, Node, Node]]]:
    """
    parses the source, serializes it and reparses it, then asserts that the
    result from the first parse is isomorphic with the result from the second
    parse.
    """
    graph = graph_factory()
    source_text = source.read_text()
    if format is None:
        format = guess_format(source)
    assert format is not None, "could not determine format for {source}"
    logging.debug("source_text = %s", source_text)
    graph.parse(data=source_text, format=format)
    graph_ts = GraphHelper.triple_set(graph, exclude_blanks=True)
    # graph_ts = GraphHelper.triple_or_quad_set(graph)
    if roundtrip:
        reconstitued_text = graph.serialize(format=format)
        logging.debug("reconstitued_text = %s", reconstitued_text)
        reconstitued_graph = graph_factory()
        logging.debug("reconstitued_graph = %s", reconstitued_graph)
        reconstitued_graph.parse(data=reconstitued_text, format=format)
        # GraphHelper.assert_equals(graph, reconstitued_graph, exclude_blanks=True)
        reconstitued_graph_ts = GraphHelper.triple_set(reconstitued_graph, exclude_blanks=True)
        # reconstitued_graph_ts = GraphHelper.triple_or_quad_set(
        #     reconstitued_graph,
        # )
        # assert graph_ts == reconstitued_graph_ts
        # crapCompare(graph, reconstitued_graph)
        # assert graph.isomorphic(reconstitued_graph)
        GraphHelper.assert_equals(graph, reconstitued_graph, exclude_blanks=False)
        # assert_isomorphic(graph, reconstitued_graph, format)
    # assert graph.isomorphic(reconstitued_graph), (
    #     "graph\n"
    #     f"{graph.serialize('n3')}\n"
    #     "must be isomorphic to\n"
    #     f"{reconstitued_graph.serialize('n3')}"
    # )
    return graph, graph_ts


def check_variant_file(
    variant_file: MultiVariantFile,
    expected_extentions: Optional[Set[str]] = None,
    roundtrip: bool = True,
) -> None:
    default_graph_id = URIRef(f"urn:fdc:example.com:{variant_file.stem}")
    if expected_extentions is not None:
        found_extentions = {
            os.path.splitext(variant)[0] for variant in variant_file.variants
        }
        assert expected_extentions == found_extentions
    first: Optional[Tuple[Graph, Set[Tuple[Node, Node, Node]]]] = None
    for variant in variant_file.variants:
        graph, graph_ts = parse_roundtrip(
            lambda: ConjunctiveGraph(identifier=default_graph_id),
            variant,
            None,
            roundtrip=roundtrip,
        )
        if first is None:
            first = (graph, graph_ts)
            # first_graph_ts = GraphHelper.triple_set(graph, exclude_blanks=True)
        else:
            # GraphHelper.assert_equals(first[0], graph, exclude_blanks=True)
            assert first[1] == graph_ts
            # # reconstitued_graph_ts = GraphHelper.triple_set(reconstitued_graph, exclude_blanks=True)


@pytest.mark.parametrize(
    "variant_file",
    [
        variant_file.pytest_param()
        for variant_file in MultiVariantFile.for_directory(DATA_DIR)
    ]
    # [case.pytest_param for case in make_test_cases()],
    # [pytest.param(,v id=variant_file.stem) for variant_file in MultiVariantFile.for_directory(DATA_DIR) ],
)
def test_variant_file(variant_file: MultiVariantFile) -> None:
    # for variant in variant_file.variants:
    #     format = guess_format(variant)
    #     assert format is not None, "could not determine format for {variant}"
    #     check_serialize_parse(variant, format, "n3")
    check_variant_file(variant_file)


# def test_n3_writing(case: TestCase):
#     graph = parse_file(case.n3_file, "n3", case.roundtrip)

#     for variant in case.other_files:
#         variant_graph = parse_file(variant, None, case.roundtrip)
#         assert graph.isomorphic(variant_graph), (
#             "graph\n"
#             f"{graph.serialize('n3')}\n"
#             "must be isomorphic to\n"
#             f"{variant_graph.serialize('n3')}"
#         )

#     graph = Graph()
#     graph.parse(case.n3_file, "n3")

#     if case.roundtrip:
#         check_serialize_parse(case.n3_file, "n3", "n3")

#     for variant in case.other_files:
#         format = guess_format(variant)
#         check_serialize_parse(variant, format, "n3")

#     n3_file = next(
#         variant
#         for variant in case.variant_file.variants
#         if variant.name.endswith(".n3")
#     )

#     if case.roundtrip()
#     check_serialize_parse(fpath, fmt, "n3")
