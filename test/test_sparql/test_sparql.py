import logging
from pathlib import Path
from test.data import TEST_DATA_DIR
from test.utils import eq_
from test.utils.graph import GraphSourceType, cached_graph
from typing import Any, Callable, Mapping, Optional, Sequence, Type

import pytest
from pytest import MonkeyPatch

import rdflib.plugins.sparql
import rdflib.plugins.sparql.operators
import rdflib.plugins.sparql.parser
from rdflib import BNode, ConjunctiveGraph, Graph, Literal, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, RDFS, XSD, Namespace
from rdflib.plugins.sparql import prepareQuery, sparql
from rdflib.plugins.sparql.algebra import translateQuery
from rdflib.plugins.sparql.evaluate import evalPart
from rdflib.plugins.sparql.evalutils import _eval
from rdflib.plugins.sparql.parser import parseQuery
from rdflib.plugins.sparql.parserutils import prettify_parsetree
from rdflib.plugins.sparql.sparql import NotBoundError, SPARQLError
from rdflib.query import Result
from rdflib.term import Identifier, Node, Variable


def test_graph_prefix():
    """
    This is issue https://github.com/RDFLib/rdflib/issues/313
    """

    g1 = Graph()
    g1.parse(
        data="""
    @prefix : <urn:ns1:> .
    :foo <p> 42.
    """,
        format="n3",
    )

    g2 = Graph()
    g2.parse(
        data="""
    @prefix : <urn:somethingelse:> .
    <urn:ns1:foo> <p> 42.
    """,
        format="n3",
    )

    assert isomorphic(g1, g2)

    q_str = """
    PREFIX : <urn:ns1:>
    SELECT ?val
    WHERE { :foo ?p ?val }
    """
    q_prepared = prepareQuery(q_str)

    expected = [(Literal(42),)]

    eq_(list(g1.query(q_prepared)), expected)
    eq_(list(g2.query(q_prepared)), expected)

    eq_(list(g1.query(q_str)), expected)
    eq_(list(g2.query(q_str)), expected)


def test_variable_order():

    g = Graph()
    g.add((URIRef("http://foo"), URIRef("http://bar"), URIRef("http://baz")))
    res = g.query("SELECT (42 AS ?a) ?b { ?b ?c ?d }")

    row = list(res)[0]
    print(row)
    assert len(row) == 2
    assert row[0] == Literal(42)
    assert row[1] == URIRef("http://foo")


def test_sparql_bnodelist():
    """

    syntax tests for a few corner-cases not touched by the
    official tests.

    """

    prepareQuery("select * where { ?s ?p ( [] ) . }")
    prepareQuery("select * where { ?s ?p ( [ ?p2 ?o2 ] ) . }")
    prepareQuery("select * where { ?s ?p ( [ ?p2 ?o2 ] [] ) . }")
    prepareQuery("select * where { ?s ?p ( [] [ ?p2 ?o2 ] [] ) . }")


def test_complex_sparql_construct():

    g = Graph()
    q = """select ?subject ?study ?id where {
    ?s a <urn:Person>;
      <urn:partOf> ?c;
      <urn:hasParent> ?mother, ?father;
      <urn:id> [ a <urn:Identifier>; <urn:has-value> ?id].
    }"""
    g.query(q)


def test_sparql_update_with_bnode():
    """
    Test if the blank node is inserted correctly.
    """
    graph = Graph()
    graph.update("INSERT DATA { _:blankA <urn:type> <urn:Blank> }")
    for t in graph.triples((None, None, None)):
        assert isinstance(t[0], BNode)
        eq_(t[1].n3(), "<urn:type>")
        eq_(t[2].n3(), "<urn:Blank>")


def test_sparql_update_with_bnode_serialize_parse():
    """
    Test if the blank node is inserted correctly, can be serialized and parsed.
    """
    graph = Graph()
    graph.update("INSERT DATA { _:blankA <urn:type> <urn:Blank> }")
    string = graph.serialize(format="ntriples")
    raised = False
    try:
        Graph().parse(data=string, format="ntriples")
    except Exception as e:
        raised = True
    assert not raised


def test_bindings():
    layer_0 = sparql.Bindings(d={"v": 1, "bar": 2})
    layer_1 = sparql.Bindings(outer=layer_0, d={"v": 3})

    assert layer_0["v"] == 1
    assert layer_1["v"] == 3
    assert layer_1["bar"] == 2

    assert "foo" not in layer_0
    assert "v" in layer_0
    assert "bar" in layer_1

    # XXX This might not be intendet behaviour
    #     but is kept for compatibility for now.
    assert len(layer_1) == 3


def test_named_filter_graph_query():
    g = ConjunctiveGraph()
    g.namespace_manager.bind("rdf", RDF)
    g.namespace_manager.bind("rdfs", RDFS)
    ex = Namespace("https://ex.com/")
    g.namespace_manager.bind("ex", ex)
    g.get_context(ex.g1).parse(
        format="turtle",
        data=f"""
    PREFIX ex: <{str(ex)}>
    PREFIX rdfs: <{str(RDFS)}>
    ex:Boris rdfs:label "Boris" .
    ex:Susan rdfs:label "Susan" .
    """,
    )
    g.get_context(ex.g2).parse(
        format="turtle",
        data=f"""
    PREFIX ex: <{str(ex)}>
    ex:Boris a ex:Person .
    """,
    )

    assert list(
        g.query(
            "SELECT ?l WHERE { GRAPH ex:g1 { ?a rdfs:label ?l } ?a a ?type }",
            initNs={"ex": ex},
        )
    ) == [(Literal("Boris"),)]
    assert list(
        g.query(
            "SELECT ?l WHERE { GRAPH ex:g1 { ?a rdfs:label ?l } FILTER EXISTS { ?a a ?type }}",
            initNs={"ex": ex},
        )
    ) == [(Literal("Boris"),)]
    assert list(
        g.query(
            "SELECT ?l WHERE { GRAPH ex:g1 { ?a rdfs:label ?l } FILTER NOT EXISTS { ?a a ?type }}",
            initNs={"ex": ex},
        )
    ) == [(Literal("Susan"),)]
    assert list(
        g.query(
            "SELECT ?l WHERE { GRAPH ?g { ?a rdfs:label ?l } ?a a ?type }",
            initNs={"ex": ex},
        )
    ) == [(Literal("Boris"),)]
    assert list(
        g.query(
            "SELECT ?l WHERE { GRAPH ?g { ?a rdfs:label ?l } FILTER EXISTS { ?a a ?type }}",
            initNs={"ex": ex},
        )
    ) == [(Literal("Boris"),)]
    assert list(
        g.query(
            "SELECT ?l WHERE { GRAPH ?g { ?a rdfs:label ?l } FILTER NOT EXISTS { ?a a ?type }}",
            initNs={"ex": ex},
        )
    ) == [(Literal("Susan"),)]


def test_txtresult():
    data = f"""\
    @prefix rdfs: <{str(RDFS)}> .
    rdfs:Class a rdfs:Class ;
        rdfs:isDefinedBy <http://www.w3.org/2000/01/rdf-schema#> ;
        rdfs:label "Class" ;
        rdfs:comment "The class of classes." ;
        rdfs:subClassOf rdfs:Resource .
    """
    graph = Graph()
    graph.parse(data=data, format="turtle")
    result = graph.query(
        """\
    SELECT ?class ?superClass ?label ?comment WHERE {
        ?class rdf:type rdfs:Class.
        ?class rdfs:label ?label.
        ?class rdfs:comment ?comment.
        ?class rdfs:subClassOf ?superClass.
    }
    """
    )
    vars = [
        Variable("class"),
        Variable("superClass"),
        Variable("label"),
        Variable("comment"),
    ]
    assert result.type == "SELECT"
    assert len(result) == 1
    assert result.vars == vars
    txtresult = result.serialize(format="txt")
    lines = txtresult.decode().splitlines()
    assert len(lines) == 3
    vars_check = [Variable(var.strip()) for var in lines[0].split("|")]
    assert vars_check == vars


def test_property_bindings(rdfs_graph: Graph) -> None:
    """
    The ``bindings`` property of a `rdflib.query.Result` result works as expected.
    """
    result = rdfs_graph.query(
        """
            SELECT ?class ?label WHERE {
                ?class rdf:type rdfs:Class.
                ?class rdfs:label ?label.
            } ORDER BY ?class
        """
    )
    expected_bindings = [
        {
            Variable("class"): RDFS.Class,
            Variable("label"): Literal("Class"),
        },
        {
            Variable("class"): RDFS.Container,
            Variable("label"): Literal("Container"),
        },
        {
            Variable("class"): RDFS.ContainerMembershipProperty,
            Variable("label"): Literal("ContainerMembershipProperty"),
        },
        {
            Variable("class"): RDFS.Datatype,
            Variable("label"): Literal("Datatype"),
        },
        {
            Variable("class"): RDFS.Literal,
            Variable("label"): Literal("Literal"),
        },
        {
            Variable("class"): RDFS.Resource,
            Variable("label"): Literal("Resource"),
        },
    ]

    assert expected_bindings == result.bindings

    result.bindings = []
    assert [] == result.bindings


def test_call_function() -> None:
    """
    SPARQL built-in function call works as expected.
    """
    graph = Graph()
    query_string = """
    SELECT ?output0 WHERE {
        BIND(CONCAT("a", " + ", "b") AS ?output0)
    }
    """
    result = graph.query(query_string)
    assert result.type == "SELECT"
    rows = list(result)
    assert len(rows) == 1
    assert len(rows[0]) == 1
    assert rows[0][0] == Literal("a + b")


def test_custom_eval() -> None:
    """
    SPARQL custom eval function works as expected.
    """
    eg = Namespace("http://example.com/")
    custom_function_uri = eg["function"]
    custom_function_result = eg["result"]

    def custom_eval_extended(ctx: Any, extend: Any) -> Any:
        for c in evalPart(ctx, extend.p):
            try:
                if (
                    hasattr(extend.expr, "iri")
                    and extend.expr.iri == custom_function_uri
                ):
                    evaluation = custom_function_result
                else:
                    evaluation = _eval(extend.expr, c.forget(ctx, _except=extend._vars))
                    if isinstance(evaluation, SPARQLError):
                        raise evaluation

                yield c.merge({extend.var: evaluation})

            except SPARQLError:
                yield c

    def custom_eval(ctx: Any, part: Any) -> Any:
        if part.name == "Extend":
            return custom_eval_extended(ctx, part)
        else:
            raise NotImplementedError()

    try:
        rdflib.plugins.sparql.CUSTOM_EVALS["test_function"] = custom_eval
        graph = Graph()
        query_string = """
        PREFIX eg: <http://example.com/>
        SELECT ?output0 ?output1 WHERE {
            BIND(CONCAT("a", " + ", "b") AS ?output0)
            BIND(eg:function() AS ?output1)
        }
        """
        result = graph.query(query_string)
        assert result.type == "SELECT"
        rows = list(result)
        assert len(rows) == 1
        assert len(rows[0]) == 2
        assert rows[0][0] == Literal("a + b")
        assert rows[0][1] == custom_function_result
    finally:
        rdflib.plugins.sparql.CUSTOM_EVALS["test_function"]


@pytest.mark.parametrize(
    "result_consumer, exception_type, ",
    [
        pytest.param(lambda result: len(result), TypeError, id="len+TypeError"),
        pytest.param(
            lambda result: list(result),
            TypeError,
            id="list+TypeError",
            marks=pytest.mark.xfail(
                reason="TypeError does not propagate through list constructor"
            ),
        ),
        pytest.param(lambda result: len(result), RuntimeError, id="len+RuntimeError"),
        pytest.param(lambda result: list(result), RuntimeError, id="list+RuntimeError"),
    ],
)
def test_custom_eval_exception(
    result_consumer: Callable[[Result], None], exception_type: Type[Exception]
) -> None:
    """
    Exception raised from a ``CUSTOM_EVALS`` function during the execution of a
    query propagates to the caller.
    """
    eg = Namespace("http://example.com/")
    custom_function_uri = eg["function"]

    def custom_eval_extended(ctx: Any, extend: Any) -> Any:
        for c in evalPart(ctx, extend.p):
            try:
                if (
                    hasattr(extend.expr, "iri")
                    and extend.expr.iri == custom_function_uri
                ):
                    raise exception_type("TEST ERROR")
                else:
                    evaluation = _eval(extend.expr, c.forget(ctx, _except=extend._vars))
                    if isinstance(evaluation, SPARQLError):
                        raise evaluation

                yield c.merge({extend.var: evaluation})

            except SPARQLError:
                yield c

    def custom_eval(ctx: Any, part: Any) -> Any:
        if part.name == "Extend":
            return custom_eval_extended(ctx, part)
        else:
            raise NotImplementedError()

    try:
        rdflib.plugins.sparql.CUSTOM_EVALS["test_function"] = custom_eval
        graph = Graph()
        query_string = """
        PREFIX eg: <http://example.com/>
        SELECT ?output0 ?output1 WHERE {
            BIND(CONCAT("a", " + ", "b") AS ?output0)
            BIND(eg:function() AS ?output1)
        }
        """
        result: Result = graph.query(query_string)
        with pytest.raises(exception_type) as excinfo:
            result_consumer(result)
        assert str(excinfo.value) == "TEST ERROR"
    finally:
        del rdflib.plugins.sparql.CUSTOM_EVALS["test_function"]


@pytest.mark.parametrize(
    "result_consumer, exception_type, ",
    [
        pytest.param(lambda result: len(result), TypeError, id="len+TypeError"),
        pytest.param(
            lambda result: list(result),
            TypeError,
            id="list+TypeError",
            marks=pytest.mark.xfail(
                reason="TypeError does not propagate through list constructor"
            ),
        ),
        pytest.param(
            lambda result: len(result.bindings),
            TypeError,
            id="len+bindings+TypeError",
        ),
        # pytest.param(
        #     lambda result: len(result),
        #     AttributeError,
        #     id="len+AttributeError",
        # ),
        # pytest.param(
        #     lambda result: list(result),
        #     AttributeError,
        #     id="list+AttributeError",
        # ),
        # pytest.param(
        #     lambda result: logging.debug("result.bindings = %s", result.bindings),
        #     AttributeError,
        #     id="log+bindings+AttributeError",
        # ),
        pytest.param(lambda result: len(result), RuntimeError, id="len+RuntimeError"),
        pytest.param(lambda result: list(result), RuntimeError, id="list+RuntimeError"),
        pytest.param(lambda result: list(result), RuntimeError, id="list+RuntimeError"),
        pytest.param(
            lambda result: len(result.bindings),
            RuntimeError,
            id="len+bindings+RuntimeError",
        ),
    ],
)
def test_operator_exception(
    result_consumer: Callable[[Result], None],
    exception_type: Type[Exception],
    monkeypatch: MonkeyPatch,
) -> None:
    """
    Exception raised from an operator during the execution of a query
    propagates to the caller.
    """

    def thrower(*args: Any, **kwargs: Any) -> None:
        raise exception_type("TEST ERROR")

    monkeypatch.setattr(
        rdflib.plugins.sparql.operators, "calculateFinalDateTime", thrower
    )

    graph = Graph()
    result: Result = graph.query(
        """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT (?d + ?duration AS ?next_year)
    WHERE {
        VALUES (?duration ?d) {
            ("P1Y"^^xsd:yearMonthDuration"2019-05-28T12:14:45Z"^^xsd:dateTime)
            ("P1Y"^^xsd:yearMonthDuration"2019-05-28"^^xsd:date)
        }
    }
    """
    )

    with pytest.raises(exception_type) as excinfo:
        result_consumer(result)
    assert str(excinfo.value) == "TEST ERROR"


@pytest.mark.parametrize(
    ["query_string", "expected_bindings"],
    [
        pytest.param(
            """
            SELECT ?label ?deprecated WHERE {
                ?s rdfs:label "Class"
                OPTIONAL {
                    ?s
                    rdfs:comment
                    ?label
                }
                OPTIONAL {
                    ?s
                    owl:deprecated
                    ?deprecated
                }
            }
            """,
            [{Variable("label"): Literal("The class of classes.")}],
            id="select-optional",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                BIND( SHA256("abc") as ?bound )
            }
            """,
            [
                {
                    Variable("bound"): Literal(
                        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
                    )
                }
            ],
            id="select-bind-sha256",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                BIND( (1+2) as ?bound )
            }
            """,
            [{Variable("bound"): Literal(3)}],
            id="select-bind-plus",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                OPTIONAL {
                    <http://example.com/a>
                    <http://example.com/b>
                    <http://example.com/c>
                }
            }
            """,
            [{}],
            id="select-optional-const",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:label "Class" .
                FILTER EXISTS {
                    <http://example.com/a>
                    <http://example.com/b>
                    <http://example.com/c>
                }
            }
            """,
            [],
            id="select-filter-exists-const-false",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:label "Class" .
                FILTER NOT EXISTS {
                    <http://example.com/a>
                    <http://example.com/b>
                    <http://example.com/c>
                }
            }
            """,
            [{Variable("s"): RDFS.Class}],
            id="select-filter-notexists-const-false",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:label "Class"
                FILTER EXISTS {
                    rdfs:Class rdfs:isDefinedBy <http://www.w3.org/2000/01/rdf-schema#>
                }
            }
            """,
            [{Variable("s"): RDFS.Class}],
            id="select-filter-exists-const-true",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:label "Class"
                FILTER NOT EXISTS {
                    rdfs:Class rdfs:isDefinedBy <http://www.w3.org/2000/01/rdf-schema#>
                }
            }
            """,
            [],
            id="select-filter-notexists-const-true",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:isDefinedBy <http://www.w3.org/2000/01/rdf-schema#>
                FILTER EXISTS {
                    ?s rdfs:label "MISSING" .
                }
            }
            """,
            [],
            id="select-filter-exists-var-false",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:isDefinedBy <http://www.w3.org/2000/01/rdf-schema#>
                FILTER EXISTS {
                    ?s rdfs:label "Class" .
                }
            }
            """,
            [{Variable("s"): RDFS.Class}],
            id="select-filter-exists-var-true",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                BIND(
                    EXISTS {
                        <http://example.com/a>
                        <http://example.com/b>
                        <http://example.com/c>
                    }
                    AS ?bound
                )
            }
            """,
            [{Variable("bound"): Literal(False)}],
            id="select-bind-exists-const-false",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                BIND(
                    EXISTS {
                        rdfs:Class rdfs:label "Class"
                    }
                    AS ?bound
                )
            }
            """,
            [{Variable("bound"): Literal(True)}],
            id="select-bind-exists-const-true",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:comment "The class of classes."
                BIND(
                    EXISTS {
                        ?s rdfs:label "Class"
                    }
                    AS ?bound
                )
            }
            """,
            [{Variable("s"): RDFS.Class, Variable("bound"): Literal(True)}],
            id="select-bind-exists-var-true",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                ?s rdfs:comment "The class of classes."
                BIND(
                    EXISTS {
                        ?s rdfs:label "Property"
                    }
                    AS ?bound
                )
            }
            """,
            [{Variable("s"): RDFS.Class, Variable("bound"): Literal(False)}],
            id="select-bind-exists-var-false",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                BIND(
                    NOT EXISTS {
                        <http://example.com/a>
                        <http://example.com/b>
                        <http://example.com/c>
                    }
                    AS ?bound
                )
            }
            """,
            [{Variable("bound"): Literal(True)}],
            id="select-bind-notexists-const-false",
        ),
        pytest.param(
            """
            SELECT * WHERE {
                BIND(
                    NOT EXISTS {
                        rdfs:Class rdfs:label "Class"
                    }
                    AS ?bound
                )
            }
            """,
            [{Variable("bound"): Literal(False)}],
            id="select-bind-notexists-const-true",
        ),
        pytest.param(
            """
            PREFIX dce: <http://purl.org/dc/elements/1.1/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT
                ?class
                (
                    GROUP_CONCAT(
                        DISTINCT( STR( ?source ) );
                        separator="|"
                    ) AS ?sources
                )
            {
                ?class a rdfs:Class.
                OPTIONAL { ?class dce:source ?source. }
            }
            GROUP BY ?class ORDER BY ?class
            """,
            [
                {
                    Variable("class"): RDFS.Class,
                    Variable("sources"): Literal(""),
                },
                {
                    Variable("class"): RDFS.Container,
                    Variable("sources"): Literal(""),
                },
                {
                    Variable("class"): RDFS.ContainerMembershipProperty,
                    Variable("sources"): Literal(""),
                },
                {
                    Variable("class"): RDFS.Datatype,
                    Variable("sources"): Literal(""),
                },
                {
                    Variable("class"): RDFS.Literal,
                    Variable("sources"): Literal(""),
                },
                {
                    Variable("class"): RDFS.Resource,
                    Variable("sources"): Literal(""),
                },
            ],
            id="select-group-concat-optional-one",
        ),
        pytest.param(
            """
            PREFIX dce: <http://purl.org/dc/elements/1.1/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT
                ?vocab
                (
                    GROUP_CONCAT(
                        DISTINCT( STR( ?source ) );
                        separator="|"
                    ) AS ?sources
                )
            {
                ?class a rdfs:Class.
                ?class rdfs:isDefinedBy ?vocab.
                OPTIONAL { ?class dce:source ?source. }
            }
            GROUP BY ?vocab ORDER BY ?vocab
            """,
            [
                {
                    Variable("vocab"): URIRef(f"{RDFS}"),
                    Variable("sources"): Literal(""),
                },
            ],
            id="select-group-concat-optional-many",
        ),
        pytest.param(
            """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT
                ?predicate
                (
                    GROUP_CONCAT(
                        DISTINCT( STR( ?vocab ) );
                        separator="|"
                    ) AS ?vocabs
                )
            {

                VALUES ?types { rdf:Property rdfs:Class }.
                VALUES ?predicate { rdf:type }.
                ?thing ?predicate ?types.
                OPTIONAL {
                  ?thing rdfs:isDefinedBy ?vocab.
                }
            }
            GROUP BY ?predicate ORDER BY ?predicate
            """,
            [
                {
                    Variable("predicate"): RDF.type,
                    Variable("vocabs"): Literal(
                        "http://www.w3.org/2000/01/rdf-schema#"
                    ),
                },
            ],
            id="select-group-concat-optional-many",
        ),
        pytest.param(
            """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            SELECT
                ?predicate
                (
                    GROUP_CONCAT(
                        DISTINCT( STR( ?vocab ) );
                        separator="|"
                    ) AS ?vocabs
                )
            {

                VALUES ?types { rdf:Property rdfs:Class }.
                VALUES ?predicate { rdf:type }.
                ?thing ?predicate ?types.
                OPTIONAL {
                  ?thing rdfs:isDefinedBy ?vocab.
                }
            }
            GROUP BY ?predicate ORDER BY ?predicate
            """,
            [
                {
                    Variable("predicate"): RDF.type,
                    Variable("vocabs"): Literal(
                        "http://www.w3.org/2000/01/rdf-schema#"
                    ),
                },
            ],
            id="select-group-concat-optional-many",
        ),
    ],
)
def test_queries_against_rdfs_graph(
    query_string: str,
    expected_bindings: Sequence[Mapping["Variable", "Identifier"]],
    rdfs_graph: Graph,
) -> None:
    """
    Results of queries against the rdfs.ttl return the expected values.
    """
    query_tree = parseQuery(query_string)

    logging.debug("query_tree = %s", prettify_parsetree(query_tree))
    logging.debug("query_tree = %s", query_tree)
    query = translateQuery(query_tree)
    logging.debug("query = %s", query)
    query._original_args = (query_string, {}, None)
    result = rdfs_graph.query(query)
    logging.debug("result = %s", result)
    assert expected_bindings == result.bindings


BLANK_GRAPH = Graph()


@pytest.mark.parametrize(
    ["graph_source", "query_string", "expected_bindings"],
    [
        pytest.param(
            (TEST_DATA_DIR / "defined_namespaces/rdfs.ttl"),
            """
            SELECT (concat("", sha1(?x)) AS ?y) WHERE {}
            """,
            [{}],
            id="bind-select-nothing-error",
        ),
        pytest.param(
            (TEST_DATA_DIR / "defined_namespaces/rdfs.ttl"),
            """
            SELECT (concat("", sha1(?x)) AS ?y) ("A" as ?x) WHERE {}
            """,
            [
                {
                    Variable("x"): Literal("A"),
                }
            ],
            id="bind-select-nothing-error",
        ),
        pytest.param(
            (TEST_DATA_DIR / "defined_namespaces/rdfs.ttl"),
            """
            SELECT (concat("", <http://example.com>) AS ?y) ("A" as ?x) WHERE {}
            """,
            [
                {
                    Variable("x"): Literal("A"),
                }
            ],
            id="bind-select-nothing-error",
        ),
        pytest.param(
            (TEST_DATA_DIR / "defined_namespaces/rdfs.ttl"),
            """
            SELECT (concat("", sha1(?x)) AS ?y) WHERE {?s rdfs:label "Resource"}
            """,
            [{}],
            id="bind-select-something-error",
        ),
        pytest.param(
            (TEST_DATA_DIR / "defined_namespaces/rdfs.ttl"),
            """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?s WHERE {?s rdfs:label "Resource" BIND (sha1(?x) AS ?m)}
            """,
            [
                {
                    Variable("s"): RDFS.Resource,
                }
            ],
            id="bind-nonexisting",
        ),
        pytest.param(
            (TEST_DATA_DIR / "defined_namespaces/rdfs.ttl"),
            """
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?s ?m WHERE {?s rdfs:label "Resource" BIND (sha1(?x) AS ?m)}
            """,
            [
                {
                    Variable("s"): RDFS.Resource,
                }
            ],
            id="bind-nonexisting",
        ),
    ],
)
def test_queries(
    graph_source: Optional[GraphSourceType],
    query_string: str,
    expected_bindings: Sequence[Mapping["Variable", "Identifier"]],
) -> None:
    """
    Results of queries against the rdfs.ttl return the expected values.
    """
    if graph_source is not None:
        graph = cached_graph((graph_source,))
    else:
        graph = BLANK_GRAPH
    query_tree = parseQuery(query_string)
    logging.debug("query_tree = %s", prettify_parsetree(query_tree))
    logging.debug("query_tree = %s", query_tree)
    query = translateQuery(query_tree)
    logging.debug("query = %s", query)
    query._original_args = (query_string, {}, None)
    result = graph.query(query)
    logging.debug("result = %s", result)
    assert expected_bindings == result.bindings


@pytest.mark.parametrize(
    ["expression", "expected_result"],
    [
        ('concat("foo", "bar")', Literal("foobar")),
        ('concat("foo"@en, "bar"@en)', Literal("foobar", lang="en")),
        (
            'concat("foo"^^xsd:string, "bar"^^xsd:string)',
            Literal("foobar", datatype=XSD.string),
        ),
        ('concat("foo", "bar"^^xsd:string)', Literal("foobar")),
        ('concat("foo"@en, "bar")', Literal("foobar")),
        ('concat("foo"@en, "bar"^^xsd:string)', Literal("foobar")),
        ('concat("foo"@fr, "bar"@en)', Literal("foobar")),
        ("<https://example.com>", URIRef("https://example.com")),
        ('concat(<https://example.com>, "/suffix")', None),
        ("strlen(<https://example.com>)", None),
        ("sha1(<https://example.com>)", None),
    ],
)
def test_expression(
    expression: str,
    expected_result: Optional[Node],
) -> None:
    """
    Results of queries against the rdfs.ttl return the expected values.
    """
    graph = BLANK_GRAPH
    query_string = f"SELECT ({expression} AS ?bound_variable) WHERE {{}}"
    query_tree = parseQuery(query_string)
    logging.debug("query_tree = %s", prettify_parsetree(query_tree))
    logging.debug("query_tree = %s", query_tree)
    query = translateQuery(query_tree)
    logging.debug("query = %s", query)
    query._original_args = (query_string, {}, None)
    result = graph.query(query)
    logging.debug("result = %s", result)
    variable = Variable("bound_variable")
    assert len(result.bindings) == 1
    if expected_result is None:
        assert variable not in result.bindings[0]
    else:
        assert expected_result == result.bindings[0][variable]
