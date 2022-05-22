import enum
from dataclasses import dataclass, field
from functools import lru_cache
from optparse import Option
from pathlib import Path
from test.data import TEST_DATA_DIR
from test.utils import file_uri_to_path, manifest
from test.utils.graph import GraphSource, GraphSourceType, cached_graph, load_sources
from test.utils.namespace import MF
from typing import (
    Collection,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import pytest
from _pytest.mark.structures import Mark, MarkDecorator, ParameterSet

from rdflib.graph import Graph
from rdflib.namespace import RDF
from rdflib.term import IdentifiedNode, Identifier, URIRef

TEST_VOCAB = cached_graph(
    (
        TEST_DATA_DIR / "defined_namespaces/dawgt.ttl",
        TEST_DATA_DIR / "defined_namespaces/mf.ttl",
        TEST_DATA_DIR / "defined_namespaces/qb.ttl",
        TEST_DATA_DIR / "defined_namespaces/qt.ttl",
        TEST_DATA_DIR / "defined_namespaces/rdfs.ttl",
        TEST_DATA_DIR / "defined_namespaces/rdftest.ttl",
        TEST_DATA_DIR / "defined_namespaces/rdf.ttl",
        TEST_DATA_DIR / "defined_namespaces/ut.n3",
    )
)

POFilterType = Tuple[Optional[URIRef], Optional[URIRef]]
POFiltersType = Iterable[POFilterType]

MarkType = Union[MarkDecorator, Collection[Union[MarkDecorator, Mark]]]
MarksDictType = Dict[str, Union[MarkDecorator, Collection[Union[MarkDecorator, Mark]]]]


@dataclass
class Manifest:
    graph: Graph
    identifier: IdentifiedNode
    public_id: Optional[str] = None

    @classmethod
    def from_graph(
        cls, graph: Graph, public_id: Optional[str] = None
    ) -> Generator["Manifest", None, None]:
        for identifier in graph.subjects(RDF.type, MF.Manifest):
            manifest = Manifest(graph, identifier, public_id)
            yield manifest
            yield from manifest.included()

    @classmethod
    def from_sources(
        cls, *sources: GraphSourceType, public_id: Optional[str] = None
    ) -> Generator["Manifest", None, None]:
        for source in sources:
            graph = load_sources(source, public_id=public_id)
            yield from cls.from_graph(graph, public_id)

    def included(self) -> Generator["Manifest", None, None]:
        for includes in self.graph.subjects(RDF.type, MF.include):
            for include in self.graph.items(includes):
                path: Path = file_uri_to_path(include)
                source = GraphSource.from_path(path, self.public_id)
                graph = source.load()
                yield from Manifest.from_graph(graph, self.public_id)

    def entires(
        self,
        exclude: Optional[POFiltersType] = None,
        include: Optional[POFiltersType] = None,
    ) -> Generator["ManifestEntry", None, None]:
        for entries in self.graph.objects(self.identifier, MF.entries):
            for entry_iri in self.graph.items(entries):
                entry = ManifestEntry(self, entry_iri)
                if exclude is not None and entry.check_filters(exclude):
                    continue
                if include is not None and not entry.check_filters(include):
                    continue
                yield entry

    def params(
        self,
        exclude: Optional[POFiltersType] = None,
        include: Optional[POFiltersType] = None,
        mark_dict: Optional[MarksDictType] = None,
    ) -> Generator["ParameterSet", None, None]:
        for entry in self.entires(exclude, include):
            yield entry.param(mark_dict)


def params_from_sources(
    *sources: GraphSourceType,
    public_id: Optional[str] = None,
    exclude: Optional[POFiltersType] = None,
    include: Optional[POFiltersType] = None,
    mark_dict: Optional[MarksDictType] = None,
) -> Generator["ParameterSet", None, None]:
    for manifest in Manifest.from_sources(*sources, public_id=public_id):
        yield from manifest.params(include, exclude, mark_dict)


IdentifierT = TypeVar("IdentifierT", bound=Identifier)


# @dataclass
# class ManifestEntryGenerator:
#     sources: List[Path]
#     public_id: str
#     include: Optional[POFiltersType] = None
#     exclude: Optional[POFiltersType] = None
#     marks_dict: MarksDictType = field(default_factory=dict)


@dataclass
class ManifestEntry:
    manifest: Manifest
    identifier: IdentifiedNode
    type: IdentifiedNode = field(init=False)
    mf_action: Optional[Identifier] = field(init=False)
    mf_result: Optional[Identifier] = field(init=False)

    def __post_init__(self) -> None:
        # types = list(self.graph.objects(self.identifier, RDF.type))
        # assert len(types) == 1
        # self.type = types[0]
        type = self.value(RDF.type, IdentifiedNode)
        assert type is not None
        self.type = type

        self.mf_action = self.value(MF.action, Identifier)
        self.mf_result = self.value(MF.result, Identifier)

    @property
    def graph(self) -> Graph:
        return self.manifest.graph

    def param(self, mark_dict: Optional[MarksDictType] = None) -> ParameterSet:
        id = f"{self.identifier}"
        marks: MarkType = tuple()
        if mark_dict is not None:
            marks = mark_dict.get(id, marks)
        return pytest.param(self, id=f"{self.identifier}", marks=marks)

    # @property
    # def mf_action(self) -> Optional[URIRef]:
    #     return self.value(MF.action, URIRef)

    # @property
    # def mf_result(self) -> Optional[URIRef]:
    #     return self.value(MF.result, URIRef)

    def value(
        self, predicate: Identifier, value_type: Type[IdentifierT]
    ) -> Optional[IdentifierT]:
        value = self.graph.value(self.identifier, predicate)
        if value is not None:
            assert isinstance(value, value_type)
        return value

    def check_filters(self, filters: POFiltersType) -> bool:
        for filter in filters:
            if (self.identifier, filter[0], filter[1]) in self.graph:
                return True
        return False


def local_file_uri(file_uri: str, public_base: str, local_path: Path) -> str:
    return file_uri.replace(public_base, local_path.as_uri())


def local_file_path(file_uri: str, public_base: str, local_path: Path) -> str:
    return file_uri_to_path(local_file_uri(file_uri, public_base, local_path))
