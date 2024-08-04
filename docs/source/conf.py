"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

import os
from urllib.parse import urlparse


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "machine-access-control"
copyright = "2024, Jason Antman"
author = "Jason Antman"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.todo",
    "sphinx.ext.intersphinx",
    "sphinx_last_updated_by_git",
]

templates_path = ["_templates"]
exclude_patterns = []

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "collapse_navigation": False,
    "sticky_navigation": False,
}
html_static_path = ["_static"]

html_context = {"theme_vcs_pageview_mode": "edit", "conf_py_path": "/source/"}

if os.environ.get("GITHUB_ACTIONS") == "true":
    html_context["display_github"] = True
    html_context["github_user"], html_context["github_repo"] = os.environ[
        "GITHUB_REPOSITORY"
    ].split("/")
    html_context["github_host"] = urlparse(os.environ["GITHUB_API_URL"]).hostname
    html_context["github_version"] = os.environ.get(
        "GITHUB_REF_NAME",
        os.environ.get("GITHUB_HEAD_REF", os.environ.get("GITHUB_SHA")),
    )

html_css_files = [
    # thanks to: https://rackerlabs.github.io/docs-rackspace/tools/rtd-tables.html
    "theme_overrides.css"  # override wide tables in RTD theme
]
