# -*- coding: utf-8 -*-
# https://github.com/RDFLib/rdflib-jsonld/blob/feature/json-ld-1.1/rdflib_jsonld/util.py
import typing as t

if t.TYPE_CHECKING:
    import json
else:
    try:
        import json

        assert json  # workaround for pyflakes issue #13
    except ImportError:
        import simplejson as json

from os import sep
from os.path import normpath
import re

from urllib.parse import urljoin, urlsplit, urlunsplit

from rdflib.parser import create_input_source

from io import StringIO


def source_to_json(source):
    # TODO: conneg for JSON (fix support in rdflib's URLInputSource!)
    source = create_input_source(source, format="json-ld")

    stream = source.getByteStream()
    try:
        return json.load(StringIO(stream.read().decode("utf-8")))
    finally:
        stream.close()


VOCAB_DELIMS = ("#", "/", ":")


def split_iri(iri):
    for delim in VOCAB_DELIMS:
        at = iri.rfind(delim)
        if at > -1:
            return iri[: at + 1], iri[at + 1 :]
    return iri, None


# https://datatracker.ietf.org/doc/html/rfc3986#appendix-A defines
# >    absolute-URI  = scheme ":" hier-part [ "?" query ]
# >    hier-part     = "//" authority path-abempty
# >                  / path-absolute
# >                  / path-rootless
# >                  / path-empty
# >    scheme        = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
# https://datatracker.ietf.org/doc/html/rfc3986#section-2.3 defines
# > For consistency, percent-encoded octets in the ranges of ALPHA
# > (%41-%5A and %61-%7A), DIGIT (%30-%39), hyphen (%2D), period (%2E),
# > underscore (%5F), or tilde (%7E) should not be created by URI
# > producers and, when found in a URI, should be decoded to their
# > corresponding unreserved characters by URI normalizers.
# _abs_url_re is crafted to match `scheme ":" "//"` which if matched will imply that the url is absolute.
_absolute_url_re = re.compile(
    r"^[\x41-\x5A\x61-\x7A][\x41-\x5A\x61-\x7A\x30-\x39+.-]*://"
)


def norm_url(base: str, url: str) -> str:
    """
    >>> norm_url('http://example.org/', '/one')
    'http://example.org/one'
    >>> norm_url('http://example.org/', '/one#')
    'http://example.org/one#'
    >>> norm_url('http://example.org/one', 'two')
    'http://example.org/two'
    >>> norm_url('http://example.org/one/', 'two')
    'http://example.org/one/two'
    >>> norm_url('http://example.org/', 'http://example.net/one')
    'http://example.net/one'
    >>> norm_url('http://example.org/', 'http://example.org//one')
    'http://example.org//one'
    >>> norm_url('http://example.org/', 'http://example.org')
    'http://example.org'
    >>> norm_url('http://example.org/', 'mailto:name@example.com')
    'mailto:name@example.com'
    """
    if _absolute_url_re.match(url):
        return url
    parts = urlsplit(urljoin(base, url))
    path = normpath(parts[2])
    if sep != "/":
        path = "/".join(path.split(sep))
    if parts[2].endswith("/") and not path.endswith("/"):
        path += "/"
    result = urlunsplit(parts[0:2] + (path,) + parts[3:])
    if url.endswith("#") and not result.endswith("#"):
        result += "#"
    return result


def context_from_urlinputsource(source):
    if source.content_type == "application/json":
        # response_info was added to InputSource in rdflib 4.2
        try:
            links = source.response_info.getallmatchingheaders("Link")
        except AttributeError:
            return
        for link in links:
            if ' rel="http://www.w3.org/ns/json-ld#context"' in link:
                i, j = link.index("<"), link.index(">")
                if i > -1 and j > -1:
                    return urljoin(source.url, link[i + 1 : j])
