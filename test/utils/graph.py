from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional, Set, Tuple, Union

from rdflib.graph import Graph
from rdflib.namespace import RDFS
from rdflib.term import IdentifiedNode, URIRef
from rdflib.util import guess_format


@dataclass(frozen=True)
class GraphSource:
    path: Path
    format: str
    public_id: Optional[str] = None

    @classmethod
    def from_path(cls, path: Path, public_id: Optional[str] = None) -> "GraphSource":
        format = guess_format(f"{path}")
        if format is None:
            raise ValueError(f"could not guess format for source {path}")

        return cls(path, format, public_id)

    @classmethod
    def from_paths(cls, *paths: Path) -> Tuple["GraphSource", ...]:
        result = []
        for path in paths:
            result.append(cls.from_path(path))
        return tuple(result)

    def load(
        self, graph: Optional[Graph] = None, public_id: Optional[str] = None
    ) -> Graph:
        if graph is None:
            graph = Graph()
        graph.parse(
            source=self.path,
            format=self.format,
            publicID=self.public_id if public_id is None else public_id,
        )
        return graph

    # @classmethod
    # def load_sources(cls, *sources: Union["GraphSource", Path], graph: Optional[Graph] = None) -> Graph:
    #     if graph is None:
    #         graph = Graph()
    #     for source in sources:
    #         if isinstance(source, Path):
    #             source = GraphSource.from_path(source)
    #         graph.parse(source=source.path, format=source.format)
    #     return graph


GraphSourceType = Union[GraphSource, Path]


def load_sources(
    *sources: GraphSourceType,
    graph: Optional[Graph] = None,
    public_id: Optional[str] = None,
) -> Graph:
    if graph is None:
        graph = Graph()
    for source in sources:
        if isinstance(source, Path):
            source = GraphSource.from_path(source)
        source.load(graph, public_id)
    return graph


@lru_cache(maxsize=None)
def cached_graph(
    sources: Tuple[Union[GraphSource, Path], ...], public_id: Optional[str] = None
) -> Graph:
    return load_sources(*sources, public_id=public_id)


def subclasses_of(graph: Graph, node: IdentifiedNode) -> Set[IdentifiedNode]:
    return set(graph.transitive_subjects(RDFS.subClassOf, node))


def superclasses_of(graph: Graph, node: IdentifiedNode) -> Set[IdentifiedNode]:
    return set(graph.transitive_objects(node, RDFS.subClassOf))


def is_subclass_of(graph: Graph, node: IdentifiedNode, cls: URIRef) -> bool:
    return cls in subclasses_of(graph, node)


def is_superclass_of(graph: Graph, node: IdentifiedNode, cls: URIRef) -> bool:
    return cls in superclasses_of(graph, node)
