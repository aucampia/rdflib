import unittest
from unittest.case import expectedFailure
import rdflib
import re
from rdflib import Namespace
from .testutils import GraphHelper

from nose import SkipTest

TRIPLE = (
    rdflib.URIRef("http://example.com/s"),
    rdflib.RDFS.label,
    rdflib.Literal("example 1"),
)


EG = Namespace("http://example.com/")


class TestTrig(unittest.TestCase):
    def testEmpty(self):
        g = rdflib.Graph()
        s = g.serialize(format="trig")
        self.assertTrue(s is not None)

    def test_single_quad(self) -> None:
        graph = rdflib.ConjunctiveGraph()
        quad = (EG["subject"], EG["predicate"], EG["object"], EG["graph"])
        graph.add(quad)
        check_graph = rdflib.ConjunctiveGraph()
        data_str = graph.serialize(format="trig")
        check_graph.parse(data=data_str, format="trig")
        quad_set, check_quad_set = GraphHelper.quad_sets([graph, check_graph])
        self.assertEqual(quad_set, check_quad_set)

    @expectedFailure
    def test_default_identifier(self) -> None:
        """
        This should pass, but for some reason when the default identifier is
        set, trig serializes quads inside this default indentifier to an
        anonymous graph.

        So in this test, data_str is:

            @base <utf-8> .
            @prefix ns1: <http://example.com/> .

            {
                ns1:subject ns1:predicate ns1:object .
            }

        instead of:
            @base <utf-8> .
            @prefix ns1: <http://example.com/> .

            ns1:graph {
                ns1:subject ns1:predicate ns1:object .
            }
        """
        graph_id = EG["graph"]
        graph = rdflib.ConjunctiveGraph(identifier=EG["graph"])
        quad = (EG["subject"], EG["predicate"], EG["object"], graph_id)
        graph.add(quad)
        check_graph = rdflib.ConjunctiveGraph()
        data_str = graph.serialize(format="trig")
        check_graph.parse(data=data_str, format="trig")
        quad_set, check_quad_set = GraphHelper.quad_sets([graph, check_graph])
        self.assertEqual(quad_set, check_quad_set)

    def testRepeatTriples(self):
        g = rdflib.ConjunctiveGraph()
        g.get_context("urn:a").add(
            (rdflib.URIRef("urn:1"), rdflib.URIRef("urn:2"), rdflib.URIRef("urn:3"))
        )

        g.get_context("urn:b").add(
            (rdflib.URIRef("urn:1"), rdflib.URIRef("urn:2"), rdflib.URIRef("urn:3"))
        )

        self.assertEqual(len(g.get_context("urn:a")), 1)
        self.assertEqual(len(g.get_context("urn:b")), 1)

        s = g.serialize(format="trig", encoding="latin-1")
        self.assertTrue(b"{}" not in s)  # no empty graphs!

    def testSameSubject(self):
        g = rdflib.ConjunctiveGraph()
        g.get_context("urn:a").add(
            (rdflib.URIRef("urn:1"), rdflib.URIRef("urn:p1"), rdflib.URIRef("urn:o1"))
        )

        g.get_context("urn:b").add(
            (rdflib.URIRef("urn:1"), rdflib.URIRef("urn:p2"), rdflib.URIRef("urn:o2"))
        )

        self.assertEqual(len(g.get_context("urn:a")), 1)
        self.assertEqual(len(g.get_context("urn:b")), 1)

        s = g.serialize(format="trig", encoding="latin-1")

        self.assertEqual(len(re.findall(b"p1", s)), 1)
        self.assertEqual(len(re.findall(b"p2", s)), 1)

        self.assertTrue(b"{}" not in s)  # no empty graphs!

    def testRememberNamespace(self):
        g = rdflib.ConjunctiveGraph()
        g.add(TRIPLE + (rdflib.URIRef("http://example.com/graph1"),))
        # In 4.2.0 the first serialization would fail to include the
        # prefix for the graph but later serialize() calls would work.
        first_out = g.serialize(format="trig", encoding="latin-1")
        second_out = g.serialize(format="trig", encoding="latin-1")
        self.assertTrue(b"@prefix ns1: <http://example.com/> ." in second_out)
        self.assertTrue(b"@prefix ns1: <http://example.com/> ." in first_out)

    def testGraphQnameSyntax(self):
        g = rdflib.ConjunctiveGraph()
        g.add(TRIPLE + (rdflib.URIRef("http://example.com/graph1"),))
        out = g.serialize(format="trig", encoding="latin-1")
        self.assertTrue(b"ns1:graph1 {" in out)

    def testGraphUriSyntax(self):
        g = rdflib.ConjunctiveGraph()
        # getQName will not abbreviate this, so it should serialize as
        # a '<...>' term.
        g.add(TRIPLE + (rdflib.URIRef("http://example.com/foo."),))
        out = g.serialize(format="trig", encoding="latin-1")
        self.assertTrue(b"<http://example.com/foo.> {" in out)

    def testBlankGraphIdentifier(self):
        g = rdflib.ConjunctiveGraph()
        g.add(TRIPLE + (rdflib.BNode(),))
        out = g.serialize(format="trig", encoding="latin-1")
        graph_label_line = out.splitlines()[-4]

        self.assertTrue(re.match(br"^_:[a-zA-Z0-9]+ \{", graph_label_line))

    def testGraphParsing(self):
        # should parse into single default graph context
        data = """
<http://example.com/thing#thing_a> <http://example.com/knows> <http://example.com/thing#thing_b> .
"""
        g = rdflib.ConjunctiveGraph()
        g.parse(data=data, format="trig")
        self.assertEqual(len(list(g.contexts())), 1)

        # should parse into single default graph context
        data = """
<http://example.com/thing#thing_a> <http://example.com/knows> <http://example.com/thing#thing_b> .

{ <http://example.com/thing#thing_c> <http://example.com/knows> <http://example.com/thing#thing_d> . }
"""
        g = rdflib.ConjunctiveGraph()
        g.parse(data=data, format="trig")
        self.assertEqual(len(list(g.contexts())), 1)

        # should parse into 2 contexts, one default, one named
        data = """
<http://example.com/thing#thing_a> <http://example.com/knows> <http://example.com/thing#thing_b> .

{ <http://example.com/thing#thing_c> <http://example.com/knows> <http://example.com/thing#thing_d> . }

<http://example.com/graph#graph_a> {
    <http://example.com/thing/thing_e> <http://example.com/knows> <http://example.com/thing#thing_f> .
}
"""
        g = rdflib.ConjunctiveGraph()
        g.parse(data=data, format="trig")
        self.assertEqual(len(list(g.contexts())), 2)

    @unittest.skipIf(
        True, "Iterative serialization currently produces 16 copies of everything"
    )
    def testRoundTrips(self):

        data = """
<http://example.com/thing#thing_a> <http://example.com/knows> <http://example.com/thing#thing_b> .

{ <http://example.com/thing#thing_c> <http://example.com/knows> <http://example.com/thing#thing_d> . }

<http://example.com/graph#graph_a> {
    <http://example.com/thing/thing_e> <http://example.com/knows> <http://example.com/thing#thing_f> .
}
"""
        g = rdflib.ConjunctiveGraph()
        for i in range(5):
            g.parse(data=data, format="trig")
            data = g.serialize(format="trig").decode()

        # output should only contain 1 mention of each resource/graph name
        self.assertEqual(data.count("thing_a"), 1)
        self.assertEqual(data.count("thing_b"), 1)
        self.assertEqual(data.count("thing_c"), 1)
        self.assertEqual(data.count("thing_d"), 1)
        self.assertEqual(data.count("thing_e"), 1)
        self.assertEqual(data.count("thing_f"), 1)
        self.assertEqual(data.count("graph_a"), 1)

    def testDefaultGraphSerializesWithoutName(self):
        data = """
<http://example.com/thing#thing_a> <http://example.com/knows> <http://example.com/thing#thing_b> .

{ <http://example.com/thing#thing_c> <http://example.com/knows> <http://example.com/thing#thing_d> . }
"""
        g = rdflib.ConjunctiveGraph()
        g.parse(data=data, format="trig")
        data = g.serialize(format="trig", encoding="latin-1")

        self.assertTrue(b"None" not in data)

    def testPrefixes(self):

        data = """
        @prefix ns1: <http://ex.org/schema#> .
        <http://ex.org/docs/document1> = {
            ns1:Person_A a ns1:Person ;
                ns1:TextSpan "Simon" .
        }
        <http://ex.org/docs/document2> = {
            ns1:Person_C a ns1:Person ;
                ns1:TextSpan "Agnes" .
        }
        """

        cg = rdflib.ConjunctiveGraph()
        cg.parse(data=data, format="trig")
        data = cg.serialize(format="trig", encoding="latin-1")

        self.assertTrue("ns2: <http://ex.org/docs/".encode("latin-1") in data, data)
        self.assertTrue("<ns2:document1>".encode("latin-1") not in data, data)
        self.assertTrue("ns2:document1".encode("latin-1") in data, data)
