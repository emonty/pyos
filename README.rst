pyos
====

Python SDK for OpenStack Clouds

See the COPYING file for license and copyright information.

**pyos** is a should work with most OpenStack-based cloud deployments.
If your cloud provider has features that are not OpenStack features that
you want to use, then pyos is not for you. You should instead use an
SDK specific to that cloud provider ... just beware that you may be locking
yourself into their proprietary choices without meaning to.

pyos will go out of its way to hide the differences between legit deployment
choices that your cloud provider may have made. For instance, your cloud
provider may not use the floating-ip extension, but instead will just give
every instance you boot an IP. Awesome! It turns out that all you probably
wanted was an instance that could talk to the internet and you didn't care
one whit about floating-ips in the first place. We'll try to help with that.`

Getting Started with OpenStack
------------------------------

To sign up for a cloud account, go to

http://www.openstack.org/marketplace/public-clouds/

find one or more clouds that fits your needs, and go nuts.

If you are working with an OpenStack deployment, you can find more
information at http://www.openstack.org.

Requirements
------------

-  An OpenStack Cloud account

   -  username
   -  password

-  Python 2.7

   -  pyos is not yet tested yet with other Python versions. Please
      post feedback about what works or does not work with other
      versions.

Installation
------------

The best way to install **pyos** is by using
`pip <http://www.pip-installer.org/en/latest/>`__ to get the latest
official release:

::

    pip install pyos

If you would like to work with the current development state of pyos,
you can install directly from master on StackForge:

::

    pip install git://git.openstack.org/stackforge/pyos.git

If you are not using
`virtualenv <http://pypi.python.org/pypi/virtualenv>`__, you will need
to run ``pip install`` as admin using ``sudo``.

You may also download and install from source. The source code for
**pyos** is available on
`StackForge <https://git.openstack.org/cgit/stackforge/pyos`__.

Once you have the source code, ``cd`` to the base directory of the
source and run (using ``sudo``, if necessary):

::

    pip install .

Updates
-------

If you installed **pyos** using pip, it is simple to get the latest
updates:

::

    # PyPI
    pip install --upgrade pyos
    # GitHub
    pip install --upgrade git://git.openstack.org/stackforge/pyos.git

Contributing
------------

Please see the HACKING and CONTRIBUTING.rst files for contribution guidelines.
