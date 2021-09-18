import unittest
from rdflib import Graph, URIRef
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pathlib import Path, PurePath


class TestSerialize(unittest.TestCase):
    def setUp(self) -> None:

        graph = Graph()
        subject = URIRef("example:subject")
        predicate = URIRef("example:predicate")
        object = URIRef("example:object")
        self.triple = (
            subject,
            predicate,
            object,
        )
        graph.add(self.triple)
        self.graph = graph

        self._tmpdir = TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)

        return super().setUp()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def check_file(self, source: PurePath, format: str) -> None:
        source = Path(source)
        self.assertTrue(source.exists())
        graph_check = Graph()
        graph_check.parse(source=source, format=format)
        # self.assertEqual(self.triple, next(iter(graph_check)))
        self.assertEqual(self.triple, (None, None, None))

    def check_data_string(self, data: str, format: str) -> None:
        self.assertIsInstance(data, str)
        graph_check = Graph()
        graph_check.parse(data=data, format=format)
        self.assertEqual(self.triple, next(iter(graph_check)))

    def check_data_bytes(self, data: bytes, format: str) -> None:
        self.assertIsInstance(data, bytes)
        graph_check = Graph()
        graph_check.parse(data=data, format=format)
        self.assertEqual(self.triple, next(iter(graph_check)))

    def test_serialize_to_purepath(self) -> None:
        format = "nt"
        with TemporaryDirectory() as td:
            tfpath = PurePath(td) / "out.nt"
            self.graph.serialize(destination=tfpath, format=format)
            self.check_file(tfpath, format)

    def test_serialize_to_path(self) -> None:
        format = "nt"
        with NamedTemporaryFile() as tf:
            tfpath = Path(tf.name)
            self.graph.serialize(destination=tfpath, format=format)
            self.check_file(tfpath, format)

    def test_serialize_to_neturl(self) -> None:
        with self.assertRaises(ValueError) as raised:
            self.graph.serialize(destination="http://example.com/", format="nt")
        self.assertIn("destination", f"{raised.exception}")

    def test_serialize_to_fileurl(self) -> None:
        format = "nt"
        with TemporaryDirectory() as td:
            tfpath = Path(td) / "out.nt"
            tfurl = tfpath.as_uri()
            self.assertRegex(tfurl, r"^file:")
            self.assertFalse(tfpath.exists())
            self.graph.serialize(destination=tfurl, format="nt")
            self.check_file(tfpath, format)

    def test_str(self) -> None:
        format = "ttl"

        def check(data: str) -> None:
            self.check_data_string(data, format=format)

        check(self.graph.serialize())
        check(self.graph.serialize(None, format))
        check(self.graph.serialize(None, format, None, None))
        check(self.graph.serialize(None, format=format))

    def test_bytes(self) -> None:
        format = "ttl"
        encoding = "utf-8"

        def check(data: bytes) -> None:
            self.check_data_bytes(data, format=format)

        check(self.graph.serialize(encoding=encoding))
        check(self.graph.serialize(None, format, encoding=encoding))
        check(self.graph.serialize(None, format, None, encoding=encoding))
        check(self.graph.serialize(None, format, encoding=encoding))
        check(self.graph.serialize(None, format=format, encoding=encoding))

    def test_file(self) -> None:
        format = "ttl"
        outfile = self.tmpdir / "output.ttl"
        encoding = "utf-8"

        def check(graph: Graph) -> None:
            self.check_file(outfile, format=format)

        check(self.graph.serialize(outfile))
        check(self.graph.serialize(outfile, format))
        check(self.graph.serialize(outfile, format, None))
        check(self.graph.serialize(outfile, format, None, None))
        check(self.graph.serialize(outfile, format, None, encoding))
        # check(self.graph.serialize(encoding=encoding))
        # check(self.graph.serialize(None, format, encoding=encoding))
        # check(self.graph.serialize(None, format, None, encoding=encoding))
        # check(self.graph.serialize(None, format, encoding=encoding))
        # check(self.graph.serialize(None, format=format, encoding=encoding))


if __name__ == "__main__":
    unittest.main()
