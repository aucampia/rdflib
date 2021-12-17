from types import GeneratorType
from typing import Generator
from rdflib import Graph, URIRef, Literal, BNode, XSD
from rdflib.plugins.sparql import prepareQuery
from rdflib.compare import isomorphic
import rdflib
from .testutils import eq_
from pprint import pprint
import io
import pytest
import inspect


def test_dateTime_dateTime_subs_issue():
    """
    Test for query mentioned in the Issue #629
    https://github.com/RDFLib/rdflib/issues/629

    """

    data1 = """
    @prefix : <#>.
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.

    :C a rdfs:Class.

    :start a rdf:Property;
        rdfs:domain :C;
        rdfs:range xsd:dateTime.

    :end a rdf:Property;
        rdfs:domain :C;
        rdfs:range xsd:dateTime.

    :c1 a :C;
        :start "2016-01-01T20:00:00"^^xsd:dateTime;
        :end "2016-01-02T20:01:00"^^xsd:dateTime.

    :c2 a :C;
        :start "2016-01-01T20:05:00"^^xsd:dateTime;
        :end "2016-01-01T20:30:00"^^xsd:dateTime.
    """

    graph1 = Graph()
    f = io.StringIO(data1)
    graph1.parse(f, format="n3")

    result = graph1.query(
        """
    SELECT ?c ?duration
    WHERE {
        ?c :start ?start;
            :end ?end.
        BIND(?end - ?start AS ?duration)
    }
    """
    )

    answer = list(result)
    answer = sorted(answer)
    # expected result will be a list of 2 tuples
    # FirstElement of these tuples will be a node with a path of directory of saved project
    # Second Element while represent the actual durations

    expectedFirstDuration = rdflib.term.Literal(
        "P1DT1M",
        datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#duration"),
    )
    expectedSecondDuration = rdflib.term.Literal(
        "PT25M",
        datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#duration"),
    )

    eq_(answer[0][1], expectedFirstDuration)
    eq_(answer[1][1], expectedSecondDuration)


def test_dateTime_duration_subs():
    """
    Test cases for subtraction operation between dateTime and duration

    """
    data = """
    @prefix : <#>.
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.
    """
    graph = Graph()
    f = io.StringIO(data)
    graph.parse(f, format="n3")

    ## 1st Test Case

    result1 = graph.query(
        """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT (?d - ?duration AS ?next_year)
    WHERE {
        VALUES (?duration ?d) {
            ("P1Y"^^xsd:yearMonthDuration"2019-05-28T12:14:45Z"^^xsd:dateTime)
            ("P1Y"^^xsd:yearMonthDuration"2019-05-28"^^xsd:date)
        }
    }
    """
    )
    expected = []
    expected.append(
        rdflib.term.Literal(
            "2018-05-28T12:14:45+00:00",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#dateTime"),
        )
    )
    expected.append(
        rdflib.term.Literal(
            "2018-05-28",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#date"),
        )
    )

    # assert result1._bindings == []
    # assert isinstance(result1._genbindings, GeneratorType)
    # # assert inspect.isgeneratorfunction(result1._genbindings), ""
    # # assert type(result1._genbindings) == generator
    # # # assert result1._genbindings == []

    # print("before first check: ...")

    # # assert len(result1) > 0

    # # # len(result1._genbindings)
    # # list(result1._genbindings)

    # # return

    # # # assert len(result1.bindings) > 0

    # print("first check: ... result1._genbindings = ", result1._genbindings)
    # with pytest.raises(TypeError):
    #     z = list(result1._genbindings)
    #     print("z = ", z)
    # #     # len(result1.bindings)

    # assert result1._bindings == []
    # assert isinstance(result1._genbindings, GeneratorType)

    # print("second check: ... result1._genbindings = ", result1._genbindings)
    # with pytest.raises(TypeError):
    #     z = list(result1._genbindings)
    #     print("z = ", z)
    # #     # len(result1.bindings)

    # # # assert len(result1) > 0

    # # # with pytest.raises(TypeError):
    # # #     len(result1)
    # # # with pytest.raises(TypeError):
    # # #     len(result1)

    # # # result1l = list(result1)
    # # # assert len(result1l) > 0

    # # list(result1)[0][0]

    # return

    eq_(list(result1)[0][0], expected[0])
    eq_(list(result1)[1][0], expected[1])

    ## 2nd Test Case

    result2 = graph.query(
        """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT (?d - ?duration AS ?next_year)
    WHERE {
        VALUES (?duration ?d) {
            ("P3DT1H15M"^^xsd:dayTimeDuration "2000-10-30T11:12:00"^^xsd:dateTime)
		    ("P3DT1H15M"^^xsd:dayTimeDuration "2000-10-30"^^xsd:date)
        }
    }
    """
    )

    expected = []
    expected.append(
        rdflib.term.Literal(
            "2000-10-27T09:57:00",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#dateTime"),
        )
    )
    expected.append(
        rdflib.term.Literal(
            "2000-10-27",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#date"),
        )
    )

    # list(result2)[0][0]

    eq_(list(result2)[0][0], expected[0])
    eq_(list(result2)[1][0], expected[1])


def test_dateTime_duration_add():
    """
    Test cases for addition operation between dateTime and duration

    """
    data = """
    @prefix : <#>.
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.
    """
    graph = Graph()
    f = io.StringIO(data)
    graph.parse(f, format="n3")

    ## 1st Test case

    result1 = graph.query(
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

    # print(list(result1))
    expected = []
    expected.append(
        rdflib.term.Literal(
            "2020-05-28T12:14:45+00:00",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#dateTime"),
        )
    )
    expected.append(
        rdflib.term.Literal(
            "2020-05-28",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#date"),
        )
    )

    eq_(list(result1)[0][0], expected[0])
    eq_(list(result1)[1][0], expected[1])

    ## 2nd Test case

    result2 = graph.query(
        """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT (?d + ?duration AS ?next_year)
    WHERE {
        VALUES (?duration ?d) {
            ("P3DT1H15M"^^xsd:dayTimeDuration "2000-10-30T11:12:00"^^xsd:dateTime)
            ("P3DT1H15M"^^xsd:dayTimeDuration "2000-10-30"^^xsd:date)
        }
    }
    """
    )

    # print(list(result2))
    expected = []
    expected.append(
        rdflib.term.Literal(
            "2000-11-02T12:27:00",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#dateTime"),
        )
    )
    expected.append(
        rdflib.term.Literal(
            "2000-11-02",
            datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#date"),
        )
    )

    eq_(list(result2)[0][0], expected[0])
    eq_(list(result2)[1][0], expected[1])


def test_dateTime_dateTime_subs():
    """
    Test cases for subtraction operation between dateTime and dateTime

    """
    data = """
    @prefix : <#>.
    @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>.
    @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>.
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#>.
    """

    graph = Graph()
    f = io.StringIO(data)
    graph.parse(f, format="n3")

    result1 = graph.query(
        """
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    SELECT (?l - ?r AS ?duration)
    WHERE {
        VALUES (?l ?r) {
            ("2000-10-30T06:12:00-05:00"^^xsd:dateTime "1999-11-28T09:00:00Z"^^xsd:dateTime)
            ("2000-10-30"^^xsd:date"1999-11-28"^^xsd:date)
        }
    }
    """
    )

    expected1 = rdflib.term.Literal(
        "P337DT2H12M",
        datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#duration"),
    )
    expected2 = rdflib.term.Literal(
        "P337D",
        datatype=rdflib.term.URIRef("http://www.w3.org/2001/XMLSchema#duration"),
    )

    eq_(list(result1)[0][0], expected1)
    eq_(list(result1)[1][0], expected2)
