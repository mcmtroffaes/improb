Automatic Installer
~~~~~~~~~~~~~~~~~~~

The simplest way to install improb, is to `download <http://pypi.python.org/pypi/improb/#downloads>`_ the installer and run it. To use the library, you also need `pycddlib <http://pypi.python.org/pypi/pycddlib/#downloads>`_.

Building From Source
~~~~~~~~~~~~~~~~~~~~

`Download <http://pypi.python.org/pypi/improb/#downloads>`_ and extract the source ``.zip``. On Windows, start the command line, and run the setup script from within the extracted folder::

    cd ....\improb-x.x.x
    C:\PythonXX\python.exe setup.py install

On Linux, start a terminal and run::

    cd ..../improb-x.x.x
    python setup.py build
    su -c 'python setup.py install'

Building From Git
~~~~~~~~~~~~~~~~~

To install the *latest* code, clone it with `Git <http://git-scm.com>`_ by running::

    git clone git://github.com/mcmtroffaes/improb

You can also browse the source code on GitHub: `mcmtroffaes/improb <http://github.com/mcmtroffaes/improb>`_.

Then simply run the :file:`build.sh` script: this will build the library, install it, generate the documentation, and run all the doctests. Note that you need `Sphinx <http://sphinx.pocoo.org/>`_ to generate the documentation and to run the doctests.
