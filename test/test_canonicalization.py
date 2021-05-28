from collections import Counter
from rdflib.term import Node
from rdflib import Graph, RDF, BNode, URIRef, Namespace, ConjunctiveGraph, Literal
from rdflib.namespace import FOAF, OWL, RDFS, XSD
from rdflib.compare import to_isomorphic, to_canonical_graph, _TripleCanonicalizer

import rdflib
from rdflib.plugins.stores.memory import Memory

from io import StringIO
import unittest
import typing as t


def get_digest_value(rdf, mimetype):
    graph = Graph()
    graph.load(StringIO(rdf), format=mimetype)
    stats = {}
    ig = to_isomorphic(graph)
    result = ig.graph_digest(stats)
    print(stats)
    return result


def negative_graph_match_test():
    """Test of FRIR identifiers against tricky RDF graphs with blank nodes."""
    testInputs = [
        [
            str(
                """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         [ :label "Same" ].
         """
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         [ :label "Same" ],
         [ :label "Same" ].
         """
            ),
            False,
        ],
        [
            str(
                """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         <http://example.org/a>.
         """
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     <http://example.org> :rel
         <http://example.org/a>,
         <http://example.org/a>.
         """
            ),
            True,
        ],
        [
            str(
                """@prefix : <http://example.org/ns#> .
     :linear_two_step_symmetry_start :related [ :related [ :related :linear_two_step_symmatry_end]],
                                              [ :related [ :related :linear_two_step_symmatry_end]]."""
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     :linear_two_step_symmetry_start :related [ :related [ :related :linear_two_step_symmatry_end]],
                                              [ :related [ :related :linear_two_step_symmatry_end]]."""
            ),
            True,
        ],
        [
            str(
                """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ]."""
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ];
          ]."""
            ),
            False,
        ],
        # This test fails because the algorithm purposefully breaks the symmetry of symetric
        [
            str(
                """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ]."""
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ]."""
            ),
            True,
        ],
        [
            str(
                """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :label "foo";
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ]."""
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     _:a :rel [
         :rel [
         :rel [
         :rel [
           :rel _:a;
          ];
          ];
          ];
          ]."""
            ),
            False,
        ],
        [
            str(
                """@prefix : <http://example.org/ns#> .
     _:0001 :rel _:0003, _:0004.
     _:0002 :rel _:0005, _:0006.
     _:0003 :rel _:0001, _:0007, _:0010.
     _:0004 :rel _:0001, _:0009, _:0008.
     _:0005 :rel _:0002, _:0007, _:0009.
     _:0006 :rel _:0002, _:0008, _:0010.
     _:0007 :rel _:0003, _:0005, _:0009.
     _:0008 :rel _:0004, _:0006, _:0010.
     _:0009 :rel _:0004, _:0005, _:0007.
     _:0010 :rel _:0003, _:0006, _:0008.
     """
            ),
            str(
                """@prefix : <http://example.org/ns#> .
     _:0001 :rel _:0003, _:0004.
     _:0002 :rel _:0005, _:0006.
     _:0003 :rel _:0001, _:0007, _:0010.
     _:0008 :rel _:0004, _:0006, _:0010.
     _:0009 :rel _:0004, _:0005, _:0007.
     _:0010 :rel _:0003, _:0006, _:0008.
     _:0004 :rel _:0001, _:0009, _:0008.
     _:0005 :rel _:0002, _:0007, _:0009.
     _:0006 :rel _:0002, _:0008, _:0010.
     _:0007 :rel _:0003, _:0005, _:0009.
     """
            ),
            True,
        ],
    ]

    def fn(rdf1, rdf2, identical):
        digest1 = get_digest_value(rdf1, "text/turtle")
        digest2 = get_digest_value(rdf2, "text/turtle")
        print(rdf1)
        print(digest1)
        print(rdf2)
        print(digest2)
        assert (digest1 == digest2) == identical

    for inputs in testInputs:
        yield fn, inputs[0], inputs[1], inputs[2]


def test_issue494_collapsing_bnodes():
    """Test for https://github.com/RDFLib/rdflib/issues/494 collapsing BNodes"""
    g = Graph()
    g += [
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["object"], URIRef("source")),
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["predicate"], BNode("vcb3")),
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["subject"], BNode("vcb2")),
        (BNode("Na1a8fbcf755f41c1b5728f326be50994"), RDF["type"], RDF["Statement"]),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["object"], URIRef("target")),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["predicate"], BNode("vcb0")),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["subject"], URIRef("source")),
        (BNode("Na713b02f320d409c806ff0190db324f4"), RDF["type"], RDF["Statement"]),
        (BNode("Ndb804ba690a64b3dbb9063c68d5e3550"), RDF["object"], BNode("vr0KcS4")),
        (
            BNode("Ndb804ba690a64b3dbb9063c68d5e3550"),
            RDF["predicate"],
            BNode("vrby3JV"),
        ),
        (BNode("Ndb804ba690a64b3dbb9063c68d5e3550"), RDF["subject"], URIRef("source")),
        (BNode("Ndb804ba690a64b3dbb9063c68d5e3550"), RDF["type"], RDF["Statement"]),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["object"], URIRef("source")),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["predicate"], BNode("vcb5")),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["subject"], URIRef("target")),
        (BNode("Ndfc47fb1cd2d4382bcb8d5eb7835a636"), RDF["type"], RDF["Statement"]),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["object"], URIRef("source")),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["predicate"], BNode("vcb4")),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["subject"], URIRef("source")),
        (BNode("Nec6864ef180843838aa9805bac835c98"), RDF["type"], RDF["Statement"]),
    ]

    # print('graph length: %d, nodes: %d' % (len(g), len(g.all_nodes())))
    # print('triple_bnode degrees:')
    # for triple_bnode in g.subjects(RDF['type'], RDF['Statement']):
    #     print(len(list(g.triples([triple_bnode, None, None]))))
    # print('all node degrees:')
    g_node_degs = sorted(
        [len(list(g.triples([node, None, None]))) for node in g.all_nodes()],
        reverse=True,
    )
    # print(g_node_degs)

    cg = to_canonical_graph(g)
    # print('graph length: %d, nodes: %d' % (len(cg), len(cg.all_nodes())))
    # print('triple_bnode degrees:')
    # for triple_bnode in cg.subjects(RDF['type'], RDF['Statement']):
    #     print(len(list(cg.triples([triple_bnode, None, None]))))
    # print('all node degrees:')
    cg_node_degs = sorted(
        [len(list(cg.triples([node, None, None]))) for node in cg.all_nodes()],
        reverse=True,
    )
    # print(cg_node_degs)

    assert len(g) == len(cg), "canonicalization changed number of triples in graph"
    assert len(g.all_nodes()) == len(
        cg.all_nodes()
    ), "canonicalization changed number of nodes in graph"
    assert len(list(g.subjects(RDF["type"], RDF["Statement"]))) == len(
        list(cg.subjects(RDF["type"], RDF["Statement"]))
    ), "canonicalization changed number of statements"
    assert g_node_degs == cg_node_degs, "canonicalization changed node degrees"

    # counter for subject, predicate and object nodes
    g_pos_counts = Counter(), Counter(), Counter()
    for t in g:
        for i, node in enumerate(t):
            g_pos_counts[i][t] += 1
    g_count_signature = [sorted(c.values()) for c in g_pos_counts]

    cg = to_canonical_graph(g)
    cg_pos_counts = Counter(), Counter(), Counter()
    for t in cg:
        for i, node in enumerate(t):
            cg_pos_counts[i][t] += 1
    cg_count_signature = [sorted(c.values()) for c in cg_pos_counts]

    assert (
        g_count_signature == cg_count_signature
    ), "canonicalization changed node position counts"


def test_issue682_signing_named_graphs():
    ns = Namespace("http://love.com#")

    mary = BNode()
    john = URIRef("http://love.com/lovers/john#")

    cmary = URIRef("http://love.com/lovers/mary#")
    cjohn = URIRef("http://love.com/lovers/john#")

    store = Memory()

    g = ConjunctiveGraph(store=store)
    g.bind("love", ns)

    gmary = Graph(store=store, identifier=cmary)

    gmary.add((mary, ns["hasName"], Literal("Mary")))
    gmary.add((mary, ns["loves"], john))

    gjohn = Graph(store=store, identifier=cjohn)
    gjohn.add((john, ns["hasName"], Literal("John")))

    ig = to_isomorphic(g)
    igmary = to_isomorphic(gmary)

    assert len(igmary) == len(gmary)
    assert len(ig) == len(g)
    assert len(igmary) < len(ig)
    assert ig.graph_digest() != igmary.graph_digest()


def test_issue725_collapsing_bnodes_2():
    g = Graph()
    g += [
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v2"),
        ),
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v0"),
        ),
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N0a76d42406b84fe4b8029d0a7fa04244"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v1"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v0"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N2f62af5936b94a8eb4b1e4bfa8e11d95"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v5"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v4"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N5ae541f93e1d4e5880450b1bdceb6404"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            URIRef("urn:gp_learner:fixed_var:source"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v0"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("N86ac7ca781f546ae939b8963895f672e"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#object"),
            BNode("v1"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate"),
            BNode("v3"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#subject"),
            URIRef("urn:gp_learner:fixed_var:target"),
        ),
        (
            BNode("Nac82b883ca3849b5ab6820b7ac15e490"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement"),
        ),
    ]

    turtle = """
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
    @prefix xml: <http://www.w3.org/XML/1998/namespace> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    [] a rdf:Statement ;
        rdf:object [ ] ;
        rdf:predicate _:v0 ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object _:v1 ;
        rdf:predicate _:v0 ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object [ ] ;
        rdf:predicate [ ] ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object <urn:gp_learner:fixed_var:source> ;
        rdf:predicate _:v0 ;
        rdf:subject <urn:gp_learner:fixed_var:target> .

    [] a rdf:Statement ;
        rdf:object _:v1 ;
        rdf:predicate [ ] ;
        rdf:subject <urn:gp_learner:fixed_var:target> ."""

    # g = Graph()
    # g.parse(data=turtle, format='turtle')

    stats = {}
    cg = rdflib.compare.to_canonical_graph(g, stats=stats)

    # print ('graph g length: %d, nodes: %d' % (len(g), len(g.all_nodes())))
    # print ('triple_bnode degrees:')
    # for triple_bnode in g.subjects(rdflib.RDF['type'], rdflib.RDF['Statement']):
    #     print (len(list(g.triples([triple_bnode, None, None]))))
    # print ('all node out-degrees:')
    # print (sorted(
    #     [len(list(g.triples([node, None, None]))) for node in g.all_nodes()]))
    # print ('all node in-degrees:')
    # print (sorted(
    #     [len(list(g.triples([None, None, node]))) for node in g.all_nodes()]))
    # print(g.serialize(format='n3'))
    #
    # print ('graph cg length: %d, nodes: %d' % (len(cg), len(cg.all_nodes())))
    # print ('triple_bnode degrees:')
    # for triple_bnode in cg.subjects(rdflib.RDF['type'],
    #                                 rdflib.RDF['Statement']):
    #     print (len(list(cg.triples([triple_bnode, None, None]))))
    # print ('all node out-degrees:')
    # print (sorted(
    #     [len(list(cg.triples([node, None, None]))) for node in cg.all_nodes()]))
    # print ('all node in-degrees:')
    # print (sorted(
    #     [len(list(cg.triples([None, None, node]))) for node in cg.all_nodes()]))
    # print(cg.serialize(format='n3'))

    assert len(g.all_nodes()) == len(cg.all_nodes())

    cg = to_canonical_graph(g)
    assert len(g) == len(cg), "canonicalization changed number of triples in graph"
    assert len(g.all_nodes()) == len(
        cg.all_nodes()
    ), "canonicalization changed number of nodes in graph"
    assert len(list(g.subjects(RDF["type"], RDF["Statement"]))) == len(
        list(cg.subjects(RDF["type"], RDF["Statement"]))
    ), "canonicalization changed number of statements"

    # counter for subject, predicate and object nodes
    g_pos_counts = Counter(), Counter(), Counter()
    for t in g:
        for i, node in enumerate(t):
            g_pos_counts[i][t] += 1
    g_count_signature = [sorted(c.values()) for c in g_pos_counts]

    cg_pos_counts = Counter(), Counter(), Counter()
    for t in cg:
        for i, node in enumerate(t):
            cg_pos_counts[i][t] += 1
    cg_count_signature = [sorted(c.values()) for c in cg_pos_counts]

    assert (
        g_count_signature == cg_count_signature
    ), "canonicalization changed node position counts"


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


class TestConsistency(unittest.TestCase):
    ttlpreamble: str
    ttlfrags: t.List[str]
    tsets: t.List[TripleSetT]

    @classmethod
    def setUpClass(cls) -> None:
        cls.ttlpreamble = f"""
        @prefix foaf: <{FOAF}> .
        """
        ttlfrags: t.List[str] = []
        ttlfrags.append(
            """
            [] a foaf:Person ;
                foaf:name "Golan Trevize"@en ;
                .
            """
        )
        ttlfrags.append(
            """
            [] a foaf:Person ;
                foaf:name "Janov Pelorat"@en ;
                .
            """
        )
        ttlfrags.append(
            """
            [] a foaf:Person ;
                foaf:name "R. Daneel Olivaw"@en ;
                .
            """
        )
        cls.ttlfrags = ttlfrags

        tsets: t.List[TripleSetT] = []
        bnode = BNode()
        tsets.append(
            {
                (bnode, FOAF.name, Literal("Golan Trevize")),
                (bnode, RDF.type, FOAF.Person),
            }
        )
        bnode = BNode()
        tsets.append(
            {
                (bnode, FOAF.name, Literal("Janov Pelorat")),
                (bnode, RDF.type, FOAF.Person),
            }
        )
        bnode = BNode()
        tsets.append(
            {
                (bnode, FOAF.name, Literal("R. Daneel Olivaw")),
                (bnode, RDF.type, FOAF.Person),
            }
        )
        cls.tsets = tsets

    def test_consistent_ids_ttl(self) -> None:

        graphs: t.List[Graph] = []
        cgraphs: t.List[Graph] = []
        ctsets: t.List[TripleSetT] = []
        accumulator: str = self.ttlpreamble
        for idx, ttlfrags in enumerate(self.ttlfrags):
            accumulator += ttlfrags
            graph = Graph()
            graph.parse(format="turtle", data=accumulator)
            graphs.append(graph)
            cgraph = to_canonical_graph(graph)
            cgraphs.append(cgraph)
            ctset = to_tripleset(cgraph)
            ctsets.append(ctset)
            if idx > 0:
                logging.debug(
                    "idx=%s:cgraphs[-2] = \n%s",
                    idx,
                    cgraphs[-2].skolemize().serialize(format="n3"),
                )
                logging.debug(
                    "idx=%s:cgraphs[-1] = \n%s",
                    idx,
                    cgraphs[-1].skolemize().serialize(format="n3"),
                )
                assert ctsets[-2].issubset(ctsets[-1])

    def test_canonicalizer(self) -> None:
        graph = Graph()
        graph += self.tsets[0]
        stats: t.Dict[str, t.Any] = {}

        tcan = _TripleCanonicalizer(graph)
        colors = tcan._initial_color()
        logging.info("colors = %s", colors)
        logging.info("colors = %s", [str(color) for color in colors])
        result = set(tcan.canonical_triples(stats))
        logging.info("stats = %s", stats)
        logging.info("result = %s", result)



        graph += self.tsets[1]
        stats = {}
        tcan = _TripleCanonicalizer(graph)
        colors = tcan._initial_color()
        logging.info("colors = %s", colors)
        logging.info("colors = %s", [str(color) for color in colors])
        result = set(tcan.canonical_triples(stats))
        logging.info("stats = %s", stats)
        logging.info("result = %s", result)

        # result = set(_TripleCanonicalizer(graph).canonical_triples(stats))
        # logging.info("stats = %s", stats)
        # logging.info("result = %s", result)


        # graph += self.tsets[1]
        # stats = {}
        # result = set(_TripleCanonicalizer(graph).canonical_triples(stats))
        # logging.info("stats = %s", stats)
        # logging.info("result = %s", result)

    def test_consistent_ids(self) -> None:

        graphs: t.List[Graph] = []
        cgraphs: t.List[Graph] = []
        ctsets: t.List[TripleSetT] = []
        accumulator: TripleSetT = set()
        for idx, tset in enumerate(self.tsets):
            accumulator.update(tset)
            graph = Graph()
            graph += accumulator
            graphs.append(graph)
            cgraph = to_canonical_graph(graph)
            cgraphs.append(cgraph)
            ctset = to_tripleset(cgraph)
            ctsets.append(ctset)
            if idx > 0:
                logging.debug(
                    "cgraphs[idx=%s-1] = \n%s",
                    idx,
                    cgraphs[idx - 1].skolemize().serialize(format="n3"),
                )
                logging.debug(
                    "cgraphs[idx=%s] = \n%s",
                    idx,
                    cgraphs[idx].skolemize().serialize(format="n3"),
                )
                assert ctsets[idx].issubset(ctsets[idx - 1])


if __name__ == "__main__":
    unittest.main()