User Interfaces
===============

``sqlformat``
  The ``sqlformat`` command line script ist distributed with the module.
  Run :command:`sqlformat --help` to list available options and for usage
  hints.
  It understands a ``--dialect`` (or ``--flavor``) option which selects the
  SQL dialect to be used.  Use ``-v``/``--verbose`` to increase output
  verbosity; each occurrence raises the level (``-vvv`` is level 3) and level
  1 shows where configuration options were loaded from.

``sqlformat.appspot.com``
  An example `Google App Engine <https://cloud.google.com/appengine/>`_
  application that exposes the formatting features using a web front-end.
  See https://sqlformat.org/ for details.
  The source for this application is available from a source code check out
  of the :mod:`sqlparse` module (see :file:`extras/appengine`).

