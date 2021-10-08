from test.testutils import GraphHelper
import unittest
from rdflib import Graph, Namespace
from tempfile import TemporaryDirectory
from pathlib import Path
import json
import io
import csv
import inspect

EG = Namespace("http://example.com/")


class TestSerializeTabular(unittest.TestCase):
    def setUp(self) -> None:
        graph = Graph()
        triples = [
            (EG["e0"], EG["a0"], EG["e1"]),
            (EG["e0"], EG["a0"], EG["e2"]),
            (EG["e0"], EG["a0"], EG["e3"]),
            (EG["e1"], EG["a1"], EG["e2"]),
            (EG["e1"], EG["a1"], EG["e3"]),
            (EG["e2"], EG["a2"], EG["e3"]),
        ]
        GraphHelper.add_triples(graph, triples)

        query = """
        PREFIX eg: <http://example.com/>
        SELECT ?subject ?predicate ?object WHERE {
            VALUES ?predicate { eg:a1 }
            ?subject ?predicate ?object
        } ORDER BY ?object
        """
        self.result = graph.query(query)
        self.result_table = [
            ["subject", "predicate", "object"],
            ["http://example.com/e1", "http://example.com/a1", "http://example.com/e2"],
            ["http://example.com/e1", "http://example.com/a1", "http://example.com/e3"],
        ]

        self._tmpdir = TemporaryDirectory()
        self.tmpdir = Path(self._tmpdir.name)

        return super().setUp()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def formats(self) -> None:



    def test_serialize_table_csv_str(self) -> None:
        format = "csv"

        def check(data: str) -> None:
            with self.subTest(caller=inspect.stack()[1]):
                self.assertIsInstance(data, str)
                data_io = io.StringIO(data)
                data_reader = csv.reader(data_io, "unix")
                data_rows = list(data_reader)
                self.assertEqual(data_rows, self.result_table)

        # check(self.result.serialize())
        # check(self.result.serialize(None))
        # check(self.result.serialize(None, None))
        check(self.result.serialize(None, None, None))
        check(self.result.serialize(None, None, format))
        check(self.result.serialize(format=format))
        # check(self.result.serialize(destination=None))
        check(self.result.serialize(destination=None, format=format))
        check(self.result.serialize(destination=None, encoding=None, format=format))

    def test_serialize_table_csv_bytes(self) -> None:
        encoding = "utf-8"
        format = "csv"

        def check(data: bytes) -> None:
            with self.subTest(caller=inspect.stack()[1]):
                self.assertIsInstance(data, bytes)
                data_str = data.decode(encoding)
                data_io = io.StringIO(data_str)
                data_reader = csv.reader(data_io, "unix")
                data_rows = list(data_reader)
                self.assertEqual(data_rows, self.result_table)

        # check(self.result.serialize(None, encoding))
        # check(self.result.serialize(None, encoding, None))
        check(self.result.serialize(None, encoding, format))
        check(self.result.serialize(encoding=encoding, format=format))
        # check(self.result.serialize(destination=None, encoding=encoding))
        check(self.result.serialize(destination=None, encoding=encoding, format=format))

    def test_serialize_table_csv_file(self) -> None:
        outfile = self.tmpdir / "output.csv"

        self.assertFalse(outfile.exists())

        def check(none: None) -> None:
            with self.subTest(caller=inspect.stack()[1]):
                self.assertTrue(outfile.exists())
                with outfile.open("r") as file_io:
                    data_reader = csv.reader(file_io, "unix")
                    data_rows = list(data_reader)
                self.assertEqual(data_rows, self.result_table)

        check(self.result.serialize(outfile))

        # self.result.serialize(outfile)
        # check_file()

    def test_serialize_table_json(self) -> None:
        format = "json"

        json_data = {
            "head": {"vars": ["subject", "predicate", "object"]},
            "results": {
                "bindings": [
                    {
                        "subject": {
                            "type": "uri",
                            "value": "http://example.com/e1",
                        },
                        "predicate": {
                            "type": "uri",
                            "value": "http://example.com/a1",
                        },
                        "object": {
                            "type": "uri",
                            "value": "http://example.com/e2",
                        },
                    },
                    {
                        "subject": {
                            "type": "uri",
                            "value": "http://example.com/e1",
                        },
                        "predicate": {
                            "type": "uri",
                            "value": "http://example.com/a1",
                        },
                        "object": {
                            "type": "uri",
                            "value": "http://example.com/e3",
                        },
                    },
                ]
            },
        }

        def check(returned: str) -> None:
            with self.subTest(caller=inspect.stack()[1]):
                obj = json.loads(returned)
                self.assertEqual(obj, json_data)

        check(self.result.serialize(format=format))
        check(self.result.serialize(None, format=format))
        check(self.result.serialize(None, None, format=format))
        check(self.result.serialize(None, None, format))
        check(self.result.serialize(destination=None, format=format))
        check(self.result.serialize(destination=None, encoding=None, format=format))


if __name__ == "__main__":
    unittest.main()
