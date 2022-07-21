"""
This module contains tests for the parsing of the turtle family of formats: N3,
Turtle, NTriples, NQauds and TriG.
"""

import enum
import itertools
from dataclasses import dataclass, field
import logging
import re
from typing import Callable, Dict, Iterator, List, Set, Tuple, Union

import pytest
from _pytest.mark.structures import Mark, MarkDecorator, ParameterSet

from rdflib import XSD, Graph, Literal, Namespace
from rdflib.term import Identifier
from rdflib.util import from_n3

OUTPUTURLNS = Namespace("http://example.com/output/")
MARKERNS = Namespace("example:test:")


@pytest.mark.parametrize(
    ["format", "namespace", "pname_ns", "pname_local", "expected_output"],
    [
        ("turtle", OUTPUTURLNS, "", r"foo", r":foo"),
        ("turtle", OUTPUTURLNS, "", r"foo~bar", r":foo~bar"),
        ("turtle", OUTPUTURLNS, "", r"foo/bar", r":foo\/bar"),
        ("turtle", OUTPUTURLNS, "", r"foo:bar", f"<{OUTPUTURLNS['foo:bar']}>"),
        ("turtle", OUTPUTURLNS, "ons", r"foo", r"ons:foo"),
        ("turtle", OUTPUTURLNS, "ons", r"foo/bar", r"ons:foo\/bar"),
        ("turtle", OUTPUTURLNS, "ons", r"foo_bar", r"ons:foo_bar"),
        ("turtle", OUTPUTURLNS, "ons", r"foo~bar", r":foo~bar"),
    ],
)
def test_pname(
    format: str,
    namespace: Namespace,
    pname_ns: str,
    pname_local: str,
    expected_output: str,
) -> None:
    graph = Graph(bind_namespaces="none")
    graph.bind(pname_ns, namespace)
    graph.bind("p_test_marker", MARKERNS)
    # graph.add((MARKERNS["subject0"], MARKERNS["predicate0"], namespace["object0"]))
    graph.add((MARKERNS["subject1"], MARKERNS["predicate1"], namespace[pname_local]))
    data = graph.serialize(format=format)
    logging.debug("data = %s", data)
    # pattern = re.compile(r"^.*\sp_test_marker:subject\s+_test_marker:predicate\s+(\S+)\s*.$", re.DOTALL)
    pattern = re.compile(
        r"^.*\sp_test_marker:subject1\s+p_test_marker:predicate1\s+(\S+)\s*[.]\s*$",
        re.DOTALL,
    )
    pmatch = pattern.match(data)
    logging.debug("pmatch = %s", pmatch)
    if pmatch is not None:
        logging.debug("pmatch.groups() = %s", pmatch.groups())
    assert pmatch is not None
    assert pmatch.group(1) == expected_output
    # assert data == ""
