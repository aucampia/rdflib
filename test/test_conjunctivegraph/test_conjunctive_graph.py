"""
Tests for ConjunctiveGraph that do not depend on the underlying store
"""

from test.utils import GraphHelper

import pytest

from rdflib import ConjunctiveGraph, Graph
from rdflib.namespace import Namespace
from rdflib.parser import StringInputSource
from rdflib.term import BNode, Identifier, URIRef

DATA = """
<http://example.org/record/1> a <http://xmlns.com/foaf/0.1/Document> .
"""

PUBLIC_ID = "http://example.org/record/1"

EG = Namespace("http://example.com/")


def test_add() -> None:
    quad = (EG["subject"], EG["predicate"], EG["object"], EG["graph"])
    g = ConjunctiveGraph()
    g.add(quad)
    quad_set = GraphHelper.quad_set(g)
    assert len(quad_set) == 1
    assert next(iter(quad_set)) == quad


def test_bnode_publicid():

    g = ConjunctiveGraph()
    b = BNode()
    data = "<d:d> <e:e> <f:f> ."
    print("Parsing %r into %r" % (data, b))
    g.parse(data=data, format="turtle", publicID=b)

    triples = list(g.get_context(b).triples((None, None, None)))
    if not triples:
        raise Exception("No triples found in graph %r" % b)

    u = URIRef(b)

    triples = list(g.get_context(u).triples((None, None, None)))
    if triples:
        raise Exception("Bad: Found in graph %r: %r" % (u, triples))


def test_quad_contexts():
    g = ConjunctiveGraph()
    a = URIRef("urn:a")
    b = URIRef("urn:b")
    g.get_context(a).add((a, a, a))
    g.addN([(b, b, b, b)])

    assert set(g) == set([(a, a, a), (b, b, b)])
    for q in g.quads():
        assert isinstance(q[3], Graph)


def get_graph_ids_tests():
    def check(kws):
        cg = ConjunctiveGraph()
        cg.parse(**kws)

        for g in cg.contexts():
            gid = g.identifier
            assert isinstance(gid, Identifier)

    yield check, dict(data=DATA, publicID=PUBLIC_ID, format="turtle")

    source = StringInputSource(DATA.encode("utf8"))
    source.setPublicId(PUBLIC_ID)
    yield check, dict(source=source, format="turtle")


@pytest.mark.parametrize("checker, kws", get_graph_ids_tests())
def test_graph_ids(checker, kws):
    checker(kws)
