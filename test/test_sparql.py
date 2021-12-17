import logging
import traceback
from typing import Any, Callable, Type
from rdflib.plugins.sparql import sparql, prepareQuery, CUSTOM_EVALS
from rdflib.plugins.sparql.sparql import SPARQLError
from rdflib import Graph, URIRef, Literal, BNode, ConjunctiveGraph
from rdflib.namespace import Namespace, RDF, RDFS
from rdflib.compare import isomorphic
from rdflib.query import Result
from rdflib.term import Variable
from rdflib.plugins.sparql.evaluate import evalExtend, evalPart
from rdflib.plugins.sparql.evalutils import _eval
import pytest
from _pytest._code import ExceptionInfo
import sys

from .testutils import eq_


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

    assert (
        list(
            g.query(
                "SELECT ?l WHERE { GRAPH ex:g1 { ?a rdfs:label ?l } ?a a ?type }",
                initNs={"ex": ex},
            )
        )
        == [(Literal("Boris"),)]
    )
    assert (
        list(
            g.query(
                "SELECT ?l WHERE { GRAPH ex:g1 { ?a rdfs:label ?l } FILTER EXISTS { ?a a ?type }}",
                initNs={"ex": ex},
            )
        )
        == [(Literal("Boris"),)]
    )
    assert (
        list(
            g.query(
                "SELECT ?l WHERE { GRAPH ex:g1 { ?a rdfs:label ?l } FILTER NOT EXISTS { ?a a ?type }}",
                initNs={"ex": ex},
            )
        )
        == [(Literal("Susan"),)]
    )
    assert (
        list(
            g.query(
                "SELECT ?l WHERE { GRAPH ?g { ?a rdfs:label ?l } ?a a ?type }",
                initNs={"ex": ex},
            )
        )
        == [(Literal("Boris"),)]
    )
    assert (
        list(
            g.query(
                "SELECT ?l WHERE { GRAPH ?g { ?a rdfs:label ?l } FILTER EXISTS { ?a a ?type }}",
                initNs={"ex": ex},
            )
        )
        == [(Literal("Boris"),)]
    )
    assert (
        list(
            g.query(
                "SELECT ?l WHERE { GRAPH ?g { ?a rdfs:label ?l } FILTER NOT EXISTS { ?a a ?type }}",
                initNs={"ex": ex},
            )
        )
        == [(Literal("Susan"),)]
    )


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


def test_call_function() -> None:
    graph = Graph()
    query_string = """
    SELECT ?output0 WHERE {
        BIND(CONCAT("a", " + ", "b") AS ?output0)
    }
    """
    result = graph.query(query_string)
    assert result.type == "SELECT"
    rows = list(result)
    print("rows = ", rows)
    assert len(rows) == 1
    assert len(rows[0]) == 1
    assert rows[0][0] == Literal("a + b")


def test_custom_eval() -> None:
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
        logging.debug("ctx = %s, part = %s", ctx, part)
        if part.name == "Extend":
            return custom_eval_extended(ctx, part)
        else:
            raise NotImplementedError()

    global CUSTOM_EVALS
    try:
        CUSTOM_EVALS["test_function"] = custom_eval
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
        print("rows = ", rows)
        assert len(rows) == 1
        assert len(rows[0]) == 2
        assert rows[0][0] == Literal("a + b")
        assert rows[0][1] == custom_function_result
    finally:
        del CUSTOM_EVALS["test_function"]


# @pytest.mark.xfail(
#     reason=(
#         "TODO FIXME: if query result resolution causes an exception,"
#         "a subsequent request to resolve the same query query should also fail."
#     )
# )
# def test_custom_eval_runtime_error() -> None:
#     eg = Namespace("http://example.com/")
#     custom_function_uri = eg["function"]

#     def custom_eval_extended(ctx: Any, extend: Any) -> Any:
#         for c in evalPart(ctx, extend.p):
#             try:
#                 if (
#                     hasattr(extend.expr, "iri")
#                     and extend.expr.iri == custom_function_uri
#                 ):
#                     raise RuntimeError("TEST ERROR")
#                 else:
#                     evaluation = _eval(extend.expr, c.forget(ctx, _except=extend._vars))
#                     if isinstance(evaluation, SPARQLError):
#                         raise evaluation

#                 yield c.merge({extend.var: evaluation})

#             except SPARQLError:
#                 yield c

#     def custom_eval(ctx: Any, part: Any) -> Any:
#         logging.debug("ctx = %s, part = %s", ctx, part)
#         if part.name == "Extend":
#             return custom_eval_extended(ctx, part)
#         else:
#             raise NotImplementedError()

#     global CUSTOM_EVALS
#     try:
#         CUSTOM_EVALS["test_function"] = custom_eval
#         graph = Graph()
#         query_string = """
#         PREFIX eg: <http://example.com/>
#         SELECT ?output0 ?output1 WHERE {
#             BIND(CONCAT("a", " + ", "b") AS ?output0)
#             BIND(eg:function() AS ?output1)
#         }
#         """
#         excinfo: ExceptionInfo
#         result = graph.query(query_string)
#         with pytest.raises(RuntimeError) as excinfo:
#             list(result)

#         ex = excinfo.value
#         tb_lines = [
#             line.rstrip("\n")
#             for line in traceback.format_exception(ex.__class__, ex, ex.__traceback__)
#         ]
#         logging.debug("traceback = %s", "\n".join(tb_lines))
#         assert str(ex) == "TEST ERROR"
#         with pytest.raises(Exception) as excinfo:
#             list(result)
#     finally:
#         del CUSTOM_EVALS["test_function"]


# @pytest.mark.xfail(reason="TODO FIXME: TypeErrors are not propagated")


@pytest.mark.parametrize(
    "consumer",
    [
        # lambda result: len(result),
        lambda result: list(result),
    ],
)
def test_custom_eval_exception(consumer: Callable[[Result], None]) -> None:
    """
    Exception raised from a custom eval during the execution of a query gets
    forwarded correctly.
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
                    print("will throw type error")
                    traceback.print_stack(file=sys.stdout)
                    raise TypeError("TEST ERROR")
                else:
                    evaluation = _eval(extend.expr, c.forget(ctx, _except=extend._vars))
                    if isinstance(evaluation, SPARQLError):
                        raise evaluation

                yield c.merge({extend.var: evaluation})

            except SPARQLError:
                yield c

    def custom_eval(ctx: Any, part: Any) -> Any:
        logging.debug("ctx = %s, part = %s", ctx, part)
        if part.name == "Extend":
            return custom_eval_extended(ctx, part)
        else:
            raise NotImplementedError()

    global CUSTOM_EVALS
    try:
        CUSTOM_EVALS["test_function"] = custom_eval
        graph = Graph()
        query_string = """
        PREFIX eg: <http://example.com/>
        SELECT ?output0 ?output1 WHERE {
            BIND(CONCAT("a", " + ", "b") AS ?output0)
            BIND(eg:function() AS ?output1)
        }
        """
        excinfo: ExceptionInfo
        # result = graph.query(query_string)
        # list(result)
        result = graph.query(query_string)
        with pytest.raises(TypeError) as excinfo:
            consumer(result)
            # list(result)
        assert str(excinfo.value) == "TEST ERROR"
    finally:
        del CUSTOM_EVALS["test_function"]
