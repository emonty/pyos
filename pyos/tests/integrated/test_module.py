#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import unittest

import pyos


# This file needs to contain the actual credentials for a
# valid Rackspace Cloud account.
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")


class TestCase(unittest.TestCase):
    def setUp(self):
        pyos.set_credential_file(creds_file)

    def tearDown(self):
        pyos.clear_credentials()

    def test_cloudservers_images(self):
        imgs = pyos.cloudservers.images.list()
        self.assert_(isinstance(imgs, list))

    def test_cloudfiles_base_container(self):
        conts = pyos.cloudfiles.get_all_containers()
        self.assert_(isinstance(conts, list))

    def test_cloud_loadbalancers(self):
        lbs = pyos.cloud_loadbalancers.list()
        self.assert_(isinstance(lbs, list))

    def test_cloud_db(self):
        flavors = pyos.cloud_databases.list_flavors()
        self.assert_(isinstance(flavors, list))


if __name__ == "__main__":
    unittest.main()
