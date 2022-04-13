# Meta-documentation

This page gives basic explanation of how this documentation is built and maintained.

## Documentation generator

This documentation is built through [Sphinx](https://www.sphinx-doc.org/), a popular documentation generator
for (but not limited to) Python projects.

Sphinx supports, by default, [reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html)
as markup language for the documentation source files, which can be a bit obscure for the uninitiated user, unfortunately.
Instead, to make writing documentation more user-friendly, 
**MarkDown** was chosen as preferred base format because it is easier to use, more widely known and supported.
The [MyST-parser](https://myst-parser.readthedocs.io/en/latest/) plugin for Sphinx is used to make that possible.


## Quick syntax guide

This is just a superficial listing of some key MarkDown/MyST syntax features.
See the references under {ref}`syntax-further-reading` for more detailed information. 


### Markdown base

As a base, MyST follows the [CommonMark specification](https://spec.commonmark.org/current/) for MarkDown.
A very minimal example of this format with some headers, paragraphs and a list:

```md
# Page title

A paragraph explaining something **important**.

## Section title

Let's enumrate a couple of points:

- First item
- Another item
```

On the web, one can easily find multiple MarkDown tutorials and guides with more detail.


### MyST extensions

MyST adds a couple of extensions on top of Markdown for more advanced authoring of software documentation
as discussed in the [MyST Syntax Guide](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#).

In short, there are two main constructs:

1. [_Directives_ for block-level extensions](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#directives-a-block-level-extension-point), 
   which are enclosed in triple-backticks, 
   have a directive name in curly brackets and possibly 
   [additional parameters](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#parameterizing-directives). 
   For example, to embed a Python code snippet with line numbers and a caption:
   ````md
   ```{code-block} python
   :lineno-start: 23
   :caption: Code snippet with a caption
   
   for line in open(path, "r"):
       print(line)
   ```
   ````
   
   looks rendered like this:

   ```{code-block} python
   :lineno-start: 23
   :caption: Code snippet with a caption
   
   for line in open(path, "r"):
       print(line)
   ```
   
   
2. [_Roles_ for in-line extensions](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#roles-an-in-line-extension-point)
   are the more compact, in-line version of directives with format `` {role}`content` ``.
   For example for small mathematical formulas:
   ```md
   This is Euler's famous identity: {math}`e^{i\pi} + 1 = 0`
   ```
   which will be rendered as:

   > This is Euler's famous identity: {math}`e^{i\pi} + 1 = 0`


(syntax-references)=
### References

A common feature in documentation is referencing other internal parts or external sources,
which is supported as follows:

- [external links](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#markdown-links-and-referencing) 
  can be written the standard MarkDown way as `[link text][https://example.com/]` 
  which will create a link with text "link text", 
  linking to [https://example.com/](https://example.com/).

- link to another documentation file in the documentation tree, for example the index page:
  `[homepage](index.md)` will render as [homepage](index.md).

- link to a [custom anchor](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html#targets-and-cross-referencing),
  (like another (sub)section of the documentation).
  First, the anchor must be defined with the `(anchor)=` syntax.
  This section for example is preceded with this anchor:
  ```md
  (syntax-references)=
  ### References
  ```
  and can be referenced with `` {ref}`syntax-references` ``, 
  which will be rendered as {ref}`syntax-references`.


(syntax-further-reading)=
### Further reading

For more information or inspiration, see: 
- [learn MarkDown in 60 seconds](https://commonmark.org/help/) 
  or [experiment interectively](https://spec.commonmark.org/dingus/)
- [the MyST Syntax Guide](https://myst-parser.readthedocs.io/en/latest/syntax/syntax.html)
- [the Myst Syntax Reference](https://myst-parser.readthedocs.io/en/latest/syntax/reference.html)


## Build the documentation

To build the documentation locally (e.g. to check some updates/additions you made):

- Prerequisites
   - work in a virtual environment, 
     with the `dev` dependencies (such as `sphinx` and `myst-parser`) installed.
     For example, if this fits your workflow, 
     install the package in `--editable` mode with the `dev` extra (from the project root):
     ```bash
     pip install -e .[dev]
     ```

- Run `sphinx-build`, from the `docs` folder
   - the easiest option (if you have the `make` build tool) is:
     ```bash
     make html
     ```
   - if `make` is not available, or you need a bit more flexibility, run `sphinx build` directly:
     ```bash
     sphinx-build -b html source build/html
     ```

- Visit the generated HTML tree, by opening `docs/build/html/index.html` in your browser.
