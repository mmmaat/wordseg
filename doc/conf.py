#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# wordseg documentation build configuration file, created by
# sphinx-quickstart on Thu Apr  6 20:18:12 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import datetime
import sys
import wordseg

try:
    import sklearn.metrics.cluster
except ImportError:
    import mock
    sys.modules['sklearn.metrics.cluster'] = mock.MagicMock()


html_theme = "sphinx_rtd_theme"
# html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]


# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autosummary',
              'sphinx.ext.autodoc',
              'sphinx.ext.todo',
              'sphinx.ext.imgmath',
              'sphinx.ext.viewcode',
              'sphinx.ext.napoleon']

# The suffix(es) of source filenames. Support both markdown and rst
# source_parsers = {'.md': 'recommonmark.parser.CommonMarkParser'}
source_suffix = ['.rst']  # , '.md']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['wordseg_templates']

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'wordseg'
author = wordseg.author()
copyright = f'2017 - {datetime.datetime.now().year}, {author}'


# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

_VERSION = wordseg.version()

# The short X.Y version.
version = '.'.join(_VERSION.split('.')[:2])

# The full version, including alpha/beta/rc tags.
release = _VERSION

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['wordseg_static']
