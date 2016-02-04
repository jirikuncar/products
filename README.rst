==========
 Products
==========

Simple product database with prices per retailer.


Installation
============

Create a virtual environment and install requirements for
``requirements.txt``.

.. code-block:: console

   $ mkvirtualenv products
   (products)$ pip install -r requirements.txt


Quick Start
===========

There is a simple init command.

.. code-block:: console

   (products)$ flask -a products.py init
   (products)$ flask -a products.py run

Now simple open your browser on http://localhost:5000/?retailer=Coop.
