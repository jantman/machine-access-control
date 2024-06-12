"""Sphinx configuration."""
project = "Machine_Access_Control"
author = "Jason Antman"
copyright = "2024, Jason Antman"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
