===================
CfbIO |TravisLink|_
===================

.. |TravisLink| image:: https://api.travis-ci.org/rembish/cfb.png
.. _TravisLink: https://travis-ci.org/rembish/cfb

CfbIO provides access to internal structure of Microsoft Compound File Binary
File Format.

Module operates with input file like standard IO module in Python. You can
seek, read and maybe one day write those files, like all other file-like
objects. Also module grants access to internal directory structure containing
Entries, which are also standard readable/seekable objects.

So, your work with this module is very simple::

    from cfb import CfbIO
    from cfb.directory.entry import SEEK_END

    doc = CfbIO("tests/data/simple.doc")

    root = doc.root
    print(root.read())  # Read whole root entry buffer

    some_entry = doc.directory[1].left
    some_entry.seek(100, whence=SEEK_END)
    print(some_entry.read(100))  # Read last 100 bytes from left sibling

All classes are lazy, so you can read really big files without memory leaks.
All data will be read only, when you will want it.
