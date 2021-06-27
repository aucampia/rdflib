from typing import ClassVar
from rdflib.graph import Graph
from .testutils import ServedSimpleHTTPMock
import unittest

class TestStore(unittest.TestCase):
    query_path: ClassVar[str]
    update_path: ClassVar[str]
    httpmock: ClassVar[ServedSimpleHTTPMock]

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.httpmock = ServedSimpleHTTPMock()
        cls.query_path = f"{cls.httpmock.url}/db/sparql"
        cls.update_path = f"{cls.httpmock.url}/db/update"

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.httpmock.stop()

    def setUp(self):
        self.httpmock.reset()
        self.graph = Graph(store="SPARQLUpdateStore")
        self.graph.open(self.path, create=True)

    def tearDown(self):
        self.graph.close()
