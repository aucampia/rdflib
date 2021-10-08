from io import IOBase
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
    IO,
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
    Callable,
)
import inspect
from rdflib.plugin import PluginException
from rdflib.serializer import Serializer
import enum
from contextlib import ExitStack

EG = Namespace("http://example.com/")


class GraphType(str, enum.Enum):
    QUAD = enum.auto()
    TRIPLE = enum.auto()


class FormatInfo(NamedTuple):
    serializer_name: str
    deserializer_name: str
    graph_types: Set[GraphType]
    encodings: Set[str]


class FormatInfos(Dict[str, FormatInfo]):
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

    def select(
        self,
        *,
        name: Optional[Set[str]] = None,
        graph_type: Optional[Set[GraphType]] = None,
    ) -> Iterable[FormatInfo]:
        for format in self.values():
            if graph_type is not None and not graph_type.isdisjoint(format.graph_types):
                yield format
            if name is not None and format.serializer_name in name:
                yield format

    @classmethod
    def make_graph(self, format_info: FormatInfo) -> Graph:
        if GraphType.QUAD in format_info.graph_types:
            return ConjunctiveGraph()
        else:
            return Graph()

    @classmethod
    def make(cls) -> "FormatInfos":
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


format_infos = FormatInfos.make()


class TestSerialize(unittest.TestCase):
    def setUp(self) -> None:
        self.triple = (
            EG["subject"],
            EG["predicate"],
            EG["object"],
        )
        self.context = EG["graph"]
        self.quad = (*self.triple, self.context)

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
                names.intersection(format_infos.keys()),
                set(),
                f"serializers does not include any of {names}",
            )

    def assert_graphs_equal(self, lhs: Graph, rhs: Graph) -> None:
        lhs_has_quads = hasattr(lhs, "quads")
        rhs_has_quads = hasattr(rhs, "quads")
        lhs_set: Set[Any]
        rhs_set: Set[Any]
        if lhs_has_quads and rhs_has_quads:
            lhs = cast(ConjunctiveGraph, lhs)
            rhs = cast(ConjunctiveGraph, rhs)
            lhs_set, rhs_set = GraphHelper.quad_sets([lhs, rhs])
        else:
            lhs_set, rhs_set = GraphHelper.triple_sets([lhs, rhs])
        self.assertEqual(lhs_set, rhs_set)
        self.assertTrue(len(lhs_set) > 0)
        self.assertTrue(len(rhs_set) > 0)

    def check_data_string(self, data: str, format: str) -> None:
        self.assertIsInstance(data, str)
        format_info = format_infos[format]
        graph_check = FormatInfos.make_graph(format_info)
        graph_check.parse(data=data, format=format_info.deserializer_name)
        self.assert_graphs_equal(self.graph, graph_check)

    def check_data_bytes(self, data: bytes, format: str, encoding: str) -> None:
        self.assertIsInstance(data, bytes)

        # double check that encoding is right
        data_str = data.decode(encoding)
        format_info = format_infos[format]
        graph_check = FormatInfos.make_graph(format_info)
        graph_check.parse(data=data_str, format=format_info.deserializer_name)
        self.assert_graphs_equal(self.graph, graph_check)

        # actual check
        # TODO FIXME : handle other encodings
        if encoding == "utf-8":
            graph_check = FormatInfos.make_graph(format_info)
            graph_check.parse(data=data, format=format_info.deserializer_name)
            self.assert_graphs_equal(self.graph, graph_check)

    def check_file(self, source: PurePath, format: str, encoding: str) -> None:
        source = Path(source)
        format_info = format_infos[format]

        # double check that encoding is right
        data_str = source.read_text(encoding=encoding)
        graph_check = FormatInfos.make_graph(format_info)
        # print(
        #     {
        #         "format_info": format_info,
        #         "format_info.deserializer_name": format_info.deserializer_name,
        #     }
        # )
        # print("data_str", data_str)
        graph_check.parse(data=data_str, format=format_info.deserializer_name)
        self.assert_graphs_equal(self.graph, graph_check)

        self.assertTrue(source.exists())
        # actual check
        # TODO FIXME : This should work for all encodings, not just utf-8
        if encoding == "utf-8":
            graph_check = FormatInfos.make_graph(format_info)
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
        test_formats = format_infos.keys()
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
                for format_info in format_infos.values()
            )
        ):

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
        # outfile = self.tmpdir / "output"
        counter = 0

        def filerefx(
            ref: Union[
                str,
                PurePath,
                Callable[[ExitStack], IO[bytes]],
                Callable[[ExitStack], IO[str]],
            ],
            stack: ExitStack,
        ) -> Union[str, PurePath, IO[bytes], IO[str]]:
            if callable(ref):
                return ref(stack)
            return ref

        def filerefs() -> List[
            Tuple[
                Union[
                    str,
                    PurePath,
                    Callable[[ExitStack], IO[bytes]],
                    Callable[[ExitStack], IO[str]],
                ],
                Path,
            ]
        ]:
            result: List[
                Tuple[
                    Union[
                        str,
                        PurePath,
                        Callable[[ExitStack], IO[bytes]],
                        Callable[[ExitStack], IO[str]],
                    ],
                    Path,
                ]
            ] = []
            path = self.tmpdir / "output-path"
            result.append((path, path))
            path = self.tmpdir / "output-purepath"
            result.append((PurePath(path), path))
            path = self.tmpdir / "output-strpath"
            result.append((f"{path}", path))
            path = self.tmpdir / "output-uri"
            result.append((path.as_uri(), path))
            nonlocal counter
            counter += 1
            result.append(
                (
                    lambda stack: stack.enter_context(
                        (self.tmpdir / f"output-iobytes-{counter}").open("wb")
                    ),
                    self.tmpdir / f"output-iobytes-{counter}",
                )
            )
            # result.append(
            #     (
            #         lambda: (self.tmpdir / "output-iostr").open("w"),
            #         self.tmpdir / "output-iostr",
            #     )
            # )
            # path = self.tmpdir / "output-iostr"
            # result.append((lambda: path.open("w"), path))
            return result

        for (format, encoding, file_info) in itertools.chain(
            *(
                itertools.product(
                    {format_info.serializer_name},
                    format_info.encodings,
                    filerefs(),
                )
                for format_info in format_infos.select(name={"xml"})
                # for format_info in format_infos.values()
            )
        ):
            fileref, outfile = file_info

            print({"format": format, "encoding": encoding, "file_info": file_info})

            # if isinstance(fileref, IOBase):
            #     self.assertFalse(fileref.closed)
            #     print({"fileref.closed": fileref.closed})

            def check(_graph: Graph) -> None:
                with self.subTest(
                    format=format,
                    encoding=encoding,
                    fileref=fileref,
                    caller=inspect.stack()[1],
                ):
                    print("outfile.read_text() =", outfile.read_text())
                    self.check_file(outfile, format, encoding)

            with ExitStack() as stack:
                if (format, encoding) == ("turtle", "utf-8"):
                    check(self.graph.serialize(filerefx(fileref, stack)))
                    check(self.graph.serialize(filerefx(fileref, stack), encoding=None))
                if format == "turtle":
                    check(
                        self.graph.serialize(
                            filerefx(fileref, stack), encoding=encoding
                        )
                    )
                if encoding == sys.getdefaultencoding():
                    check(self.graph.serialize(filerefx(fileref, stack), format))
                    check(self.graph.serialize(filerefx(fileref, stack), format, None))
                    check(
                        self.graph.serialize(
                            filerefx(fileref, stack), format, None, None
                        )
                    )

                check(
                    self.graph.serialize(
                        filerefx(fileref, stack), format, encoding=encoding
                    )
                )
                check(
                    self.graph.serialize(
                        filerefx(fileref, stack), format, None, encoding
                    )
                )


if __name__ == "__main__":
    unittest.main()
