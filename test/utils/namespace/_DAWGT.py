from rdflib.namespace import DefinedNamespace, Namespace
from rdflib.term import URIRef


class DAWGT(DefinedNamespace):
    _fail = True

    _NS = Namespace("http://www.w3.org/2001/sw/DataAccess/tests/test-dawg#")

    ResultForm: URIRef  # Super class of all result forms
    Status: URIRef  # Super class of all test status classes
    approval: URIRef  # The approval status of the test with respect to the working group.
    approvedBy: URIRef  # Contains a reference to the minutes of the RDF Data Access Working Group where the test case status was last changed.
    description: URIRef  # A human-readable summary of the test case.
    issue: URIRef  # Contains a pointer to the associated issue on the RDF Data Access Working Group Tracking document.
    resultForm: URIRef  # None
    warning: URIRef  # Indicates that while the test should pass, it may generate a warning.
