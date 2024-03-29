#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import os
import random
import sys
import unittest

from six import StringIO

from mock import MagicMock as Mock
from mock import patch

import pyos
import pyos.utils as utils
import pyos.exceptions as exc
from pyos import base_identity

from pyos import fakes


class DummyResponse(object):
    def read(self):
        pass

    def readline(self):
        pass


class IdentityTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(IdentityTest, self).__init__(*args, **kwargs)
        self.username = "TESTUSER"
        self.password = "TESTPASSWORD"
        self.base_identity_class = base_identity.BaseIdentity
        self.identity_class = pyos.identity.KeystoneIdentity

    def _get_clean_identity(self):
        return self.identity_class()

    def setUp(self):
        self.identity = fakes.FakeIdentity()
        self.service = fakes.FakeIdentityService(self.identity)

    def tearDown(self):
        pass

    def test_svc_repr(self):
        svc = self.service
        rep = svc.__repr__()
        self.assertTrue(svc.service_type in rep)

    def test_svc_ep_for_region(self):
        svc = self.service
        region = utils.random_unicode().upper()
        bad_region = utils.random_unicode().upper()
        good_url = utils.random_unicode()
        bad_url = utils.random_unicode()
        good_ep = fakes.FakeEndpoint({"public_url": good_url}, svc.service_type,
                region, self.identity)
        bad_ep = fakes.FakeEndpoint({"public_url": bad_url}, svc.service_type,
                bad_region, self.identity)
        svc.endpoints = utils.DotDict({region: good_ep, bad_region: bad_ep})
        ep = svc._ep_for_region(region)
        self.assertEqual(ep, good_ep)

    def test_svc_ep_for_region_all(self):
        svc = self.service
        region = "ALL"
        good_url = utils.random_unicode()
        bad_url = utils.random_unicode()
        good_ep = fakes.FakeEndpoint({"public_url": good_url}, svc.service_type,
                region, self.identity)
        bad_ep = fakes.FakeEndpoint({"public_url": bad_url}, svc.service_type,
                region, self.identity)
        svc.endpoints = utils.DotDict({region: good_ep, "other": bad_ep})
        ep = svc._ep_for_region("notthere")
        self.assertEqual(ep, good_ep)

    def test_svc_ep_for_region_not_found(self):
        svc = self.service
        region = utils.random_unicode().upper()
        good_url = utils.random_unicode()
        bad_url = utils.random_unicode()
        good_ep = fakes.FakeEndpoint({"public_url": good_url}, svc.service_type,
                region, self.identity)
        bad_ep = fakes.FakeEndpoint({"public_url": bad_url}, svc.service_type,
                region, self.identity)
        svc.endpoints = utils.DotDict({region: good_ep, "other": bad_ep})
        ep = svc._ep_for_region("notthere")
        self.assertIsNone(ep)

    def test_svc_get_client(self):
        svc = self.service
        clt = utils.random_unicode()
        region = utils.random_unicode()

        class FakeEPForRegion(object):
            client = clt

        svc._ep_for_region = Mock(return_value=FakeEPForRegion())
        ret = svc.get_client(region)
        self.assertEqual(ret, clt)

    def test_svc_get_client_none(self):
        svc = self.service
        region = utils.random_unicode()
        svc._ep_for_region = Mock(return_value=None)
        self.assertRaises(exc.NoEndpointForRegion, svc.get_client, region)

    def test_svc_regions(self):
        svc = self.service
        key1 = utils.random_unicode()
        val1 = utils.random_unicode()
        key2 = utils.random_unicode()
        val2 = utils.random_unicode()
        svc.endpoints = {key1: val1, key2: val2}
        regions = svc.regions
        self.assertEqual(len(regions), 2)
        self.assertTrue(key1 in regions)
        self.assertTrue(key2 in regions)

    def test_ep_get_client_already_failed(self):
        svc = self.service
        ep_dict = {"publicURL": "http://example.com", "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ep._client = exc.NoClientForService()
        self.assertRaises(exc.NoClientForService, ep._get_client)

    def test_ep_get_client_exists(self):
        svc = self.service
        ep_dict = {"publicURL": "http://example.com", "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        clt = utils.random_unicode()
        ep._client = clt
        ret = ep._get_client()
        self.assertEqual(ret, clt)

    def test_ep_get_client_none(self):
        svc = self.service
        ep_dict = {"publicURL": "http://example.com", "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        sav = pyos.client_class_for_service
        pyos.client_class_for_service = Mock(return_value=None)
        self.assertRaises(exc.NoClientForService, ep._get_client)
        pyos.client_class_for_service = sav

    def test_ep_get_client_no_url(self):
        svc = self.service
        ep_dict = {"publicURL": "http://example.com", "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        sav = pyos.client_class_for_service
        ep.public_url = None
        pyos.client_class_for_service = Mock(return_value=object)
        self.assertRaises(exc.NoEndpointForService, ep._get_client)
        pyos.client_class_for_service = sav

    def test_ep_get_client(self):
        svc = self.service
        ep_dict = {"publicURL": "http://example.com", "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        sav = pyos.client_class_for_service
        ep.public_url = utils.random_unicode()
        pyos.client_class_for_service = Mock(return_value=object)
        fake = utils.random_unicode()
        ep._create_client = Mock(return_value=fake)
        ret = ep._get_client()
        self.assertEqual(ret, fake)
        self.assertEqual(ep._client, fake)
        pyos.client_class_for_service = sav

    def test_ep_get_new_client(self):
        svc = self.service
        ep_dict = {"publicURL": "http://example.com", "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ep._get_client = Mock()
        ep.get_new_client()
        ep._get_client.assert_called_once_with(public=True, cached=False)

    def test_ep_get(self):
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ret = ep.get("public")
        self.assertEqual(ret, pub)
        ret = ep.get("private")
        self.assertEqual(ret, priv)
        self.assertRaises(ValueError, ep.get, "invalid")

    def test_ep_getattr(self):
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        svc_att = "exists"
        att_val = utils.random_unicode()
        setattr(svc, svc_att, att_val)
        ep._get_client = Mock(return_value=svc)
        ret = ep.exists
        self.assertEqual(ret, att_val)
        self.assertRaises(AttributeError, getattr, ep, "bogus")

    def test_ep_client_prop(self):
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        clt = utils.random_unicode()
        ep._get_client = Mock(return_value=clt)
        ret = ep.client
        self.assertEqual(ret, clt)

    def test_ep_client_private_prop(self):
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        clt = utils.random_unicode()
        ep._get_client = Mock(return_value=clt)
        ret = ep.client_private
        self.assertEqual(ret, clt)

    def test_ep_create_client_compute(self):
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        vssl = random.choice((True, False))
        public = random.choice((True, False))
        sav_gs = pyos.get_setting
        pyos.get_setting = Mock(return_value=vssl)
        sav_conn = pyos.connect_to_cloudservers
        fake_client = fakes.FakeClient()
        fake_client.identity = self.identity
        pyos.connect_to_cloudservers = Mock(return_value=fake_client)
        ep.service = "compute"
        ret = ep._create_client(None, None, public)
        self.assertEqual(ret, fake_client)
        pyos.connect_to_cloudservers.assert_called_once_with(region=ep.region,
                context=ep.identity)
        pyos.connect_to_cloudservers = sav_conn
        pyos.get_setting = sav_gs

    def test_ep_create_client_all_other(self):
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = utils.random_unicode().upper()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        vssl = random.choice((True, False))
        public = random.choice((True, False))
        url = utils.random_unicode()
        sav_gs = pyos.get_setting
        pyos.get_setting = Mock(return_value=vssl)

        class FakeClientClass(object):
            def __init__(self, identity, region_name, management_url,
                    verify_ssl):
                self.identity = identity
                self.region_name = region_name
                self.management_url = management_url
                self.verify_ssl = verify_ssl

        ret = ep._create_client(FakeClientClass, url, public)
        self.assertTrue(isinstance(ret, FakeClientClass))
        pyos.get_setting = sav_gs

    def test_init(self):
        ident = self.identity_class(
            username=self.username, password=self.password)
        self.assertEqual(ident.username, self.username)
        self.assertEqual(ident.password, self.password)
        self.assertIsNone(ident.token)
        self.assertIsNone(ident._creds_file)

    def test_auth_with_token_name(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            nm = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            # Need to stuff this into the standard response
            sav = resp.content["access"]["user"]["name"]
            resp.content["access"]["user"]["name"] = nm
            ident.method_post = Mock(return_value=(resp, resp.json()))
            ident.auth_with_token(tok, tenant_name=nm)
            ident.method_post.assert_called_once_with("tokens",
                    headers={'Content-Type': 'application/json', 'Accept':
                    'application/json'}, std_headers=False, data={'auth':
                    {'token': {'id': tok}, 'tenantName': nm}})
            self.assertEqual(ident.username, nm)
            resp.content["access"]["user"]["name"] = sav

    def test_auth_with_token_id(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            # Need to stuff this into the standard response
            sav = resp.content["access"]["token"]["tenant"]["id"]
            resp.content["access"]["token"]["tenant"]["id"] = tenant_id
            ident.method_post = Mock(return_value=(resp, resp.json()))
            ident.auth_with_token(tok, tenant_id=tenant_id)
            ident.method_post.assert_called_once_with("tokens",
                    headers={'Content-Type': 'application/json', 'Accept':
                    'application/json'}, std_headers=False, data={'auth':
                    {'token': {'id': tok}, 'tenantId': tenant_id}})
            self.assertEqual(ident.tenant_id, tenant_id)
            resp.content["access"]["token"]["tenant"]["id"] = sav

    def test_auth_with_token_without_tenant_id(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = None
            resp = fakes.FakeIdentityResponse()
            # Need to stuff this into the standard response
            sav = resp.content["access"]["token"]["tenant"]["id"]
            resp.content["access"]["token"]["tenant"]["id"] = tenant_id
            ident.method_post = Mock(return_value=(resp, resp.json()))
            ident.auth_with_token(tok, tenant_id=tenant_id)
            ident.method_post.assert_called_once_with("tokens",
                    headers={'Content-Type': 'application/json', 'Accept':
                    'application/json'}, std_headers=False, data={'auth':
                    {'token': {'id': tok}}})
            self.assertEqual(ident.tenant_id, tenant_id)
            resp.content["access"]["token"]["tenant"]["id"] = sav

    def test_auth_with_token_id_auth_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            resp.status_code = 401
            ident.method_post = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthenticationFailed, ident.auth_with_token,
                    tok, tenant_id=tenant_id)

    def test_auth_with_token_id_auth_fail_general(self):
        for cls in self.id_classes.values():
            ident = cls()
            tok = utils.random_unicode()
            tenant_id = utils.random_unicode()
            resp = fakes.FakeIdentityResponse()
            resp.status_code = 499
            resp.reason = "fake"
            resp.json = Mock(return_value={"error": {"message": "fake"}})
            ident.method_post = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthenticationFailed, ident.auth_with_token,
                    tok, tenant_id=tenant_id)

    def test_get_client(self):
        ident = self.identity
        ident.authenticated = True
        svc = "fake"
        region = utils.random_unicode()
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        clt = fakes.FakeClient()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ep._get_client = Mock(return_value=clt)
        ident.services[svc].endpoints = {region: ep}
        ret = ident.get_client(svc, region)
        self.assertEqual(ret, clt)

    def test_get_client_unauthenticated(self):
        ident = self.identity
        ident.authenticated = False
        svc = "fake"
        region = utils.random_unicode()
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        clt = fakes.FakeClient()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ep._get_client = Mock(return_value=clt)
        ident.services[svc].endpoints = {region: ep}
        self.assertRaises(exc.NotAuthenticated, ident.get_client, svc, region)

    def test_get_client_private(self):
        ident = self.identity
        ident.authenticated = True
        svc = "fake"
        region = utils.random_unicode()
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        clt = fakes.FakeClient()
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ep._get_client = Mock(return_value=clt)
        ident.services[svc].endpoints = {region: ep}
        ret = ident.get_client(svc, region, public=False)
        self.assertEqual(ret, clt)
        ep._get_client.assert_called_once_with(cached=True, public=False,
                client_class=None)

    @patch("pyos.client_class_for_service")
    def test_get_client_no_cache(self, mock_ccfs):
        ident = self.identity
        ident.authenticated = True
        svc = "fake"
        region = utils.random_unicode()
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        clt_class = fakes.FakeClient
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        mock_ccfs.return_value = clt_class
        ident.services[svc].endpoints = {region: ep}
        ret = ident.get_client(svc, region, cached=False)
        self.assertTrue(isinstance(ret, clt_class))
        mock_ccfs.assert_called_once_with(svc)

    def test_get_client_no_client(self):
        ident = self.identity
        ident.authenticated = True
        svc = "fake"
        region = utils.random_unicode()
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        ep._get_client = Mock(return_value=None)
        ident.services[svc].endpoints = {region: ep}
        self.assertRaises(exc.NoSuchClient, ident.get_client, svc, region)

    def test_set_credentials(self):
        for cls in self.id_classes.values():
            ident = cls()
            ident.authenticate = Mock()
            ident.set_credentials(self.username, self.password,
                    authenticate=True)
            self.assertEqual(ident.username, self.username)
            self.assertEqual(ident.password, self.password)
            self.assertIsNone(ident.token)
            self.assertIsNone(ident._creds_file)
            ident.authenticate.assert_called_once_with()

    def test_set_credential_file(self):
        ident = self.identity_class()
        user = "fakeuser"
        # Use percent signs in key to ensure it doesn't get interpolated.
        key = "fake%api%key"
        ident.authenticate = Mock()
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\n")
                ff.write("username = %s\n" % user)
                ff.write("api_key = %s\n" % key)
            ident.set_credential_file(tmpname, authenticate=True)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.password, key)
        # Using 'password' instead of 'api_key'
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\n")
                ff.write("username = %s\n" % user)
                ff.write("password = %s\n" % key)
            ident.set_credential_file(tmpname)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.password, key)
        # File doesn't exist
        self.assertRaises(exc.FileNotFound, ident.set_credential_file,
                "doesn't exist")
        # Missing section
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("user = x\n")
            self.assertRaises(exc.InvalidCredentialFile,
                    ident.set_credential_file, tmpname)
        # Incorrect section
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[bad_section]\nusername = x\napi_key = y\n")
            self.assertRaises(exc.InvalidCredentialFile,
                    ident.set_credential_file, tmpname)
        # Incorrect option
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as ff:
                ff.write("[rackspace_cloud]\nuserbad = x\napi_key = y\n")
            self.assertRaises(exc.InvalidCredentialFile,
                    ident.set_credential_file, tmpname)

    def test_set_credential_file_keystone(self):
        ident = pyos.identity.KeystoneIdentity(
                username=self.username,
                password=self.password)
        user = "fakeuser"
        password = "fakeapikey"
        tenant_id = "faketenantid"
        with utils.SelfDeletingTempfile() as tmpname:
            with file(tmpname, "wb") as ff:
                ff.write("[keystone]\n")
                ff.write("username = %s\n" % user)
                ff.write("password = %s\n" % password)
                ff.write("tenant_id = %s\n" % tenant_id)
            ident.set_credential_file(tmpname)
        self.assertEqual(ident.username, user)
        self.assertEqual(ident.password, password)

    def test_keyring_auth_no_keyring(self):
        ident = self.identity
        sav = pyos.base_identity.keyring
        pyos.base_identity.keyring = None
        self.assertRaises(exc.KeyringModuleNotInstalled, ident.keyring_auth)
        pyos.base_identity.keyring = sav

    def test_keyring_auth_no_username(self):
        ident = self.identity
        sav = pyos.get_setting
        pyos.get_setting = Mock(return_value=None)
        self.assertRaises(exc.KeyringUsernameMissing, ident.keyring_auth)
        pyos.get_setting = sav

    def test_keyring_auth_no_password(self):
        ident = self.identity
        sav = pyos.base_identity.keyring.get_password
        pyos.base_identity.keyring.get_password = Mock(return_value=None)
        self.assertRaises(exc.KeyringPasswordNotFound, ident.keyring_auth,
                "fake")
        pyos.base_identity.keyring.get_password = sav

    def test_keyring_auth_apikey(self):
        ident = self.identity
        ident.authenticate = Mock()
        sav = pyos.base_identity.keyring.get_password
        pw = utils.random_unicode()
        pyos.base_identity.keyring.get_password = Mock(return_value=pw)
        user = utils.random_unicode()
        ident._creds_style = "apikey"
        ident.keyring_auth(username=user)
        ident.authenticate.assert_called_once_with(username=user, api_key=pw)
        pyos.base_identity.keyring.get_password = sav

    def test_keyring_auth_password(self):
        ident = self.identity
        ident.authenticate = Mock()
        sav = pyos.base_identity.keyring.get_password
        pw = utils.random_unicode()
        pyos.base_identity.keyring.get_password = Mock(return_value=pw)
        user = utils.random_unicode()
        ident._creds_style = "password"
        ident.keyring_auth(username=user)
        ident.authenticate.assert_called_once_with(username=user, password=pw)
        pyos.base_identity.keyring.get_password = sav

    def test_get_extensions(self):
        ident = self.identity
        v1 = utils.random_unicode()
        v2 = utils.random_unicode()
        resp_body = {"extensions": {"values": [v1, v2]}}
        ident.method_get = Mock(return_value=(None, resp_body))
        ret = ident.get_extensions()
        self.assertEqual(ret, [v1, v2])

    def test_get_credentials_keystone(self):
        ident = self.identity_class(username=self.username,
                password=self.password)
        creds = ident._format_credentials()
        user = creds["auth"]["passwordCredentials"]["username"]
        key = creds["auth"]["passwordCredentials"]["password"]
        self.assertEqual(self.username, user)
        self.assertEqual(self.password, key)

    def test_authenticate(self):
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_body = fakes.fake_identity_response
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        ident = self.identity_class()
        utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
        ident.authenticate()
        pyos.http.request = savrequest

    def test_authenticate_fail_creds(self):
        ident = self.identity_class(username="BAD", password="BAD")
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 401
        fake_body = fakes.fake_identity_response
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        self.assertRaises(exc.AuthenticationFailed, ident.authenticate)
        pyos.http.request = savrequest

    def test_authenticate_fail_other(self):
        ident = self.identity_class(username="BAD", password="BAD")
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 500
        fake_body = {u'unauthorized': {
                u'message': u'Username or api key is invalid', u'code': 500}}
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        self.assertRaises(exc.InternalServerError, ident.authenticate)
        pyos.http.request = savrequest

    def test_authenticate_fail_no_message(self):
        ident = self.identity_class(username="BAD", password="BAD")
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 500
        fake_body = {u'unauthorized': {
                u'bogus': u'Username or api key is invalid', u'code': 500}}
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        self.assertRaises(exc.InternalServerError, ident.authenticate)
        pyos.http.request = savrequest

    def test_authenticate_fail_gt_299(self):
        ident = self.identity_class(username="BAD", password="BAD")
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 444
        fake_body = {u'unauthorized': {
                u'message': u'Username or api key is invalid', u'code': 500}}
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        self.assertRaises(exc.AuthenticationFailed, ident.authenticate)
        pyos.http.request = savrequest

    def test_authenticate_fail_gt_299ino_message(self):
        ident = self.identity_class(username="BAD", password="BAD")
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_resp.status_code = 444
        fake_body = {u'unauthorized': {
                u'bogus': u'Username or api key is invalid', u'code': 500}}
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        self.assertRaises(exc.AuthenticationFailed, ident.authenticate)
        pyos.http.request = savrequest

    def test_authenticate_backwards_compatibility_connect_param(self):
        savrequest = pyos.http.request
        fake_resp = fakes.FakeIdentityResponse()
        fake_body = fakes.fake_identity_response
        pyos.http.request = Mock(return_value=(fake_resp, fake_body))
        ident = self.identity_class()
        # Necessary for testing to avoid NotImplementedError.
        utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
        ident.authenticate(connect=False)
        pyos.http.request = savrequest

    def test_auth_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            test_token = utils.random_unicode()
            ident.token = test_token
            self.assertEqual(ident.auth_token, test_token)

    def test_auth_endpoint(self):
        for cls in self.id_classes.values():
            ident = cls()
            test_ep = utils.random_unicode()
            ident._get_auth_endpoint = Mock(return_value=test_ep)
            self.assertEqual(ident.auth_endpoint, test_ep)

    def test_set_auth_endpoint(self):
        for cls in self.id_classes.values():
            ident = cls()
            test_ep = utils.random_unicode()
            ident.auth_endpoint = test_ep
            self.assertEqual(ident._auth_endpoint, test_ep)

    def test_regions(self):
        ident = self.base_identity_class()
        fake_resp = fakes.FakeIdentityResponse()
        ident._parse_response(fake_resp.json())
        expected = ("DFW", "ORD", "SYD", "FAKE")
        self.assertEqual(len(ident.regions), len(expected))
        for rgn in expected:
            self.assertTrue(rgn in ident.regions)

    def test_getattr_service(self):
        ident = self.base_identity_class()
        ident.authenticated = True
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        self.service.endpoints = {rgn: ep}
        ident.services = {"fake": self.service}
        ret = ident.fake
        self.assertEqual(ret, self.service.endpoints)

    def test_getattr_region(self):
        ident = self.base_identity_class()
        ident.authenticated = True
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        self.service.endpoints = {rgn: ep}
        ident.services = {"fake": self.service}
        ret = ident.FOO
        self.assertEqual(ret, {"fake": ep})

    def test_getattr_fail(self):
        ident = self.base_identity_class()
        ident.authenticated = True
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        self.service.endpoints = {rgn: ep}
        ident.services = {"fake": self.service}
        self.assertRaises(AttributeError, getattr, ident, "BAR")

    def test_getattr_not_authed(self):
        ident = self.base_identity_class()
        ident.authenticated = False
        svc = self.service
        pub = utils.random_unicode()
        priv = utils.random_unicode()
        ep_dict = {"publicURL": pub, "privateURL": priv, "tenantId": "aa"}
        rgn = "FOO"
        ep = fakes.FakeEndpoint(ep_dict, svc, rgn, self.identity)
        self.service.endpoints = {rgn: ep}
        ident.services = {"fake": self.service}
        self.assertRaises(exc.NotAuthenticated, getattr, ident, "BAR")

    def test_http_methods(self):
        ident = self.base_identity_class()
        ident._call = Mock()
        uri = utils.random_unicode()
        dkv = utils.random_unicode()
        data = {dkv: dkv}
        hkv = utils.random_unicode()
        headers = {hkv: hkv}
        std_headers = True
        ident.method_get(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with("GET", uri, False, data, headers,
                std_headers)
        ident.method_head(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with("HEAD", uri, False, data, headers,
                std_headers)
        ident.method_post(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with("POST", uri, False, data, headers,
                std_headers)
        ident.method_put(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with("PUT", uri, False, data, headers,
                std_headers)
        ident.method_delete(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with("DELETE", uri, False, data,
                headers, std_headers)
        ident.method_patch(uri, admin=False, data=data, headers=headers,
                std_headers=std_headers)
        ident._call.assert_called_with("PATCH", uri, False, data,
                headers, std_headers)

    def test_call(self):
        ident = self.base_identity_class()
        sav_req = pyos.http.request
        pyos.http.request = Mock()
        sav_debug = ident.http_log_debug
        ident.http_log_debug = True
        uri = "https://%s/%s" % (utils.random_ascii(), utils.random_ascii())
        sav_stdout = sys.stdout
        out = StringIO()
        sys.stdout = out
        utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
        dkv = utils.random_ascii()
        data = {dkv: dkv}
        hkv = utils.random_ascii()
        headers = {hkv: hkv}
        for std_headers in (True, False):
            expected_headers = ident._standard_headers() if std_headers else {}
            expected_headers.update(headers)
            for admin in (True, False):
                ident.method_post(uri, data=data, headers=headers,
                        std_headers=std_headers, admin=admin)
                pyos.http.request.assert_called_with("POST", uri, body=data,
                        headers=expected_headers)
                self.assertEqual(out.getvalue(), "")
                out.seek(0)
                out.truncate()
        out.close()
        pyos.http.request = sav_req
        ident.http_log_debug = sav_debug
        sys.stdout = sav_stdout

    def test_call_without_slash(self):
        ident = self.base_identity_class()
        ident._get_auth_endpoint = Mock()
        ident._get_auth_endpoint.return_value = "http://example.com/v2.0"
        ident.verify_ssl = False
        pyos.http.request = Mock()
        ident._call("POST", "tokens", False, {}, {}, False)
        pyos.http.request.assert_called_with("POST",
                "http://example.com/v2.0/tokens", headers={},
                raise_exception=False)

    def test_call_with_slash(self):
        ident = self.base_identity_class()
        ident._get_auth_endpoint = Mock()
        ident._get_auth_endpoint.return_value = "http://example.com/v2.0/"
        ident.verify_ssl = False
        pyos.http.request = Mock()
        ident._call("POST", "tokens", False, {}, {}, False)
        pyos.http.request.assert_called_with("POST",
                "http://example.com/v2.0/tokens", headers={},
                raise_exception=False)

    def test_find_user_fail_base(self):
        ident = self.identity
        fake = utils.random_unicode()
        self.assertRaises(NotImplementedError, ident.find_user_by_name, fake)
        self.assertRaises(NotImplementedError, ident.find_user_by_email, fake)
        self.assertRaises(NotImplementedError, ident.find_user_by_id, fake)
        self.assertRaises(NotImplementedError, ident.get_user, fake)

    def test_get_keystone_endpoint(self):
        ident = self.identity_class()
        fake_ep = utils.random_unicode()
        sav_setting = pyos.get_setting
        pyos.get_setting = Mock(return_value=fake_ep)
        ep = ident._get_auth_endpoint()
        self.assertEqual(ep, fake_ep)
        pyos.get_setting = sav_setting

    def test_get_keystone_endpoint_fail(self):
        ident = self.identity_class()
        sav_setting = pyos.get_setting
        pyos.get_setting = Mock(return_value=None)
        self.assertRaises(exc.EndpointNotDefined, ident._get_auth_endpoint)
        pyos.get_setting = sav_setting

    def test_get_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            ident.token = "test_token"
            sav_valid = ident._has_valid_token
            sav_auth = ident.authenticate
            ident._has_valid_token = Mock(return_value=True)
            ident.authenticate = Mock()
            tok = ident.get_token()
            self.assertEqual(tok, "test_token")
            # Force
            tok = ident.get_token(force=True)
            ident.authenticate.assert_called_with()
            # Invalid token
            ident._has_valid_token = Mock(return_value=False)
            ident.authenticated = False
            tok = ident.get_token()
            ident.authenticate.assert_called_with()
            ident._has_valid_token = sav_valid
            ident.authenticate = sav_auth

    def test_has_valid_token(self):
        savrequest = pyos.http.request
        pyos.http.request = Mock(return_value=(fakes.FakeIdentityResponse(),
                fakes.fake_identity_response))
        for cls in self.id_classes.values():
            ident = self.identity_class()
            # Necessary for testing to avoid NotImplementedError.
            utils.add_method(ident, lambda self: "", "_get_auth_endpoint")
            ident.authenticate()
            valid = ident._has_valid_token()
            self.assertTrue(valid)
            ident.expires = datetime.datetime.now() - datetime.timedelta(1)
            valid = ident._has_valid_token()
            self.assertFalse(valid)
            ident = self._get_clean_identity()
            valid = ident._has_valid_token()
            self.assertFalse(valid)
        pyos.http.request = savrequest

    def test_list_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            ident.method_get = Mock(return_value=(resp, resp.json()))
            tokens = ident.list_tokens()
            ident.method_get.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assertTrue("token" in tokens)

    def test_list_token_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 403
            ident.method_get = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthorizationFailure, ident.list_tokens)

    def test_check_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            ident.method_head = Mock(return_value=(resp, resp.json()))
            valid = ident.check_token()
            ident.method_head.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assertTrue(valid)

    def test_check_token_fail_auth(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 403
            ident.method_head = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthorizationFailure, ident.check_token)

    def test_check_token_fail_valid(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 404
            ident.method_head = Mock(return_value=(resp, resp.json()))
            valid = ident.check_token()
            ident.method_head.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assertFalse(valid)

    def test_revoke_token(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            token = ident.token = utils.random_unicode()
            ident.method_delete = Mock(return_value=(resp, resp.json()))
            valid = ident.revoke_token(token)
            ident.method_delete.assert_called_with("tokens/%s" % ident.token,
                    admin=True)
            self.assertTrue(valid)

    def test_revoke_token_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tokens"
            resp.status_code = 401
            token = ident.token = utils.random_unicode()
            ident.method_delete = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthorizationFailure, ident.revoke_token,
                    token)

    def test_get_token_endpoints(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "endpoints"
            ident.method_get = Mock(return_value=(resp, resp.json()))
            eps = ident.get_token_endpoints()
            self.assertTrue(isinstance(eps, list))
            ident.method_get.assert_called_with("tokens/%s/endpoints" %
                    ident.token, admin=True)

    def test_get_token_endpoints_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "endpoints"
            resp.status_code = 401
            ident.method_get = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthorizationFailure,
                    ident.get_token_endpoints)

    def test_get_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            ident.method_get = Mock(return_value=(resp, resp.json()))
            tenant = ident.get_tenant()
            self.assertTrue(isinstance(tenant, base_identity.Tenant))

    def test_get_tenant_none(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            ident._list_tenants = Mock(return_value=[])
            tenant = ident.get_tenant()
            self.assertIsNone(tenant)

    def test_list_tenants(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            ident.method_get = Mock(return_value=(resp, resp.json()))
            tenants = ident.list_tenants()
            self.assertTrue(isinstance(tenants, list))
            are_tenants = [isinstance(itm, base_identity.Tenant)
                    for itm in tenants]
            self.assertTrue(all(are_tenants))

    def test_list_tenants_auth_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            resp.status_code = 403
            ident.method_get = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.AuthorizationFailure, ident.list_tenants)

    def test_list_tenants_other_fail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenants"
            resp.status_code = 404
            ident.method_get = Mock(return_value=(resp, resp.json()))
            self.assertRaises(exc.TenantNotFound, ident.list_tenants)

    def test_create_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            ident.method_post = Mock(return_value=(resp, resp.json()))
            fake_name = utils.random_unicode()
            fake_desc = utils.random_unicode()
            tenant = ident.create_tenant(fake_name, description=fake_desc)
            self.assertTrue(isinstance(tenant, base_identity.Tenant))
            cargs = ident.method_post.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("tenants", ))
            data = cargs[1]["data"]["tenant"]
            self.assertEqual(data["name"], fake_name)
            self.assertEqual(data["description"], fake_desc)

    def test_update_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            ident.method_put = Mock(return_value=(resp, resp.json()))
            fake_id = utils.random_unicode()
            fake_name = utils.random_unicode()
            fake_desc = utils.random_unicode()
            tenant = ident.update_tenant(fake_id, name=fake_name,
                    description=fake_desc)
            self.assertTrue(isinstance(tenant, base_identity.Tenant))
            cargs = ident.method_put.call_args
            self.assertEqual(len(cargs), 2)
            self.assertEqual(cargs[0], ("tenants/%s" % fake_id, ))
            data = cargs[1]["data"]["tenant"]
            self.assertEqual(data["name"], fake_name)
            self.assertEqual(data["description"], fake_desc)

    def test_delete_tenant(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            ident.method_delete = Mock(return_value=(resp, resp.json()))
            fake_id = utils.random_unicode()
            ident.delete_tenant(fake_id)
            ident.method_delete.assert_called_with("tenants/%s" % fake_id)

    def test_delete_tenantfail(self):
        for cls in self.id_classes.values():
            ident = cls()
            resp = fakes.FakeIdentityResponse()
            resp.response_type = "tenant"
            resp.status_code = 404
            ident.method_delete = Mock(return_value=(resp, resp.json()))
            fake_id = utils.random_unicode()
            self.assertRaises(exc.TenantNotFound, ident.delete_tenant, fake_id)

    def test_list_roles(self):
        ident = self.identity
        nm = utils.random_unicode()
        id_ = utils.random_unicode()
        svcid = utils.random_unicode()
        limit = utils.random_unicode()
        marker = utils.random_unicode()
        resp = fakes.FakeResponse()
        resp_body = {"roles": [{"name": nm, "id": id_}]}
        ident.method_get = Mock(return_value=(resp, resp_body))
        exp_uri = "OS-KSADM/roles?serviceId=%s&limit=%s&marker=%s" % (svcid,
                limit, marker)
        ret = ident.list_roles(service_id=svcid, limit=limit, marker=marker)
        ident.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 1)
        role = ret[0]
        self.assertTrue(isinstance(role, base_identity.Role))

    def test_get_role(self):
        ident = self.identity
        role = utils.random_unicode()
        nm = utils.random_unicode()
        id_ = utils.random_unicode()
        resp = fakes.FakeResponse()
        resp_body = {"role": {"name": nm, "id": id_}}
        ident.method_get = Mock(return_value=(resp, resp_body))
        exp_uri = "OS-KSADM/roles/%s" % role
        ret = ident.get_role(role)
        ident.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, base_identity.Role))
        self.assertEqual(ret.name, nm)
        self.assertEqual(ret.id, id_)

    def test_add_role_to_user(self):
        ident = self.identity
        role = utils.random_unicode()
        user = utils.random_unicode()
        ident.method_put = Mock(return_value=(None, None))
        exp_uri = "users/%s/roles/OS-KSADM/%s" % (user, role)
        ident.add_role_to_user(role, user)
        ident.method_put.assert_called_once_with(exp_uri)

    def test_delete_role_from_user(self):
        ident = self.identity
        role = utils.random_unicode()
        user = utils.random_unicode()
        ident.method_delete = Mock(return_value=(None, None))
        exp_uri = "users/%s/roles/OS-KSADM/%s" % (user, role)
        ident.delete_role_from_user(role, user)
        ident.method_delete.assert_called_once_with(exp_uri)

    def test_parse_api_time_us(self):
        test_date = "2012-01-02T05:20:30.000-05:00"
        expected = datetime.datetime(2012, 1, 2, 10, 20, 30)
        for cls in self.id_classes.values():
            ident = cls()
            parsed = ident._parse_api_time(test_date)
            self.assertEqual(parsed, expected)

    def test_parse_api_time_uk(self):
        test_date = "2012-01-02T10:20:30.000Z"
        expected = datetime.datetime(2012, 1, 2, 10, 20, 30)
        for cls in self.id_classes.values():
            ident = cls()
            parsed = ident._parse_api_time(test_date)
            self.assertEqual(parsed, expected)


if __name__ == "__main__":
    unittest.main()
#    suite = unittest.TestLoader().loadTestsFromTestCase(IdentityTest)
#    unittest.TextTestRunner(verbosity=2).run(suite)
