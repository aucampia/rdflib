"""
Tests for ConjunctiveGraph that do not depend on the underlying store
"""

import unittest
from rdflib import ConjunctiveGraph, Graph
from rdflib.namespace import Namespace
from rdflib.term import Identifier, URIRef, BNode
from rdflib.parser import StringInputSource
from os import path

from .testutils import GraphHelper


DATA = """
<http://example.org/record/1> a <http://xmlns.com/foaf/0.1/Document> .
"""

PUBLIC_ID = "http://example.org/record/1"

EG = Namespace("http://example.com/")


class TestConjuctiveGraph(unittest.TestCase):
    def test_add(self) -> None:
        quad = (EG["subject"], EG["predicate"], EG["object"], EG["graph"])
        g = ConjunctiveGraph()
        g.add(quad)
        quad_set = GraphHelper.quad_set(g)
        self.assertEqual(len(quad_set), 1)
        self.assertEqual(next(iter(quad_set)), quad)


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


def test_graph_ids():
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


if __name__ == "__main__":
    import nose

    nose.main(defaultTest=__name__)
