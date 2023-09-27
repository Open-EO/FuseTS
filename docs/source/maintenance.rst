.. _development-and-maintenance:

###########################
Development and maintenance
###########################


For development on the ``fusets`` package itself,
it is recommended to install a local git checkout of the project
in development mode (``-e``)
with additional development related dependencies (``[dev]``)
like this::

    pip install -e .[dev]

If you are on Windows and experience problems installing this way, you can find some solutions in section `Development Installation on Windows`_.

Running the unit tests
======================

The test suite of the FuseTS leverages
the nice `pytest <https://docs.pytest.org/en/stable/>`_ framework.
It is installed automatically when installing the FuseTS
with the ``[dev]`` extra as shown above.
Running the whole tests is as simple as executing::

    pytest

There are a ton of command line options for fine-tuning
(e.g. select a subset of tests, how results should be reported, ...).
Run ``pytest -h`` for a quick overview
or check the `pytest <https://docs.pytest.org/en/stable/>`_ documentation for more information.

For example::

    # Skip tests that are marked as slow
    pytest -m "not slow"


Building the documentation
==========================

Building the documentation requires `Sphinx <https://www.sphinx-doc.org/en/master/>`_
and some plugins
(which are installed automatically as part of the ``[dev]`` install).

Quick and easy
---------------

The easiest way to build the documentation is working from the ``docs`` folder
and using the ``Makefile``:

.. code-block:: shell

    # From `docs` folder
    make html

(assumes you have ``make`` available, if not: use ``python -msphinx -M html .  build``.)

This will generate the docs in HTML format under ``docs/build/html/``.
Open the HTML files manually,
or use Python's built-in web server to host them locally, e.g.:

.. code-block:: shell

    # From `docs` folder
    python -m http.server 8000

Then, visit  http://127.0.0.1:8000/build/html/ in your browser


Like a Pro
------------

When doing larger documentation work, it can be tedious to manually rebuild the docs
and refresh your browser to check the result.
Instead, use `sphinx-autobuild <https://github.com/executablebooks/sphinx-autobuild>`_
to automatically rebuild on documentation changes and live-reload it in your browser.
After installation (``pip install sphinx-autobuild`` in your development environment),
just run

.. code-block:: shell

    # From project root
    sphinx-autobuild docs/ --watch fusets/ docs/build/html/

and then visit http://127.0.0.1:8000 .
When you change (and save) documentation source files, your browser should now
automatically refresh and show the newly built docs. Just like magic.


Contributing code
==================

User contributions (such as bug fixes and new features, both in source code and documentation)
are greatly appreciated and welcome.


Pull requests
--------------

We use a traditional `GitHub Pull Request (PR) <https://docs.github.com/en/pull-requests>`_ workflow
for user contributions, which roughly follows these steps:

- Create a personal fork of https://github.com/Open-EO/FuseTS
  (unless you already have push permissions to an existing fork or the original repo)
- Preferably: work on your contribution in a new feature branch
- Push your feature branch to your fork and create a pull request
- The pull request is the place for review, discussion and fine-tuning of your work
- Once your pull request is in good shape it will be merged by a maintainer


.. _precommit:

Pre-commit for basic code quality checks
------------------------------------------

We started using the `pre-commit <https://pre-commit.com/>`_ tool
for basic code quality fine-tuning of new contributions.
Note that the whole repository does not adhere yet to these new code styles rules at the moment,
we're just gradually introducing it, piggybacking on new contributions and commits.
It's currently not enforced, but **enabling pre-commit is recommended** and appreciated
when contributing code.

Pre-commit set up
""""""""""""""""""

-   Install the ``pre-commit`` command line tool:

    -   The simplest option is to install it directly in the *virtual environment*
        you are using for FuseTS development (e.g. ``pip install pre-commit``).
    -   You can also install it *globally* on your system
        (e.g. using `pipx <https://pypa.github.io/pipx/>`_, conda, homebrew, ...)
        so you can use it across different projects.
-   Install the git hook scripts by running this in your local git clone:

    .. code-block:: console

        pre-commit install

    This will automatically install additional tools in a sandbox
    to run the various checks defined in the ``.pre-commit-config.yaml`` configuration file.

Pre-commit usage
"""""""""""""""""

When you commit new changes, the freshly installed pre-commit hook
will now automatically run each of the configured linters/formatters/...
Some of these just flag issues (e.g. invalid JSON files)
while others even automatically fix problems (e.g. clean up excessive whitespace).

If there is some kind of violation, the commit will be blocked.
Address these problems and try to commit again.

.. attention::

    Some pre-commit tools directly *edit* your files (e.g. formatting tweaks)
    instead of just flagging issues.
    This might feel intrusive at first, but once you get the hang of it,
    it should allow to streamline your workflow.

    In particular, it is recommended to use the *staging* feature of git to prepare your commit.
    Pre-commit's proposed changes are not staged automatically,
    so you can more easily keep them separate and review.

.. tip::

    You can temporarily disable pre-commit for these rare cases
    where you intentionally want to commit violating code style,
    e.g. through ``git commit`` command line option ``-n``/``--no-verify``.




Creating a release
==================

This section describes the procedure to create
properly versioned releases of the ``fusets`` package
that can be downloaded by end users (e.g. through ``pip`` from pypi.org)
and depended on by other projects.

The releases will end up on:

- PyPi: `https://pypi.org/project/fusets <https://pypi.org/project/fusets/>`_
- VITO Artifactory: `https://artifactory.vgt.vito.be/api/pypi/python-openeo/simple/fusets/ <https://artifactory.vgt.vito.be/api/pypi/python-openeo/simple/fusets/>`_
- GitHub: `https://github.com/Open-EO/FuseTS/releases <https://github.com/Open-EO/FuseTS/releases>`_

Prerequisites
-------------

-   You have permissions to push branches and tags and maintain releases on
    the `fusets project on GitHub <https://github.com/Open-EO/FuseTS>`_.
-   You have permissions to upload releases to the
    `fusets project on pypi.org <https://pypi.org/project/fusets>`_
-   The Python virtual environment you work in has the latest versions
    of the ``twine`` package installed.
    If you plan to build the wheel yourself (instead of letting Jenkins do this),
    you also need recent enough versions of the ``setuptools`` and ``wheel`` packages.

Important files
---------------

``setup.py``
    describes the metadata of the package,
    like package name ``fusets`` and version
    (which is extracted from ``fusets/__init__.py``).

``fusets/__init__.py``
    defines the version of the package.
    During general **development**, this version string should contain
    a `pre-release <https://www.python.org/dev/peps/pep-0440/#pre-releases>`_
    segment (e.g. ``a1`` for alpha releases, ``b1`` for beta releases, etc)
    to avoid collision with final releases. For example::

        __version__ = '1.0.0a1'

    As discussed below, this pre-release suffix should
    only be removed during the release procedure
    and restored when bumping the version after the release procedure.

``CHANGELOG.md``
    keeps track of important changes associated with each release.
    It follows the `Keep a Changelog <https://keepachangelog.com>`_ convention
    and should be properly updated with each bug fix, feature addition/removal, ...
    under the ``Unreleased`` section during development.

Procedure
---------

These are the steps to create and publish a new release of the ``fusets`` package.
To be as concrete as possible, we will assume that we are about to release version ``1.0.0``.

0.  Make sure you are working on **latest master branch**,
    without uncommitted changes and all tests are properly passing.

#.  Create release commit:

    A.  **Drop the pre-release suffix** from the version string in ``fusets/__init__.py``
        so that it just a "final" semantic versioning string, e.g. ``1.0.0``

    B.  **Update CHANGELOG.md**: rename the "Unreleased" section title
        to contain version and date, e.g.::

            ## [1.0.0] - 2020-12-15

        remove empty subsections
        and start a new "Unreleased" section above it, like::

            ## [Unreleased]

            ### Added

            ### Changed

            ### Removed

            ### Fixed


    C.  **Commit** these changes in git with a commit message like ``Release 1.0.0``
        and **push** to GitHub::

            git add fusets/__init__.py CHANGELOG.md
            git commit -m 'Release 1.0.0'
            git push origin main

#.  Optional, but recommended: wait for **VITO Jenkins** to build this updated master
    (trigger it manually if necessary),
    so that a build of a final, non-alpha release ``1.0.0``
    is properly uploaded to **VITO artifactory**.

#.  Create release on `PyPI <https://pypi.org/>`_:

    A.  **Obtain a wheel archive** of the package, with one of these approaches:

        -   *Preferably, the path of least surprise*: build wheel through GitHub Actions.
            Go to workflow `"Build wheel" <https://github.com/Open-EO/FuseTS/actions/workflows/build-wheel.yml>`_,
            manually trigger a build with "Run workflow" button, wait for it to finish successfully,
            download generated ``artifact.zip``, and finally: unzip it to obtain ``fusets-1.0.0-py3-none-any.whl``

        -   *Or, if you know what you are doing* and you're sure you have a clean
            local checkout, you can also build it locally::

                python setup.py bdist_wheel

            This should create ``dist/fusets-1.0.0-py3-none-any.whl``

    B.  **Upload** this wheel to `PyPI <https://pypi.org/project/fusets/>`_::

            python -m twine upload fusets-1.0.0-py3-none-any.whl

        Check the `release history on PyPI <https://pypi.org/project/fusets/#history>`_
        to verify the twine upload.
        Another way to verify that the freshly created release installs
        is using docker to do a quick install-and-burn,
        for example as follows (check the installed version in pip's output)::

            docker run --rm -it python python -m pip install --no-deps fusets

#.  Create a **git version tag** and push it to GitHub::

        git tag v1.0.0
        git push origin v1.0.0

#.  Create a **release in GitHub**:
    Go to `https://github.com/Open-EO/FuseTS/releases/new <https://github.com/Open-EO/FuseTS/releases/new>`_,
    Enter ``v1.0.0`` under "tag",
    enter title: ``FuseTS v1.0.0``,
    use the corresponding ``CHANGELOG.md`` section as description
    and publish it
    (no need to attach binaries).

#.  **Bump version** in ``fusets/__init__.py``,
    and append a pre-release "a1" suffix again, for example::

        __version__ = '1.0.1a1'

    Commit this (e.g. with message ``__init__.py: bump to 1.0.1a1``)
    and push to GitHub.

Verification
"""""""""""""

The new release should now be available/listed at:

- `https://pypi.org/project/fusets/#history <https://pypi.org/project/fusets/#history>`_
- `https://github.com/Open-EO/FuseTS/releases <https://github.com/Open-EO/FuseTS/releases>`_

Here is a bash (subshell) oneliner to verify that the PyPI release works properly::

    (
        cd /tmp &&\
        python -m venv venv-fusets &&\
        source venv-fusets/bin/activate &&\
        pip install -U fusets &&\
        python -c "import fusets;print(fusets)"
    )

It tries to install the latest version of the ``fusets`` package in a temporary virtual env,
import it and print the package information.


Development Installation on Windows
===================================

Normally you can install the client the same way on Windows as on Linux, like so:

.. code-block:: console

    pip install -e .[dev]