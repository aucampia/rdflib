# tests for the turtle2 serializer

import logging
from typing import Union
from rdflib import Graph, Namespace, Literal
import pytest
from pathlib import Path


def test_turtle2():
    g = Graph()

    g.parse(
        data="""
        @prefix ex: <https://example.org/> .
        @prefix ex2: <https://example2.org/> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

        <https://something.com/a>
            a ex:Thing , ex:OtherThing ;
            ex:name "Thing", "Other Thing"@en , "もの"@ja , "rzecz"@pl ;
            ex:singleValueProp "propval" ;
            ex:multiValueProp "propval 1" ;
            ex:multiValueProp "propval 2" ;
            ex:multiValueProp "propval 3" ;
            ex:multiValueProp "propval 4" ;
            ex:bnObj [
                ex:singleValueProp "propval" ;
                ex:multiValueProp "propval 1" ;
                ex:multiValueProp "propval 2" ;
                ex:bnObj [
                    ex:singleValueProp "propval" ;
                    ex:multiValueProp "propval 1" ;
                    ex:multiValueProp "propval 2" ;
                    ex:bnObj [
                        ex:singleValueProp "propval" ;
                        ex:multiValueProp "propval 1" ;
                        ex:multiValueProp "propval 2" ;
                    ] ,
                    [
                        ex:singleValueProp "propval" ;
                        ex:multiValueProp "propval 1" ;
                        ex:multiValueProp "propval 2" ;
                    ] ,
                    [
                        ex:singleValueProp "propval" ;
                        ex:multiValueProp "propval 1" ;
                        ex:multiValueProp "propval 2" ;
                    ] ;
                ] ;
            ] ;
        .

        ex:b
            rdf:type ex:Thing ;
            ex:name "B" ;
            ex2:name "B" .

        ex:c
            rdf:type ex:Thing ;
            ex:name "C" ;
            ex:lst2 (
                ex:one
                ex:two
                ex:three
            ) ;
            ex:lst (
                ex:one
                ex:two
                ex:three
            ) ,
            (
                ex:four
                ex:fize
                ex:six
            ) ;
            ex:bnObj [
                ex:lst (
                    ex:one
                    ex:two
                    ex:three
                ) ,
                (
                    ex:four
                    ex:fize
                    ex:six
                ) ;
            ] .
        """,
        format="turtle",
    )
    s = g.serialize(format="turtle2")
    lines = s.split("\n")

    assert "ex:b" in lines
    assert "    a ex:Thing ;" in lines
    assert (
        """    ex2:name "B" ;
."""
        in s
    )
    assert (
        """                (
                    ex:one
                    ex:two
                    ex:three
                ) ,"""
        in s
    )
    assert '    ex:singleValueProp "propval" ;' in lines

    expected_s = """PREFIX ex: <https://example.org/>
PREFIX ex2: <https://example2.org/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

ex:b
    a ex:Thing ;
    ex:name "B" ;
    ex2:name "B" ;
.

ex:c
    a ex:Thing ;
    ex:bnObj [
            ex:lst
                (
                    ex:one
                    ex:two
                    ex:three
                ) ,
                (
                    ex:four
                    ex:fize
                    ex:six
                )
        ] ;
    ex:lst
        (
            ex:four
            ex:fize
            ex:six
        ) ,
        (
            ex:one
            ex:two
            ex:three
        ) ;
    ex:lst2 (
            ex:one
            ex:two
            ex:three
        ) ;
    ex:name "C" ;
.

<https://something.com/a>
    a
        ex:OtherThing ,
        ex:Thing ;
    ex:bnObj [
            ex:bnObj [
                    ex:bnObj
                        [
                            ex:multiValueProp
                                "propval 1" ,
                                "propval 2" ;
                            ex:singleValueProp "propval"
                        ] ,
                        [
                            ex:multiValueProp
                                "propval 1" ,
                                "propval 2" ;
                            ex:singleValueProp "propval"
                        ] ,
                        [
                            ex:multiValueProp
                                "propval 1" ,
                                "propval 2" ;
                            ex:singleValueProp "propval"
                        ] ;
                    ex:multiValueProp
                        "propval 1" ,
                        "propval 2" ;
                    ex:singleValueProp "propval"
                ] ;
            ex:multiValueProp
                "propval 1" ,
                "propval 2" ;
            ex:singleValueProp "propval"
        ] ;
    ex:multiValueProp
        "propval 1" ,
        "propval 2" ,
        "propval 3" ,
        "propval 4" ;
    ex:name
        "Thing" ,
        "Other Thing"@en ,
        "もの"@ja ,
        "rzecz"@pl ;
    ex:singleValueProp "propval" ;
.

"""

    assert s == expected_s

    # re-parse test
    g2 = Graph().parse(data=s)  # turtle
    assert len(g2) == len(g)


@pytest.mark.parametrize(
    "turtle_data,literal",
    [
        (
            b'<http://example.com/subject> <http://example.com/predicate> """l0\r\nl1""".',
            Literal("l0\r\nl1"),
        )
    ],
)
def test_literal_parsing(turtle_data: bytes, literal: Literal, tmp_path: Path) -> None:
    g = Graph()
    logging.info("turtle_data = %s", turtle_data)
    tmp_file = tmp_path / "file.ttl"
    tmp_file.write_bytes(turtle_data)
    g.parse(tmp_file, format="turtle")
    logging.info("g = %s", g.serialize())
    EG = Namespace("http://example.com/")
    objects = list(g.objects(EG.subject, EG.predicate))
    assert len(objects) == 1
    object = objects[0]
    logging.info("object = %s", object)
    logging.info("literal = %s", literal)
    assert object == literal
