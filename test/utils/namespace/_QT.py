from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef


class QT(DefinedNamespace):
    """
    DESCRIPTION_EDIT_ME_!

    Generated from: SOURCE_RDF_FILE_EDIT_ME_!
    Date: 2022-05-21 22:10:44.706416
    """

    _NS = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-query#")

    QueryForm: URIRef  # Super class of all query forms
    QueryTest: URIRef  # The class of query tests
    data: URIRef  # Optional: data for the query test
    graphData: URIRef  # Optional: named-graph only data for the query test (ie. not loaded into the background graph)
    query: URIRef  # The query to ask
    queryForm: URIRef  # None
