from typing import TypeVar
import unittest
import rdflib
from rdflib.compare import graph_diff, to_canonical_graph
from rdflib.namespace import Namespace, RDF, RDFS, OWL, XSD, FOAF
from rdflib import Graph
from rdflib.term import Node, BNode, Literal

"""Test for graph_diff - much more extensive testing 
would certainly be possible"""


class TestDiff(unittest.TestCase):
    """Unicode literals for graph_diff test
    (issue 151)"""

    def testA(self):
        """with bnode"""
        g = rdflib.Graph()
        g.add((rdflib.BNode(), rdflib.URIRef("urn:p"), rdflib.Literal("\xe9")))

        diff = graph_diff(g, g)

    def testB(self):
        """Curiously, this one passes, even before the fix in issue 151"""

        g = rdflib.Graph()
        g.add((rdflib.URIRef("urn:a"), rdflib.URIRef("urn:p"), rdflib.Literal("\xe9")))

        diff = graph_diff(g, g)


import logging, os, sys

logging.basicConfig(
    level=os.environ.get("PYTHON_LOGGING_LEVEL", logging.DEBUG),
    stream=sys.stderr,
    datefmt="%Y-%m-%dT%H:%M:%S",
    format=(
        "%(asctime)s %(process)d %(thread)d %(levelno)03d:%(levelname)-8s "
        "%(name)-12s %(module)s:%(lineno)s:%(funcName)s %(message)s"
    ),
)

import typing as t

TripleT = t.Tuple[Node, Node, Node]
TripleSetT = t.Set[TripleT]
GenericT = t.TypeVar("GenericT")


def to_tripleset(input: t.Iterable[TripleT]) -> TripleSetT:
    result: TripleSetT = set()
    for triple in input:
        result.add(triple)
    return result


def to_triplesets(input: t.Sequence[Graph]) -> t.Sequence[TripleSetT]:
    result: t.List[TripleSetT] = []
    for graph in input:
        result.append(to_tripleset(graph))
    return result


class TestIssues(unittest.TestCase):

    def test_a(self) -> None:
        EGS = Namespace("example:schema:")
        EGI = Namespace("example:instance:")
        g0_ts: TripleSetT = set()
        bnode = BNode()
        g0_ts.update({
            (bnode, FOAF.name, Literal("Golan Trevize")),
            (bnode, RDF.type, FOAF.Person),
        })
        g0 = Graph()
        g0 += g0_ts
        cg0 = to_canonical_graph(g0)
        cg0_ts = to_tripleset(cg0)

        g1_ts: TripleSetT = set()
        bnode = BNode()
        g1_ts.update({
            (bnode, FOAF.name, Literal("Golan Trevize")),
            (bnode, RDF.type, FOAF.Person),
        })

        logging.debug("cg0_ts = \n%s", cg0_ts)

        


    def xtest_issue1294(self) -> None:
        TNS = Namespace("http://example.org/test#")

        base_data = f"""\
        @prefix : <{TNS}> .
        @prefix owl:   <{OWL}> .
        @prefix xsd:   <{XSD}> .
        @prefix rdfs:  <{RDFS}> .
        @prefix rdf:   <{RDF}> .

        :C1 a owl:Class ;
            rdfs:subClassOf [
                a owl:Restriction ;
                owl:minCardinality "1"^^xsd:int ;
                owl:onProperty rdfs:label ;
            ] ;
            rdfs:label "C1"@en ;
            .
        """

        extra_data = """\
        :C2 a owl:Class ;
            rdfs:subClassOf [
                a owl:Restriction ;
                owl:minCardinality "1"^^xsd:int ;
                owl:onProperty      rdfs:comment
            ] ;
            rdfs:label "C2"@en ;
            .
        """


        g1 = Graph()
        g1.parse(data=base_data, format="turtle")
        g2 = Graph()
        g2.parse(data=base_data + extra_data, format="turtle")

        g1cs = to_canonical_graph(g1).skolemize()
        g2cs = to_canonical_graph(g2).skolemize()

        logging.debug("g1cs = \n%s", g1cs.serialize(format="ntriples"))
        logging.debug("g2cs = \n%s", g2cs.serialize(format="ntriples"))

        result = graph_diff(g1, g2)
        in_both, in_first, in_second = to_triplesets(result)
        logging.debug("in_both = \n%s", in_both)
        logging.debug("in_first = \n%s", in_first)
        logging.debug("in_second = \n%s", in_second)
        result = to_triplesets(graph_diff(g1, g1))
        in_both, in_first, in_second = to_triplesets(result)
        logging.debug("in_both = \n%s", in_both)
        logging.debug("in_first = \n%s", in_first)
        logging.debug("in_second = \n%s", in_second)


if __name__ == "__main__":
    unittest.main()
