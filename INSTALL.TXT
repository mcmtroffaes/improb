Automatic Installer
~~~~~~~~~~~~~~~~~~~

The simplest way to install improb, is to `download <http://pypi.python.org/pypi/improb/#downloads>`_ the installer and run it. To use the library, you also need `pycddlib <http://pypi.python.org/pypi/pycddlib/#downloads>`_.

Building From Source
~~~~~~~~~~~~~~~~~~~~

To install from the latest source code, clone it with `Git <http://git-scm.com>`_ by running::

    git clone git://github.com/mcmtroffaes/improb

You can also browse the source code on GitHub: `mcmtroffaes/improb <http://github.com/mcmtroffaes/improb>`_.

Then simply run the :file:`build.sh` script: this will build the library, install it, generate the documentation, and run all the doctests. Note that you need `Sphinx <http://sphinx.pocoo.org/>`_ to generate the documentation and to run the doctests.

If you merely want to install the library from source, just run::

    python setup.py install
