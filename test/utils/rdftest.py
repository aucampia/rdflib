import enum
from dataclasses import dataclass, field
from test.data import TEST_DATA_DIR
from test.utils.graph import GraphSource, GraphSourceType, load_sources
from typing import Generator, List, Set

from rdflib.graph import Graph


class LoadFlag(enum.Enum):
    PROCESS_INCLUDES = enum.auto()


@dataclass
class Manifest:

    graph: Graph = field(init=False, default_factory=Graph)

    # source: GraphSource
    # report_prefix: str
    # _graph: Graph = field(init=False, default_factory=Graph)

    # def _load(self) -> None:
    #     load_sources(
    #         self.source,
    #         graph=self._graph,
    #     )

    # def __post_init__(self) -> None:
    #     self._load()

    @classmethod
    def load(
        cls, *sources: GraphSourceType, flags: Set[LoadFlag] = None
    ) -> Generator["Manifest", None, None]:
        if flags is None:
            flags = set()
        graph = load_sources(*sources)

        if LoadFlag.PROCESS_INCLUDES in flags:
            for include in graph.objects(m, MF.include):
                for i in g.items(col):
                    for x in read_manifest(i):
                        yield x
