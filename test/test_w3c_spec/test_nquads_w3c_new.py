"""This runs the nt tests for the W3C RDF Working Group's N-Quads
test suite."""
import logging
import os
from contextlib import ExitStack
from pathlib import Path
from test.data import TEST_DATA_DIR
from test.utils import GraphHelper
from test.utils.iri import file_uri_to_path, rebase_url
from test.utils.manifest import RDFTest, read_manifest
from test.utils.namespace import RDFT
from test.utils.rdftest import ManifestEntry, local_file_path, params_from_sources
from typing import Callable, Dict, Optional

import pytest

from rdflib import Graph
from rdflib.exceptions import ParserError
from rdflib.graph import Dataset, Graph
from rdflib.namespace import RDF
from rdflib.term import Node, URIRef

logger = logging.getLogger(__name__)


REMOTE_BASE_IRI = "http://www.w3.org/2013/NQuadsTests/"
LOCAL_BASE_DIR = TEST_DATA_DIR / "suites/w3c/nquads/"

VALID_TYPES = {RDFT.TestNQuadsPositiveSyntax, RDFT.TestNQuadsNegativeSyntax}


def check_entry(entry: ManifestEntry) -> None:
    assert entry.mf_action is not None
    assert entry.type in VALID_TYPES
    action_local = rebase_url(entry.mf_action, REMOTE_BASE_IRI, LOCAL_BASE_DIR.as_uri())
    if logger.isEnabledFor(logging.DEBUG):
        action_path = file_uri_to_path(action_local, Path)
        logger.debug("action = %s\n%s", action_path, action_path.read_text())
    catcher: Optional[pytest.ExceptionInfo[Exception]] = None
    with ExitStack() as xstack:
        if entry.type == RDFT.TestNQuadsNegativeSyntax:
            catcher = xstack.enter_context(pytest.raises(Exception))
        dataset = Dataset()
        dataset.parse(action_local, publicID=entry.mf_action, format="nquads")
    if catcher is not None:
        assert catcher.value is not None


@pytest.mark.parametrize(
    ["manifest_entry"],
    params_from_sources(
        LOCAL_BASE_DIR / "manifest.ttl",
        public_id=REMOTE_BASE_IRI,
        mark_dict={
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-uri-02": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-uri-03": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-uri-04": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-uri-05": pytest.mark.xfail(
                reason="accepts an invalid IRI"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-esc-01": pytest.mark.xfail(
                reason="accepts badly escaped literal"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-esc-02": pytest.mark.xfail(
                reason="accepts badly escaped literal"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-esc-03": pytest.mark.xfail(
                reason="accepts badly escaped literal"
            ),
            f"{REMOTE_BASE_IRI}#nt-syntax-bad-esc-04": pytest.mark.xfail(
                reason="accepts badly escaped literal"
            ),
        },
    ),
)
def test_entry(manifest_entry: ManifestEntry) -> None:
    check_entry(manifest_entry)
