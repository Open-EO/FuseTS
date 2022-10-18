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
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

import datetime
import inspect
import os
import sys
import fusets

sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../source'))

# -- Project information -----------------------------------------------------

project = 'DEL-03 Design Definition File'
copyright = '2022, Stefaan Lippens'
author = 'Stefaan Lippens, Jeroen Dries'

# The full version, including alpha/beta/rc tags
release = '1.1.0'


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
    ('del03_ddf', 'DEL-03-DDF-AI4FOOD-1.1.tex', 'AI4Food Design definition file',
     'Jeroen Dries', 'manual'),
]

texinfo_documents = [
    ('del03_ddf', 'DEL-03', 'Design Definition File',
     author, 'openeo', 'AI4Food Design Definition File',
     'Miscellaneous'),
]

latex_maketitle = r'''
\begin{titlepage}



\begin{center}
   \vspace*{1cm}
   
   \includegraphics[width=0.5\textwidth]{AI4Food.png}
   \\
   \begin{huge}  
       \textbf{DEL-03 Design Definition File AI4FOOD
       \\
       (WP 2)}
   \end{huge}
   \\
   \vspace{0.5cm}
   \begin{LARGE}
        Version 1.1
        \\
        \vspace{0.3cm}
        13 Octobre 2022
   \end{LARGE}
   \vspace*{2.5cm}
   \\
   \begin{large}
        Prepared by    
   \end{large}
   \\
   \includegraphics[width=0.7\textwidth]{AI4Food_companies.png}
\end{center}

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
     \vspace{3cm} {\large 13th Octobre, 2022} \vspace{0.2cm}
\end{center}
\end{titlepage}

\begin{center}

\begin{tabular}{|l|l|l|l|}
\hline
Authors: & \multicolumn{3}{|l|}{J. Dries, M. Salinero-Delgado, S. Lippens, M. Lubej}  \\          
\hline
Circulation: & \multicolumn{3}{|l|}{ESA document}\\
\hline
Release & Date & Details & Editors \\
\hline
1.0 & 17 September 2022 & CDR Version & JD, SL, ML, MSD \\
\hline
1.1 & 13 Octobre 2022 & Integrated CDR RID's & JD, SL, ML, MSD \\
\hline
\end{tabular}

\vspace{2mm}
\end{center}
\newpage

'''

latex_toc = r'''

\tableofcontents
\newpage
\listoffigures
\listoftables

\newpage
'''

#latex_logo='../source/images/AI4Food.png'
latex_elements = {
    'preamble': r'''
\usepackage{pdfpages}
\usepackage{soul}
\usepackage{hyperref}
\usepackage[titles]{tocloft}
\usepackage{svg}
\usepackage{caption}
\cftsetpnumwidth {1.25cm}\cftsetrmarg{1.5cm}
\setlength{\cftsecindent}{0.75cm}
\setlength{\cftsecnumwidth}{1.25cm}
''',
    #'fncychap': r'\usepackage[Bjornstrup]{fncychap}',
    'printindex': '',#r'\footnotesize\raggedright\printindex',
    'makeindex': '',#r'\footnotesize\raggedright\printindex',
    'maketitle': latex_maketitle,
    'tableofcontents': latex_toc
}

latex_show_urls = 'footnote'

latex_additional_files=['../source/images/AI4Food.png','../source/images/AI4Food_companies.png']
latex_toplevel_sectioning = 'section'
latex_docclass= {'manual':'article','howto':'article'}

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

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
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

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