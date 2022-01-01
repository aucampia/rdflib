from __future__ import print_function
import logging

import os
import sys
from types import TracebackType
import isodate
import datetime
import random

from contextlib import AbstractContextManager, contextmanager
from typing import (
    Callable,
    Iterable,
    List,
    NoReturn,
    Optional,
    TYPE_CHECKING,
    Type,
    Iterator,
    Set,
    Tuple,
    Dict,
    Any,
    TypeVar,
    Union,
    cast,
    NamedTuple,
)
from urllib.parse import ParseResult, unquote, urlparse, parse_qs
from traceback import print_exc
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
import email.message
import unittest

from rdflib import BNode, Graph, ConjunctiveGraph
from rdflib.term import Identifier, Node
from unittest.mock import MagicMock, Mock
from urllib.error import HTTPError
from urllib.request import urlopen
from pathlib import PurePath, PureWindowsPath
from nturl2path import url2pathname as nt_url2pathname

if TYPE_CHECKING:
    import typing_extensions as te

import warnings



def get_random_ip(parts: List[str] = None) -> str:
    if parts is None:
        parts = ["127"]
    for _ in range(4 - len(parts)):
        parts.append(f"{random.randint(0, 255)}")
    return ".".join(parts)


@contextmanager
def ctx_http_server(
    handler: Type[BaseHTTPRequestHandler], host: str = "127.0.0.1"
) -> Iterator[HTTPServer]:
    server = HTTPServer((host, 0), handler)
    server_thread = Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    yield server
    server.shutdown()
    server.socket.close()
    server_thread.join()


IdentifierTriple = Tuple[Identifier, Identifier, Identifier]
IdentifierTripleSet = Set[IdentifierTriple]
IdentifierQuad = Tuple[Identifier, Identifier, Identifier, Identifier]
IdentifierQuadSet = Set[IdentifierQuad]


class GraphHelper:
    """
    Various functions to assist with graphs.
    """

    @classmethod
    def identifier(self, node: Node) -> Identifier:
        if isinstance(node, Graph):
            return node.identifier
        else:
            return cast(Identifier, node)

    @classmethod
    def identifiers(cls, nodes: Tuple[Node, ...]) -> Tuple[Identifier, ...]:
        result = []
        for node in nodes:
            result.append(cls.identifier(node))
        return tuple(result)

    @classmethod
    def triple_set(cls, graph: Graph, exclude_blanks: bool = False) -> IdentifierTripleSet:
        result = set()
        for sn, pn, on in graph.triples((None, None, None)):
            s, p, o = cls.identifiers((sn, pn, on))
            if exclude_blanks and (isinstance(s, BNode) or isinstance(o, BNode)):
                continue
            result.add((s, p, o))
        return result

    @classmethod
    def triple_sets(
        cls, graphs: Iterable[Graph], exclude_blanks: bool = False
    ) -> List[IdentifierTripleSet]:
        result: List[IdentifierTripleSet] = []
        for graph in graphs:
            result.append(cls.triple_set(graph, exclude_blanks))
        return result

    @classmethod
    def assert_triples_equal(
        cls, lhs: Graph, rhs: Graph, exclude_blanks: bool = False
    ) -> None:
        """
        While this function is functionally equivalent to assert
        lhs.isomorphic(rhs), it is written in a way that will make pytest
        report the sets so it is easier to inspect what is missing if the
        assert fails.
        """
        lhs_set = cls.triple_set(lhs, exclude_blanks)
        rhs_set = cls.triple_set(rhs, exclude_blanks)
        logging.debug("lhs_set = %s", lhs_set)
        logging.debug("rhs_set = %s", rhs_set)
        if (
            exclude_blanks
            and (len(lhs_set) == len(rhs_set) == 0)
            and len(cls.triple_set(lhs)) != 0
        ):
            warnings.warn(
                f"assert_quads_equal with exclude_blanks={exclude_blanks} "
                "on graph that has a blank node in each triple"
            )
        assert lhs_set == rhs_set



GenericT = TypeVar("GenericT", bound=Any)


def make_spypair(method: GenericT) -> Tuple[GenericT, Mock]:
    m = MagicMock()

    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        m(*args, **kwargs)
        return method(self, *args, **kwargs)

    setattr(wrapper, "mock", m)
    return cast(GenericT, wrapper), m


HeadersT = Dict[str, List[str]]
PathQueryT = Dict[str, List[str]]


class MockHTTPRequests(NamedTuple):
    method: str
    path: str
    parsed_path: ParseResult
    path_query: PathQueryT
    headers: email.message.Message


class MockHTTPResponse(NamedTuple):
    status_code: int
    reason_phrase: str
    body: bytes
    headers: HeadersT


class SimpleHTTPMock:
    """
    SimpleHTTPMock allows testing of code that relies on an HTTP server.

    NOTE: Currently only the GET and POST methods is supported.

    Objects of this class has a list of responses for each method (GET, POST, etc...)
    and returns these responses for these methods in sequence.

    All request received are appended to a method specific list.

    Example usage:
    >>> httpmock = SimpleHTTPMock()
    >>> with ctx_http_server(httpmock.Handler) as server:
    ...    url = "http://{}:{}".format(*server.server_address)
    ...    # add a response the server should give:
    ...    httpmock.do_get_responses.append(
    ...        MockHTTPResponse(404, "Not Found", b"gone away", {})
    ...    )
    ...
    ...    # send a request to get the first response
    ...    http_error: Optional[HTTPError] = None
    ...    try:
    ...        urlopen(f"{url}/bad/path")
    ...    except HTTPError as caught:
    ...        http_error = caught
    ...
    ...    assert http_error is not None
    ...    assert http_error.code == 404
    ...
    ...    # get and validate request that the mock received
    ...    req = httpmock.do_get_requests.pop(0)
    ...    assert req.path == "/bad/path"
    """

    # TODO: add additional methods (PUT, PATCH, ...) similar to GET and POST
    def __init__(self):
        self.do_get_requests: List[MockHTTPRequests] = []
        self.do_get_responses: List[MockHTTPResponse] = []

        self.do_post_requests: List[MockHTTPRequests] = []
        self.do_post_responses: List[MockHTTPResponse] = []

        _http_mock = self

        class Handler(SimpleHTTPRequestHandler):
            http_mock = _http_mock

            def _do_GET(self):
                parsed_path = urlparse(self.path)
                path_query = parse_qs(parsed_path.query)
                request = MockHTTPRequests(
                    "GET", self.path, parsed_path, path_query, self.headers
                )
                self.http_mock.do_get_requests.append(request)

                response = self.http_mock.do_get_responses.pop(0)
                self.send_response(response.status_code, response.reason_phrase)
                for header, values in response.headers.items():
                    for value in values:
                        self.send_header(header, value)
                self.end_headers()

                self.wfile.write(response.body)
                self.wfile.flush()
                return

            (do_GET, do_GET_mock) = make_spypair(_do_GET)

            def _do_POST(self):
                parsed_path = urlparse(self.path)
                path_query = parse_qs(parsed_path.query)
                request = MockHTTPRequests(
                    "POST", self.path, parsed_path, path_query, self.headers
                )
                self.http_mock.do_post_requests.append(request)

                response = self.http_mock.do_post_responses.pop(0)
                self.send_response(response.status_code, response.reason_phrase)
                for header, values in response.headers.items():
                    for value in values:
                        self.send_header(header, value)
                self.end_headers()

                self.wfile.write(response.body)
                self.wfile.flush()
                return

            (do_POST, do_POST_mock) = make_spypair(_do_POST)

            def log_message(self, format: str, *args: Any) -> None:
                pass

        self.Handler = Handler
        self.do_get_mock = Handler.do_GET_mock
        self.do_post_mock = Handler.do_POST_mock

    def reset(self):
        self.do_get_requests.clear()
        self.do_get_responses.clear()
        self.do_get_mock.reset_mock()
        self.do_post_requests.clear()
        self.do_post_responses.clear()
        self.do_post_mock.reset_mock()

    @property
    def call_count(self):
        return self.do_post_mock.call_count + self.do_get_mock.call_count


class SimpleHTTPMockTests(unittest.TestCase):
    def test_example(self) -> None:
        httpmock = SimpleHTTPMock()
        with ctx_http_server(httpmock.Handler) as server:
            url = "http://{}:{}".format(*server.server_address)
            # add two responses the server should give:
            httpmock.do_get_responses.append(
                MockHTTPResponse(404, "Not Found", b"gone away", {})
            )
            httpmock.do_get_responses.append(
                MockHTTPResponse(200, "OK", b"here it is", {})
            )

            # send a request to get the first response
            with self.assertRaises(HTTPError) as raised:
                urlopen(f"{url}/bad/path")
            assert raised.exception.code == 404

            # get and validate request that the mock received
            req = httpmock.do_get_requests.pop(0)
            self.assertEqual(req.path, "/bad/path")

            # send a request to get the second response
            resp = urlopen(f"{url}/")
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), b"here it is")

            httpmock.do_get_responses.append(
                MockHTTPResponse(404, "Not Found", b"gone away", {})
            )
            httpmock.do_get_responses.append(
                MockHTTPResponse(200, "OK", b"here it is", {})
            )


class ServedSimpleHTTPMock(SimpleHTTPMock, AbstractContextManager):
    """
    ServedSimpleHTTPMock is a ServedSimpleHTTPMock with a HTTP server.

    Example usage:
    >>> with ServedSimpleHTTPMock() as httpmock:
    ...    # add a response the server should give:
    ...    httpmock.do_get_responses.append(
    ...        MockHTTPResponse(404, "Not Found", b"gone away", {})
    ...    )
    ...
    ...    # send a request to get the first response
    ...    http_error: Optional[HTTPError] = None
    ...    try:
    ...        urlopen(f"{httpmock.url}/bad/path")
    ...    except HTTPError as caught:
    ...        http_error = caught
    ...
    ...    assert http_error is not None
    ...    assert http_error.code == 404
    ...
    ...    # get and validate request that the mock received
    ...    req = httpmock.do_get_requests.pop(0)
    ...    assert req.path == "/bad/path"
    """

    def __init__(self, host: str = "127.0.0.1"):
        super().__init__()
        self.server = HTTPServer((host, 0), self.Handler)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self) -> None:
        self.server.shutdown()
        self.server.socket.close()
        self.server_thread.join()

    @property
    def address_string(self) -> str:
        (host, port) = self.server.server_address
        return f"{host}:{port}"

    @property
    def url(self) -> str:
        return f"http://{self.address_string}"

    def __enter__(self) -> "ServedSimpleHTTPMock":
        return self

    def __exit__(
        self,
        __exc_type: Optional[Type[BaseException]],
        __exc_value: Optional[BaseException],
        __traceback: Optional[TracebackType],
    ) -> "te.Literal[False]":
        self.stop()
        return False


class ServedSimpleHTTPMockTests(unittest.TestCase):
    def test_example(self) -> None:
        with ServedSimpleHTTPMock() as httpmock:
            # add two responses the server should give:
            httpmock.do_get_responses.append(
                MockHTTPResponse(404, "Not Found", b"gone away", {})
            )
            httpmock.do_get_responses.append(
                MockHTTPResponse(200, "OK", b"here it is", {})
            )

            # send a request to get the first response
            with self.assertRaises(HTTPError) as raised:
                urlopen(f"{httpmock.url}/bad/path")
            assert raised.exception.code == 404

            # get and validate request that the mock received
            req = httpmock.do_get_requests.pop(0)
            self.assertEqual(req.path, "/bad/path")

            # send a request to get the second response
            resp = urlopen(f"{httpmock.url}/")
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.read(), b"here it is")

            httpmock.do_get_responses.append(
                MockHTTPResponse(404, "Not Found", b"gone away", {})
            )
            httpmock.do_get_responses.append(
                MockHTTPResponse(200, "OK", b"here it is", {})
            )


def eq_(lhs, rhs, msg=None):
    """
    This function mimicks the similar function from nosetest. Ideally nothing
    should use it but there is a lot of code that still does and it's fairly
    simple to just keep this small pollyfill here for now.
    """
    if msg:
        assert lhs == rhs, msg
    else:
        assert lhs == rhs


PurePathT = TypeVar("PurePathT", bound=PurePath)


def file_uri_to_path(
    file_uri: str,
    path_class: Type[PurePathT] = PurePath,  # type: ignore[assignment]
    url2pathname: Optional[Callable[[str], str]] = None,
) -> PurePathT:
    """
    This function returns a pathlib.PurePath object for the supplied file URI.

    :param str file_uri: The file URI ...
    :param class path_class: The type of path in the file_uri. By default it uses
        the system specific path pathlib.PurePath, to force a specific type of path
        pass pathlib.PureWindowsPath or pathlib.PurePosixPath
    :returns: the pathlib.PurePath object
    :rtype: pathlib.PurePath
    """
    is_windows_path = isinstance(path_class(), PureWindowsPath)
    file_uri_parsed = urlparse(file_uri)
    if url2pathname is None:
        if is_windows_path:
            url2pathname = nt_url2pathname
        else:
            url2pathname = unquote
    pathname = url2pathname(file_uri_parsed.path)
    result = path_class(pathname)
    return result
