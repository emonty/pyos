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

pyos.set_setting("identity_type", "rackspace")
creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyos.set_credential_file(creds_file)
clb = pyos.cloud_loadbalancers

try:
    lb = clb.list()[0]
except IndexError:
    print("You do not have any load balancers yet.")
    print("Please create one and then re-run this script.")
    sys.exit()

print("Load Balancer:", lb)
orig = lb.content_caching
print("Current setting of content caching:", orig)
print()
if orig:
    print("Turning off...")
else:
    print("Turning on...")
lb.content_caching = not orig
print("New setting of content caching:", lb.content_caching)
