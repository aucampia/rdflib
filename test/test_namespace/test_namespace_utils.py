"""
This module contains tests for utility functions in the `rdflib.namespace`
module.
"""


from typing import List, Optional, Tuple
import pytest
from rdflib.namespace import split_uri


@pytest.mark.parametrize(
    ["uri", "split_start", "expected_result"],
    [
        (
            "http://example.com/output/foo/bar",
            None,
            ("http://example.com/output/foo/", "bar"),
        ),
        (
            "http://example.com/output/foo:bar",
            None,
            ("http://example.com/output/foo:", "bar"),
        ),
    ],
)
def test_split_uri(uri: str, split_start: Optional[List[str]], expected_result: Tuple[str, str]) -> None:
    if split_start is None:
        result = split_uri(uri)
    else:
        result = split_uri(uri, split_start)
    assert result == expected_result
