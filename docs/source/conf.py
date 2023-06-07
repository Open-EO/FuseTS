# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import datetime
import inspect
import os
import sys
import fusets


# -- Project information -----------------------------------------------------

title= 'System Design Document'
project = 'FuseTS'
copyright = '2022, Stefaan Lippens'
author = 'Stefaan Lippens, Jeroen Dries'

# The full version, including alpha/beta/rc tags
release = '0.0.1'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    'sphinx_autodoc_typehints',
    "sphinx.ext.linkcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.rsvgconverter"
]


myst_enable_extensions = [
    "amsmath",
    "colon_fence"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# The file extensions of source files. Sphinx considers the files with this suffix as sources.
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

latex_documents = [
    ('design.md', 'ai4food.tex', 'AI4Food Design definition file',
     'Jeroen Dries', 'manual'),
]

texinfo_documents = [
    ('design.md', 'DEL-03', 'Design Definition File',
     author, 'openeo', 'AI4Food Design Definition File',
     'Miscellaneous'),
]

latex_maketitle = r'''
\begin{titlepage}


\includepdf[pages=1]{TN_v1.1.pdf} 
\large
\newpage
~
%blank
\newpage

\begin{center}
  ~ \\
	 \vspace{0.5cm}
	 
	{\huge \textbf{AI4Food}} 
 	\vspace{3mm}
	
	{\LARGE \textbf{Design Definition File
			 \\ DEL-04 \\
			}}

	\vspace{1mm}
	
	{\large \vspace{2mm} ~ \\
	ESA AI4Food Project  \\
	Technical Officer: Patrick Griffiths 
    }
	 \vspace{1mm}
	 
	 
	 {\Large		
		J. Dries$^1$, S. Lippens$^1$}
        
      \vspace{0.5cm}  
				{\large  $^1$  \textbf{VITO} }\\
		Mol, Belgium\\
		\vspace{0.2cm}
		\vspace{0.2cm}
     \vspace{3cm} {\large 13th July, 2022} \vspace{0.2cm}
\end{center}
\end{titlepage}
'''
latex_logo='images/AI4Food.png'
latex_elements = {
    'preamble': r'''
\usepackage{pdfpages}
\usepackage{soul}
\usepackage{hyperref}
\usepackage[titles]{tocloft}
\usepackage{svg}
\cftsetpnumwidth {1.25cm}\cftsetrmarg{1.5cm}
\setlength{\cftchapnumwidth}{0.75cm}
\setlength{\cftsecindent}{\cftchapnumwidth}
\setlength{\cftsecnumwidth}{1.25cm}
''',
    #'fncychap': r'\usepackage[Bjornstrup]{fncychap}',
    'printindex': r'\footnotesize\raggedright\printindex',
    'maketitle': latex_maketitle,
}
latex_show_urls = 'footnote'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'furo'

html_theme_options = {
    'badge_branch': 'main',
    'github_user': 'Open-EO',
    'github_repo': 'FuseTS',
    'github_banner': True,
    'fixed_sidebar': False,
    'use_edit_page_button': True,
    'use_repository_button': True,
    'use_issues_button': True,
    'page_width': '1200px',
    'sidebar_width': '300px',
    'font_family': 'Cantarell, Georgia, serif',
    'code_font_family': "'Liberation Mono', 'Consolas', 'Menlo', 'DejaVu Sans Mono', 'Bitstream Vera Sans Mono', monospace",
    'extra_footer': """<p>FuseTS is built in the frame of the ESA AI4Food project.</p>""",
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/Open-EO/FuseTS",
            "html": """
                <svg stroke="currentColor" fill="currentColor" stroke-width="0" viewBox="0 0 16 16">
                    <path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"></path>
                </svg>
            """,
            "class": "",
        },
    ],
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_title = "FuseTS"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    "iris": ("https://scitools-iris.readthedocs.io/en/latest", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "numba": ("https://numba.pydata.org/numba-doc/latest", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
    "dask": ("https://docs.dask.org/en/latest", None),
    "cftime": ("https://unidata.github.io/cftime", None),
    "rasterio": ("https://rasterio.readthedocs.io/en/latest", None),
    "sparse": ("https://sparse.pydata.org/en/latest/", None),
    "xarray": ("https://docs.xarray.dev/en/stable/", None),
    "openeo": ("https://open-eo.github.io/openeo-python-client/", None),
}

# based on numpy doc/source/conf.py
def linkcode_resolve(domain, info):
    """
    Determine the URL corresponding to Python object
    """
    if domain != "py":
        return None

    modname = info["module"]
    fullname = info["fullname"]

    submod = sys.modules.get(modname)
    if submod is None:
        return None

    obj = submod
    for part in fullname.split("."):
        try:
            obj = getattr(obj, part)
        except AttributeError:
            return None

    try:
        fn = inspect.getsourcefile(inspect.unwrap(obj))
    except TypeError:
        fn = None
    if not fn:
        return None

    try:
        source, lineno = inspect.getsourcelines(obj)
    except OSError:
        lineno = None

    if lineno:
        linespec = f"#L{lineno}-L{lineno + len(source) - 1}"
    else:
        linespec = ""

    fn = os.path.relpath(fn, start=os.path.dirname(fusets.__file__))

    if "+" in fusets.__version__:
        return f"https://github.com/Open-EO/FuseTS/blob/main/src/fusets/{fn}{linespec}"
    else:
        return (
            f"https://github.com/Open-EO/FuseTS/blob/"
            f"v{fusets.__version__}/fusets/{fn}{linespec}"
        )