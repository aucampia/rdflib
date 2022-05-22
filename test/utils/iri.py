"""
Various utilities for working with IRIs and URIs.
"""


from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import Callable, Optional, Type, TypeVar
from urllib.parse import (
    ParseResult,
    parse_qs,
    quote,
    unquote,
    urlparse,
    urlsplit,
    urlunsplit,
)

from nturl2path import url2pathname as nt_url2pathname

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


def rebase_url(old_url: str, old_base: str, new_base: str) -> str:
    old_surl = urlsplit(old_url)
    old_base_surl = urlsplit(old_base)
    assert (old_surl.scheme, old_surl.netloc) == (
        old_base_surl.scheme,
        old_base_surl.netloc,
    )
    old_path = PurePosixPath(unquote(old_surl.path))
    old_base_path = PurePosixPath(unquote(old_base_surl.path))
    old_rpath = old_path.relative_to(old_base_path)
    new_base_surl = urlsplit(new_base)
    new_base_path = PurePosixPath(new_base_surl.path).joinpath(old_rpath)

    return urlunsplit(
        (
            new_base_surl.scheme,
            new_base_surl.netloc,
            quote(f"{new_base_path}"),
            old_surl.query,
            old_surl.fragment,
        )
    )
