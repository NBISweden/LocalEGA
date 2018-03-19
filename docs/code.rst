-------------------------
Source code documentation
-------------------------

.. automodule:: lega
   :members:
   :synopsis: The lega package contains code to start a *Local EGA*.

.. autosummary::

    lega.conf
    lega.utils
    lega.openpgp
    lega.keyserver
    lega.fs
    lega.ingest
    lega.vault
    lega.verify

*************
Configuration
*************

.. automodule:: lega.conf

*****************
Utility Functions
*****************

.. automodule:: lega.utils

.. autosummary::
    :toctree::

    lega.utils.amqp
    lega.utils.checksum
    lega.utils.crypto
    lega.utils.db
    lega.utils.eureka
    lega.utils.exceptions
    lega.utils.logging

*******
OpenPGP
*******

.. automodule:: lega.openpgp

.. autosummary::
    :toctree::

    lega.openpgp.constants
    lega.openpgp.generate
    lega.openpgp.iobuf
    lega.openpgp.packet
    lega.openpgp.utils

**********
FUSE layer
**********

.. automodule:: lega.fs

.. autoclass:: LegaFS

********************
Re-Encryption Worker
********************

.. automodule:: lega.ingest
   :members:

**********************************
Listener moving files to the Vault
**********************************

.. automodule:: lega.vault
   :members:

*************************
Verifying the vault files
*************************

.. automodule:: lega.verify
   :members:

*********
Keyserver
*********

.. automodule:: lega.keyserver

:ref:`genindex` | :ref:`modindex`
