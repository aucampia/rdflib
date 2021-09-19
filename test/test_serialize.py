from rdflib.namespace import Namespace
import unittest
from rdflib import Graph, URIRef
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pathlib import Path, PurePath
import sys
import itertools
from typing import Iterable, Tuple, Union
import inspect
from rdflib.plugin import PluginException

EG = Namespace("http://example.com/")


class TestSerialize(unittest.TestCase):
    def setUp(self) -> None:

        graph = Graph()
        # subject = URIRef("example:subject")
        # predicate = URIRef("example:predicate")
        # object = URIRef("example:object")
        self.triple = (
            EG["subject"],
            EG["predicate"],
            EG["object"],
        )
        graph.add(self.triple)
        self.graph = graph

        self._tmpdir = TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)

        return super().setUp()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def check_data_string(self, data: str, format: str) -> None:
        # print(f"format = {format}, data = {data}")
        self.assertIsInstance(data, str)
        graph_check = Graph()
        graph_check.parse(data=data, format=format)
        self.assertEqual(self.triple, next(iter(graph_check)))

    def check_data_bytes(self, data: bytes, format: str, encoding: str) -> None:
        self.assertIsInstance(data, bytes)
        # double check that encoding is right
        print(f"format = {format}, encoding = {encoding}\ndata = {data!r}")
        data_str = data.decode(encoding)
        print(f"data_str = {data_str!r}")
        graph_check = Graph()
        graph_check.parse(data=data_str, format=format)
        self.assertEqual(self.triple, next(iter(graph_check)))

        # actual check
        # TODO FIXME : This should work for all encodings, not just utf-8
        if encoding == "utf-8":
            graph_check = Graph()
            graph_check.parse(data=data, format=format)
            self.assertEqual(self.triple, next(iter(graph_check)))

    def check_file(self, source: PurePath, format: str, encoding: str) -> None:
        source = Path(source)
        self.assertTrue(source.exists())

        # double check that encoding is right
        data = source.read_bytes()
        print(f"format = {format}, encoding = {encoding}\ndata = {data!r}")
        data_str = source.read_text(encoding=encoding)
        graph_check = Graph()
        graph_check.parse(data=data_str, format=format)
        self.assertEqual(self.triple, next(iter(graph_check)))

        # actual check
        # TODO FIXME : This should work for all encodings, not just utf-8
        if encoding == "utf-8":
            graph_check = Graph()
            graph_check.parse(source=source, format=format)
            self.assertEqual(self.triple, next(iter(graph_check)))

    # def test_serialize_to_purepath(self) -> None:
    #     format = "nt"
    #     with TemporaryDirectory() as td:
    #         tfpath = PurePath(td) / "out.nt"
    #         self.graph.serialize(destination=tfpath, format=format)
    #         self.check_file(tfpath, format)

    # def test_serialize_to_path(self) -> None:
    #     format = "nt"
    #     with NamedTemporaryFile() as tf:
    #         tfpath = Path(tf.name)
    #         self.graph.serialize(destination=tfpath, format=format)
    #         self.check_file(tfpath, format)

    def test_serialize_to_neturl(self) -> None:
        with self.assertRaises(ValueError) as raised:
            self.graph.serialize(destination="http://example.com/", format="nt")
        self.assertIn("destination", f"{raised.exception}")

    def test_serialize_badformat(self) -> None:
        with self.assertRaises(PluginException) as raised:
            self.graph.serialize(destination="http://example.com/", format="badformat")
        self.assertIn("badformat", f"{raised.exception}")

    # def test_serialize_to_fileurl(self) -> None:
    #     format = "nt"
    #     with TemporaryDirectory() as td:
    #         tfpath = Path(td) / "out.nt"
    #         tfurl = tfpath.as_uri()
    #         self.assertRegex(tfurl, r"^file:")
    #         self.assertFalse(tfpath.exists())
    #         self.graph.serialize(destination=tfurl, format="nt")
    #         self.check_file(tfpath, format)

    def test_str(self) -> None:
        formats = ["ttl", "nt", "xml", "nt"]
        for format in formats:

            def check(data: str) -> None:
                with self.subTest(format=format, caller=inspect.stack()[1]):
                    self.check_data_string(data, format=format)

            if format == "ttl":
                check(self.graph.serialize())
            check(self.graph.serialize(None, format))
            check(self.graph.serialize(None, format, encoding=None))
            check(self.graph.serialize(None, format, None, None))
            check(self.graph.serialize(None, format=format))
            check(self.graph.serialize(None, format=format, encoding=None))

    def test_bytes(self) -> None:
        formats = ["ttl"]
        encodings = ["utf-16", "utf-8", "latin-1"]
        # TODO: FIXME: XML with non utf-8 encodings
        for (format, encoding) in itertools.chain(
            itertools.product(formats, encodings), [("nt", "ascii"), ("xml", "utf-8")]
        ):

            def check(data: bytes) -> None:
                with self.subTest(
                    format=format, encoding=encoding, caller=inspect.stack()[1]
                ):
                    self.check_data_bytes(data, format=format, encoding=encoding)

            if format == "ttl":
                check(self.graph.serialize(encoding=encoding))
            check(self.graph.serialize(None, format, encoding=encoding))
            check(self.graph.serialize(None, format, None, encoding=encoding))
            check(self.graph.serialize(None, format, encoding=encoding))
            check(self.graph.serialize(None, format=format, encoding=encoding))

    def test_file(self) -> None:
        formats = ["ttl"]
        encodings = ["utf-16", "utf-8", "latin-1"]
        outfile = self.tmpdir / "output"

        def filerefs(path: Path) -> Iterable[Union[str, PurePath]]:
            # return [path, PurePath(path), f"{path}", path.as_uri()]
            return [path]

        for (format, encoding, fileref) in itertools.chain(
            itertools.product(formats, encodings, filerefs(outfile)),
            itertools.product(["nt"], ["ascii"], filerefs(outfile)),
            itertools.product(["xml"], ["utf-8"], filerefs(outfile)),
        ):

            def check(graph: Graph) -> None:
                with self.subTest(
                    format=format,
                    encoding=encoding,
                    fileref=fileref,
                    caller=inspect.stack()[1],
                ):
                    self.check_file(outfile, format, encoding)

            if (format, encoding) == ("ttl", "utf-8"):
                check(self.graph.serialize(fileref))
                check(self.graph.serialize(fileref, encoding=None))
            if format == "ttl":
                check(self.graph.serialize(fileref, encoding=encoding))
            if encoding == sys.getdefaultencoding():
                check(self.graph.serialize(fileref, format))
                check(self.graph.serialize(fileref, format, None))
                check(self.graph.serialize(fileref, format, None, None))

            check(self.graph.serialize(fileref, format, encoding=encoding))
            check(self.graph.serialize(fileref, format, None, encoding))


if __name__ == "__main__":
    unittest.main()
