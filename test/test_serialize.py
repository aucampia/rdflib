from rdflib import graph
from rdflib.graph import ConjunctiveGraph
import tempfile
import os
import sys
from rdflib.term import Node
from test.testutils import GraphHelper, get_unique_plugin_names, get_unique_plugins
from rdflib.namespace import Namespace
import unittest
from rdflib import Graph, URIRef
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pathlib import Path, PurePath
import sys
import itertools
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)
import inspect
from rdflib.plugin import PluginException
from rdflib.serializer import Serializer
import enum

import logging

logging.basicConfig(
    level=os.environ.get("PYLOGGING_LEVEL", logging.DEBUG),
    stream=sys.stderr,
    datefmt="%Y-%m-%dT%H:%M:%S",
    format=(
        "%(asctime)s.%(msecs)03d %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
        "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
    ),
)


EG = Namespace("http://example.com/")


class GraphType(str, enum.Enum):
    QUAD = enum.auto()
    TRIPLE = enum.auto()


class FormatInfo(NamedTuple):
    serializer_name: str
    deserializer_name: str
    graph_types: Set[GraphType]
    encodings: Set[str]


class Formats(Dict[str, FormatInfo]):
    def add_format(
        self,
        serializer_name: str,
        *,
        deserializer_name: Optional[str] = None,
        graph_types: Set[GraphType],
        encodings: Set[str],
    ) -> None:
        self[serializer_name] = FormatInfo(
            serializer_name,
            serializer_name if deserializer_name is None else deserializer_name,
            {GraphType.QUAD, GraphType.TRIPLE} if graph_types is None else graph_types,
            encodings,
        )

    def select(self, *, graph_type: GraphType) -> Iterable[str]:
        for format in self.values():
            if graph_type in format.graph_types:
                yield format.serializer_name

    @classmethod
    def make_graph(self, format_info: FormatInfo) -> Graph:
        if GraphType.QUAD in format_info.graph_types:
            return ConjunctiveGraph()
        else:
            return Graph()

    @classmethod
    def make(cls) -> "Formats":
        result = cls()

        flexible_formats = {
            "trig",
        }
        for format in flexible_formats:
            result.add_format(
                format,
                graph_types={GraphType.TRIPLE, GraphType.QUAD},
                encodings={"utf-8"},
            )

        triple_only_formats = {
            "turtle",
            "nt11",
            "xml",
            "n3",
        }
        for format in triple_only_formats:
            result.add_format(
                format, graph_types={GraphType.TRIPLE}, encodings={"utf-8"}
            )

        quad_only_formats = {
            "nquads",
            "trig",
            "trix",
            "json-ld",
        }
        for format in quad_only_formats:
            result.add_format(format, graph_types={GraphType.QUAD}, encodings={"utf-8"})

        result.add_format(
            "pretty-xml",
            deserializer_name="xml",
            graph_types={GraphType.TRIPLE},
            encodings={"utf-8"},
        )
        result.add_format(
            "ntriples",
            graph_types={GraphType.TRIPLE},
            encodings={"ascii"},
        )

        return result


formats = Formats.make()


class TestSerialize(unittest.TestCase):
    def setUp(self) -> None:
        self.triple = (
            EG["subject"],
            EG["predicate"],
            EG["object"],
        )
        self.context = EG["graph"]
        # self.context = None
        self.quad = (*self.triple, self.context)

        # graph = Graph()
        # graph.add(self.triple)

        conjunctive_graph = ConjunctiveGraph()
        conjunctive_graph.add(self.quad)
        self.graph = conjunctive_graph

        self._tmpdir = TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)

        return super().setUp()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_graph(self) -> None:
        quad_set = GraphHelper.quad_set(self.graph)
        self.assertEqual(quad_set, {self.quad})

    def test_all_formats_specified(self) -> None:
        plugins = get_unique_plugins(Serializer)
        for plugin_refs in plugins.values():
            names = {plugin_ref.name for plugin_ref in plugin_refs}
            self.assertNotEqual(
                names.intersection(formats.keys()),
                set(),
                f"serializers does not include any of {names}",
            )

    def assert_graphs_equal(self, lhs: Graph, rhs: Graph) -> None:
        lhs_has_quads = hasattr(lhs, "quads")
        rhs_has_quads = hasattr(rhs, "quads")
        # self.assertEqual(lhs_has_quads, rhs_has_quads)
        lhs_set: Set[Any]
        rhs_set: Set[Any]
        if lhs_has_quads and rhs_has_quads:
            lhs = cast(ConjunctiveGraph, lhs)
            rhs = cast(ConjunctiveGraph, rhs)
            lhs_set, rhs_set = GraphHelper.quad_sets([lhs, rhs])
        else:
            lhs_set, rhs_set = GraphHelper.triple_sets([lhs, rhs])
        # print(f"lhs_set = {lhs_set}, rhs_set = {rhs_set}")
        self.assertTrue(len(lhs_set) > 0)
        self.assertTrue(len(rhs_set) > 0)
        self.assertEqual(lhs_set, rhs_set)

    def check_data_string(self, data: str, format: str) -> None:
        self.assertIsInstance(data, str)
        # if format == "trig":
        #     logging.debug("format = %s, data = %s", format, data)
        format_info = formats[format]
        graph_check = Formats.make_graph(format_info)
        graph_check.parse(data=data, format=format_info.deserializer_name)
        self.assert_graphs_equal(self.graph, graph_check)
        # graph_quads, graph_check_quads = GraphHelper.quad_sets(
        #     [self.graph, graph_check]
        # )
        # self.assertEqual(graph_quads, graph_check_quads)

    def check_data_bytes(self, data: bytes, format: str, encoding: str) -> None:
        self.assertIsInstance(data, bytes)

        # double check that encoding is right
        data_str = data.decode(encoding)

        format_info = formats[format]
        graph_check = Formats.make_graph(format_info)
        graph_check.parse(data=data_str, format=format_info.deserializer_name)

        # graph_check.parse(data=data_str, format=format)
        # self.assertEqual(self.triple, next(iter(graph_check)))
        self.assert_graphs_equal(self.graph, graph_check)

        # actual check
        # TODO FIXME : what about other encodings?
        if encoding == "utf-8":
            graph_check = Formats.make_graph(format_info)
            graph_check.parse(data=data, format=format_info.deserializer_name)
            self.assert_graphs_equal(self.graph, graph_check)
            # self.assertEqual(self.triple, next(iter(graph_check)))

    def check_file(self, source: PurePath, format: str, encoding: str) -> None:
        source = Path(source)
        self.assertTrue(source.exists())
        format_info = formats[format]

        # double check that encoding is right
        data_str = source.read_text(encoding=encoding)
        graph_check = Formats.make_graph(format_info)
        graph_check.parse(data=data_str, format=format_info.deserializer_name)
        self.assert_graphs_equal(self.graph, graph_check)

        # actual check
        # TODO FIXME : This should work for all encodings, not just utf-8
        if encoding == "utf-8":
            graph_check = Formats.make_graph(format_info)
            graph_check.parse(source=source, format=format_info.deserializer_name)
            self.assert_graphs_equal(self.graph, graph_check)

    def test_serialize_to_neturl(self) -> None:
        with self.assertRaises(ValueError) as raised:
            self.graph.serialize(destination="http://example.com/", format="nt")
        self.assertIn("destination", f"{raised.exception}")

    def test_serialize_badformat(self) -> None:
        with self.assertRaises(PluginException) as raised:
            self.graph.serialize(destination="http://example.com/", format="badformat")
        self.assertIn("badformat", f"{raised.exception}")

    def test_str(self) -> None:
        test_formats = formats.keys()
        # test_formats = {"json-ld"}
        for format in test_formats:

            def check(data: str) -> None:
                with self.subTest(format=format, caller=inspect.stack()[1]):
                    self.check_data_string(data, format=format)

            if format == "turtle":
                check(self.graph.serialize())
            check(self.graph.serialize(None, format))
            check(self.graph.serialize(None, format, encoding=None))
            check(self.graph.serialize(None, format, None, None))
            check(self.graph.serialize(None, format=format))
            check(self.graph.serialize(None, format=format, encoding=None))

    def test_bytes(self) -> None:
        for (format, encoding) in itertools.chain(
            *(
                itertools.product({format_info.serializer_name}, format_info.encodings)
                for format_info in formats.values()
            )
        ):
            print("format = ", format)
            print("encoding = ", encoding)

            def check(data: bytes) -> None:
                with self.subTest(
                    format=format, encoding=encoding, caller=inspect.stack()[1]
                ):
                    self.check_data_bytes(data, format=format, encoding=encoding)

            if format == "turtle":
                check(self.graph.serialize(encoding=encoding))
            check(self.graph.serialize(None, format, encoding=encoding))
            check(self.graph.serialize(None, format, None, encoding=encoding))
            check(self.graph.serialize(None, format, encoding=encoding))
            check(self.graph.serialize(None, format=format, encoding=encoding))

    def test_file(self) -> None:
        # formats = ["turtle"]
        # encodings = ["utf-16", "utf-8", "latin-1"]
        outfile = self.tmpdir / "output"

        def filerefs(path: Path) -> Iterable[Union[str, PurePath]]:
            return [path, PurePath(path), f"{path}", path.as_uri()]

        for (format, encoding, fileref) in itertools.chain(
            *(
                itertools.product(
                    {format_info.serializer_name},
                    format_info.encodings,
                    filerefs(outfile),
                )
                for format_info in formats.values()
            )
        ):
            print("format = ", format)
            print("encoding = ", encoding)
            print("fileref = ", fileref)
            # for (format, encoding, fileref) in itertools.chain(
            #     itertools.product(formats, encodings, filerefs(outfile)),
            #     itertools.product(["nt"], ["ascii"], filerefs(outfile)),
            #     itertools.product(["xml"], ["utf-8"], filerefs(outfile)),
            # ):

            def check(graph: Graph) -> None:
                with self.subTest(
                    format=format,
                    encoding=encoding,
                    fileref=fileref,
                    caller=inspect.stack()[1],
                ):
                    self.check_file(outfile, format, encoding)

            if (format, encoding) == ("turtle", "utf-8"):
                check(self.graph.serialize(fileref))
                check(self.graph.serialize(fileref, encoding=None))
            if format == "turtle":
                check(self.graph.serialize(fileref, encoding=encoding))
            if encoding == sys.getdefaultencoding():
                check(self.graph.serialize(fileref, format))
                check(self.graph.serialize(fileref, format, None))
                check(self.graph.serialize(fileref, format, None, None))

            check(self.graph.serialize(fileref, format, encoding=encoding))
            check(self.graph.serialize(fileref, format, None, encoding))


if __name__ == "__main__":
    unittest.main()
