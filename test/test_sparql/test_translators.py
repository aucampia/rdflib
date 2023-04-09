from unittest.mock import Mock

from rdflib import Graph
from rdflib._contrib.sparql.translators import ValuesToTheLeftOfTheJoin
from rdflib.namespace import RDFS, Namespace
from rdflib.plugins.sparql.algebra import translateUpdate
from rdflib.plugins.sparql.parser import parseUpdate
from rdflib.plugins.sparql.processor import (
    SPARQLProcessor,
    SPARQLUpdateProcessor,
    parseQuery,
    translateQuery,
)
from rdflib.plugins.sparql.sparql import Query, Update
from rdflib.query import ResultRow


def test_values_to_left():
    query_slow = """
    PREFIX ex:<https://example.org/>

    SELECT ?x {
    ?x ?y ?z .
    VALUES (?x) {
        (ex:1)
        (ex:2)
        (ex:3)
    }
    }
    """

    query_fast = """
    PREFIX ex:<https://example.org/>

    SELECT ?x {
    VALUES (?x) {
        (ex:1)
        (ex:2)
        (ex:3)
    }
        ?x ?y ?z .
    }
    """

    qs = _prepare_query(query_slow)
    qf = _prepare_query(query_fast)
    assert qs != qf
    qso = ValuesToTheLeftOfTheJoin.translate(qs)

    assert qso.algebra == qf.algebra


def _prepare_query(query_string: str) -> Query:
    parse_tree = parseQuery(query_string)
    query = translateQuery(parse_tree, None, {})
    return query


def _prepare_update(update_string: str) -> Update:
    parse_tree = parseUpdate(update_string)
    update = translateUpdate(parse_tree, None, {})
    return update


def test_graph_query(rdfs_graph: Graph):
    requested_query_string = """
    PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?x {
        ?x rdfs:label "subClassOf".
    }
    """

    translated_query_string = """
    PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?x {
        ?x rdfs:label "subPropertyOf".
    }
    """

    requested_query = _prepare_query(requested_query_string)
    translated_query = _prepare_query(translated_query_string)

    translate = Mock(return_value=translated_query)

    processor = SPARQLProcessor(rdfs_graph, translators=[translate])
    result = rdfs_graph.query(requested_query, processor)
    rows = []
    for row in result:
        assert isinstance(row, ResultRow)
        rows.append(row.asdict())

    assert rows == [{"x": RDFS.subPropertyOf}]

    translate.assert_called_once_with(requested_query)


EGNS = Namespace("https://example.com/")


def test_graph_update():
    requested_update_string = """
    PREFIX example: <https://example.com/>
    INSERT {
        example:subject example:predicate example:object1 .
    }
    WHERE { }
    """

    translated_update_string = requested_update_string.replace(
        "example:object1", "example:object2"
    )

    requested_update = _prepare_update(requested_update_string)
    translated_update = _prepare_update(translated_update_string)

    translate = Mock(return_value=translated_update)

    graph = Graph()
    processor = SPARQLUpdateProcessor(graph, translators=[translate])
    graph.update(requested_update, processor)

    assert EGNS.object2 == graph.value(EGNS.subject, EGNS.predicate)

    translate.assert_called_once_with(requested_update)
