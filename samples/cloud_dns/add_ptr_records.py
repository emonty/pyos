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
import sys

import pyos
import pyos.exceptions as exc


pyos.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyos.set_credential_file(creds_file)
dns = pyos.cloud_dns
cs = pyos.cloudservers

# Substitute an actual server ID here
server_id = "00000000-0000-0000-0000-000000000000"
server = cs.servers.get(server_id)

# Substitute your actual domain name and IP addresses here
domain_name = "abc.example.edu"
ipv4_rec = {"name": domain_name,
        "type": "PTR",
        "data": "1.2.3.4",
        "ttl": 7200}
ipv6_rec = {"name": domain_name,
        "type": "PTR",
        "data": "2001:000::0",
        "ttl": 7200}

recs = dns.add_ptr_records(server, [ipv4_rec, ipv6_rec])
print(recs)
print()
