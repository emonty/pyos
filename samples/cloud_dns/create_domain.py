#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c)2012 Rackspace US, Inc.

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function

import os

import pyos
import pyos.exceptions as exc


pyos.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyos.set_credential_file(creds_file)
dns = pyos.cloud_dns

domain_name = "abc.example.edu"
try:
    dom = dns.create(name=domain_name, emailAddress="sample@example.edu",
            ttl=900, comment="sample domain")
except exc.DomainCreationFailed as e:
    print("Domain creation failed:", e)
print("Domain created:", dom)
