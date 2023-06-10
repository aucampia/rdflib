# -*- coding: utf-8 -*-
#
# rdflib documentation build configuration file, created by
# sphinx-quickstart on Fri May 15 15:03:54 2009.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import logging
import os
import re
import sys
from typing import Any, Dict

import sphinx
import sphinx.application

import rdflib

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
# sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath(".."))

# -- General configuration -----------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
# extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.doctest']
extensions = [
    "sphinxcontrib.apidoc",
    "sphinx.ext.autodoc",
    #'sphinx.ext.autosummary',
    "sphinx_autodoc_typehints",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.ifconfig",
    "sphinx.ext.viewcode",
    "myst_parser",
    "sphinx.ext.autosectionlabel",
]

# https://github.com/sphinx-contrib/apidoc/blob/master/README.rst#configuration
apidoc_module_dir = "../rdflib"
apidoc_output_dir = "apidocs"

# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
autodoc_default_options = {"special-members": True}
autodoc_inherit_docstrings = True

# https://github.com/tox-dev/sphinx-autodoc-typehints
always_document_param_types = True

autosummary_generate = True

autosectionlabel_prefix_document = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# epydoc_mapping = {
#   '/_static/api/': [r'rdflib\.'],
#   }

# The suffix of source filenames.
source_suffix = ".rst"

# The encoding of source files.
source_encoding = "utf-8"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "rdflib"
copyright = "2009 - 2023, RDFLib Team"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.


# Find version. We have to do this because we can't import it in Python 3 until
# its been automatically converted in the setup process.
# UPDATE: This function is no longer used; once builds are confirmed to succeed, it
#         can/should be removed. --JCL 2022-12-30
def find_version(filename):
    _version_re = re.compile(r'__version__ = "(.*)"')
    for line in open(filename):
        version_match = _version_re.match(line)
        if version_match:
            return version_match.group(1)


# The full version, including alpha/beta/rc tags.
release = rdflib.__version__
# The short X.Y version.
version = re.sub("[0-9]+\\.[0-9]\\..*", "\1", release)

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
# language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
# today = ''
# Else, today_fmt is used as the format for a strftime call.
# today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
# unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ["_build", "draft"]

# The reST default role (used for this markup: `text`) to use for all documents.
default_role = "py:obj"

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
# show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# A list of ignored prefixes for module index sorting.
# modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

# The theme to use for HTML and HTML Help pages.  Major themes that come with
# Sphinx are currently 'default' and 'sphinxdoc'.
html_theme = "armstrong"


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
# html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
html_theme_path = [
    "_themes",
]

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
# html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = None

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
# html_logo = None
html_logo = "_static/RDFlib.png"

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "_static/RDFlib.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
# html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
# html_additional_pages = {}

# If false, no module index is generated.
# html_use_modindex = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = "rdflibdoc"


# -- Options for LaTeX output --------------------------------------------------

# The paper size ('letter' or 'a4').
# latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
# latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
# latex_documents = [
#     ("index", "rdflib.tex", "rdflib Documentation", "RDFLib Team", "manual"),
# ]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
# latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
# latex_use_parts = False

# Additional stuff for the LaTeX preamble.
# latex_preamble = ''

# Documents to append as an appendix to all manuals.
# latex_appendices = []

# If false, no module index is generated.
# latex_use_modindex = True


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3.8", None),
}

html_experimental_html5_writer = True

needs_sphinx = "4.1.2"

suppress_warnings = [
    # This is here to prevent:
    #  "WARNING: more than one target found for cross-reference"
    "ref.python",
    "autosectionlabel.*",
]

sphinx_version = tuple(int(part) for part in sphinx.__version__.split("."))


nitpicky = True

if sphinx_version < (5,):
    # Being nitpicky on Sphinx 4.x causes lots of problems.
    logging.warning(
        "disabling nitpicky because sphinx is too old: %s", sphinx.__version__
    )
    nitpicky = False

nitpick_ignore = [
    ("py:class", "urllib.response.addinfourl"),
    ("py:data", "typing.Literal"),
    ("py:class", "typing.IO[bytes]"),
    ("py:class", "http.client.HTTPMessage"),
    ("py:class", "importlib.metadata.EntryPoint"),
    ("py:class", "xml.dom.minidom.Document"),
    ("py:class", "xml.dom.minidom.DocumentFragment"),
    ("py:class", "isodate.duration.Duration"),
    # sphinx-autodoc-typehints has some issues with TypeVars.
    # https://github.com/tox-dev/sphinx-autodoc-typehints/issues/39
    ("py:class", "rdflib.plugin.PluginT"),
    # sphinx-autodoc-typehints does not like generic parmaeters in inheritance it seems
    ("py:class", "Identifier"),
    # These are related to pyparsing.
    ("py:class", "Diagnostics"),
    ("py:class", "ParseAction"),
    ("py:class", "ParseFailAction"),
    ("py:class", "pyparsing.core.TokenConverter"),
    ("py:class", "pyparsing.results.ParseResults"),
    # These are related to BerkeleyDB
    ("py:class", "db.DBEnv"),
]

if sys.version_info < (3, 9):
    nitpick_ignore.extend(
        [
            ("py:class", "_ContextIdentifierType"),
            ("py:class", "_ContextType"),
            ("py:class", "_GraphT"),
            ("py:class", "_NamespaceSetString"),
            ("py:class", "_ObjectType"),
            ("py:class", "_PredicateType"),
            ("py:class", "_QuadSelectorType"),
            ("py:class", "_SubjectType"),
            ("py:class", "_TripleOrPathTripleType"),
            ("py:class", "_TripleOrQuadPathPatternType"),
            ("py:class", "_TripleOrQuadPatternType"),
            ("py:class", "_TriplePathPatternType"),
            ("py:class", "_TriplePathType"),
            ("py:class", "_TriplePatternType"),
            ("py:class", "_TripleSelectorType"),
            ("py:class", "_TripleType"),
            ("py:class", "_TripleOrTriplePathType"),
            ("py:class", "TextIO"),
            ("py:class", "Message"),
        ]
    )


def autodoc_skip_member_handler(
    app: sphinx.application.Sphinx,
    what: str,
    name: str,
    obj: Any,
    skip: bool,
    options: Dict[str, Any],
):
    """
    This function will be called by Sphinx when it is deciding whether to skip a
    member of a class or module.
    """
    # https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#event-autodoc-skip-member
    if (
        app.env.docname == "apidocs/rdflib"
        and what == "module"
        and type(obj).__name__.endswith("DefinedNamespaceMeta")
    ):
        # Don't document namespaces in the `rdflib` module, they will be
        # documented in the `rdflib.namespace` module instead and Sphinx does
        # not like when these are documented in two places.
        #
        # An example of the WARNINGS that occur without this is:
        #
        # "WARNING: duplicate object description of rdflib.namespace._SDO.SDO,
        # other instance in apidocs/rdflib, use :noindex: for one of them"
        logging.info(
            "Skipping %s %s in %s, it will be documented in ",
            what,
            name,
            app.env.docname,
        )
        return True
    return None


# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#skipping-members
def setup(app: sphinx.application.Sphinx) -> None:
    """
    Setup the Sphinx application.
    """

    # Register a autodoc-skip-member handler so that certain members can be
    # skipped.
    app.connect("autodoc-skip-member", autodoc_skip_member_handler)
