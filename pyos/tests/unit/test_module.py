#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import unittest
import warnings

from six.moves import reload_module as reload

from mock import patch
from mock import MagicMock as Mock

import pyos
import pyos.exceptions as exc
import pyos.utils as utils
from pyos import fakes



class PyraxInitTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        reload(pyos)
        self.orig_connect_to_cloudservers = pyos.connect_to_cloudservers
        self.orig_connect_to_cloudfiles = pyos.connect_to_cloudfiles
        ctclb = pyos.connect_to_cloud_loadbalancers
        self.orig_connect_to_cloud_loadbalancers = ctclb
        self.orig_connect_to_cloud_databases = pyos.connect_to_cloud_databases
        self.orig_get_service_endpoint = pyos._get_service_endpoint
        super(PyraxInitTest, self).__init__(*args, **kwargs)
        self.username = "fakeuser"
        self.password = "fakeapikey"
        self.tenant_id = "faketenantid"

    def setUp(self):
        self.identity = fakes.FakeIdentity()
        vers = pyos.version.version
        pyos.settings._settings = {
                "default": {
                    "auth_endpoint": "DEFAULT_AUTH",
                    "region": "DFW",
                    "encoding": "utf-8",
                    "http_debug": False,
                    "keyring_username": "fakeuser",
                    "tenant_id": None,
                    "tenant_name": None,
                    "user_agent": "pyos/%s" % vers,
                    "use_servicenet": False,
                    "verify_ssl": False,
                },
                "alternate": {
                    "auth_endpoint": "ALT_AUTH",
                    "region": "NOWHERE",
                    "encoding": "utf-8",
                    "http_debug": False,
                    "keyring_username": "fakeuser",
                    "tenant_id": None,
                    "tenant_name": None,
                    "user_agent": "pyos/%s" % vers,
                    "use_servicenet": False,
                    "verify_ssl": False,
                }}
        pyos.identity = fakes.FakeIdentity()
        pyos.identity.authenticated = True
        pyos.connect_to_cloudservers = Mock()
        pyos.connect_to_cloudfiles = Mock()
        pyos.connect_to_cloud_loadbalancers = Mock()
        pyos.connect_to_cloud_databases = Mock()
        pyos._get_service_endpoint = Mock(return_value="http://example.com/")
        pyos.USER_AGENT = "DUMMY"

    def tearDown(self):
        pyos.settings._settings = {}
        pyos.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyos.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        octclb = self.orig_connect_to_cloud_loadbalancers
        pyos.connect_to_cloud_loadbalancers = octclb
        pyos.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyos._get_service_endpoint = self.orig_get_service_endpoint

    def test_require_auth(self):

        @pyos._require_auth
        def testfunc():
            pass

        pyos.identity.authenticated = True
        testfunc()
        pyos.identity.authenticated = False
        self.assertRaises(exc.NotAuthenticated, testfunc)

    def test_import_identity(self):
        sav = pyos.utils.import_class
        cls = utils.random_unicode()
        pyos.utils.import_class = Mock(return_value=cls)
        ret = pyos._import_identity(cls)
        self.assertEqual(ret, cls)
        pyos.utils.import_class = sav

    def test_import_identity_external(self):
        sav = pyos.utils.import_class
        cls = utils.random_unicode()

        def fake_import(nm):
            if "pyos.identity." in nm:
                raise ImportError()
            else:
                return nm

        pyos.utils.import_class = fake_import
        ret = pyos._import_identity(cls)
        self.assertEqual(ret, cls)
        pyos.utils.import_class = sav

    def test_create_context(self):
        sav = pyos._create_identity
        pyos._create_identity = Mock()
        id_type = utils.random_unicode()
        username = utils.random_unicode()
        password = utils.random_unicode()
        tenant_id = utils.random_unicode()
        tenant_name = utils.random_unicode()
        api_key = utils.random_unicode()
        verify_ssl = utils.random_unicode()
        pyos.create_context(id_type=id_type, username=username,
                password=password, tenant_id=tenant_id,
                tenant_name=tenant_name, api_key=api_key,
                verify_ssl=verify_ssl)
        pyos._create_identity.assert_called_once_with(id_type=id_type,
                username=username, password=password, tenant_id=tenant_id,
                tenant_name=tenant_name, api_key=api_key,
                verify_ssl=verify_ssl, return_context=True)
        pyos._create_identity = sav

    def test_settings_get(self):
        def_ep = pyos.get_setting("auth_endpoint", "default")
        alt_ep = pyos.get_setting("auth_endpoint", "alternate")
        self.assertEqual(def_ep, "DEFAULT_AUTH")
        self.assertEqual(alt_ep, "ALT_AUTH")

    def test_settings_get_from_env(self):
        pyos.settings._settings = {"default": {}}
        pyos.settings.env_dct = {"identity_type": "fake"}
        typ = utils.random_unicode()
        ident = utils.random_unicode()
        sav_env = os.environ
        sav_imp = pyos._import_identity
        pyos._import_identity = Mock(return_value=ident)
        os.environ = {"fake": typ}
        ret = pyos.get_setting("identity_class")
        pyos._import_identity = sav_imp
        os.environ = sav_env

    def test_settings_set_bad_env(self):
        key = utils.random_unicode()
        val = utils.random_unicode()
        self.assertRaises(exc.EnvironmentNotFound, pyos.settings.set, key,
                val, "bad_env")

    def test_settings_set_bad_key(self):
        key = utils.random_unicode()
        val = utils.random_unicode()
        self.assertRaises(exc.InvalidSetting, pyos.settings.set, key, val)

    def test_settings_set_region(self):
        key = "region"
        val = utils.random_unicode()
        pyos.settings.set(key, val)
        self.assertEqual(pyos.get_setting(key), val)

    def test_settings_set_region_no_identity(self):
        key = "region"
        val = utils.random_unicode()
        sav = pyos.identity
        pyos.identity = None
        ret = pyos.settings.set(key, val)
        self.assertIsNone(ret)
        pyos.identity = sav

    def test_settings_set_verify_ssl(self):
        key = "verify_ssl"
        val = utils.random_unicode()
        pyos.settings.set(key, val)
        self.assertEqual(pyos.get_setting(key), val)

    def test_settings_set_verify_ssl_no_identity(self):
        key = "verify_ssl"
        val = utils.random_unicode()
        sav = pyos.identity
        pyos.identity = None
        ret = pyos.settings.set(key, val)
        self.assertIsNone(ret)
        pyos.identity = sav

    def test_read_config(self):
        dummy_cfg = fakes.fake_config_file
        sav_region = pyos.default_region
        sav_USER_AGENT = pyos.USER_AGENT
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write(dummy_cfg)
            pyos.settings.read_config(cfgfile)
        self.assertEqual(pyos.get_setting("region"), "FAKE")
        self.assertTrue(pyos.get_setting("user_agent").startswith("FAKE "))
        pyos.default_region = sav_region
        pyos.USER_AGENT = sav_USER_AGENT

    def test_read_config_creds(self):
        dummy_cfg = fakes.fake_config_file
        sav_region = pyos.default_region
        sav_USER_AGENT = pyos.USER_AGENT
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write(dummy_cfg)
                # Add password entry
                cfg.write("password = fake\n")
            with warnings.catch_warnings(record=True) as warn:
                pyos.settings.read_config(cfgfile)
                self.assertEqual(len(warn), 1)
        pyos.default_region = sav_region
        pyos.USER_AGENT = sav_USER_AGENT

    def test_read_config_bad(self):
        sav_region = pyos.default_region
        dummy_cfg = fakes.fake_config_file
        # Test invalid setting
        dummy_cfg = dummy_cfg.replace("custom_user_agent", "fake")
        sav_USER_AGENT = pyos.USER_AGENT
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write(dummy_cfg)
            pyos.settings.read_config(cfgfile)
        self.assertEqual(pyos.USER_AGENT, sav_USER_AGENT)
        # Test bad file
        with utils.SelfDeletingTempfile() as cfgfile:
            with open(cfgfile, "w") as cfg:
                cfg.write("FAKE")
            self.assertRaises(exc.InvalidConfigurationFile,
                    pyos.settings.read_config, cfgfile)
        pyos.default_region = sav_region
        pyos.USER_AGENT = sav_USER_AGENT

    def test_set_credentials(self):
        pyos.set_credentials(self.username, self.password)
        self.assertEqual(pyos.identity.username, self.username)
        self.assertEqual(pyos.identity.password, self.password)
        self.assertTrue(pyos.identity.authenticated)

    def test_set_bad_credentials(self):
        self.assertRaises(exc.AuthenticationFailed, pyos.set_credentials,
                "bad", "creds")
        self.assertFalse(pyos.identity.authenticated)

    def test_set_credential_file(self):
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as tmp:
                tmp.write("[keystone]\n")
                tmp.write("username = %s\n" % self.username)
                tmp.write("password = %s\n" % self.password)
                tmp.write("tenant_id = %s\n" % self.tenant_id)
            pyos.set_credential_file(tmpname)
            self.assertEqual(pyos.identity.username, self.username)
            self.assertEqual(pyos.identity.password, self.password)
            self.assertTrue(pyos.identity.authenticated)

    def test_set_bad_credential_file(self):
        with utils.SelfDeletingTempfile() as tmpname:
            with open(tmpname, "wb") as tmp:
                tmp.write("[keystone]\n")
                tmp.write("username = bad\n")
                tmp.write("password = creds\n")
                tmp.write("tenant_id = stuff\n")
            self.assertRaises(exc.AuthenticationFailed,
                    pyos.set_credential_file, tmpname)
        self.assertFalse(pyos.identity.authenticated)

    def test_keyring_auth_no_module(self):
        pyos.keyring = None
        self.assertRaises(exc.KeyringModuleNotInstalled, pyos.keyring_auth)

    def test_keyring_auth_no_username(self):
        pyos.keyring = object()
        set_obj = pyos.settings
        env = set_obj.environment
        set_obj._settings[env]["keyring_username"] = ""
        self.assertRaises(exc.KeyringUsernameMissing, pyos.keyring_auth)

    def test_keyring_auth(self):
        class FakeKeyring(object):
            pass
        fake_keyring = FakeKeyring()
        pyos.keyring = fake_keyring
        fake_keyring.get_password = Mock(return_value="fakeapikey")
        pyos.keyring_username = "fakeuser"
        pyos.keyring_auth()
        self.assertTrue(pyos.identity.authenticated)

    def test_auth_with_token(self):
        pyos.authenticated = False
        tok = utils.random_unicode()
        tname = utils.random_unicode()
        pyos.auth_with_token(tok, tenant_name=tname)
        self.assertTrue(pyos.identity.authenticated)
        self.assertEqual(pyos.identity.token, tok)
        self.assertEqual(pyos.identity.tenant_name, tname)

    def test_clear_credentials(self):
        pyos.set_credentials(self.username, self.password)
        # These next lines are required to test that clear_credentials
        # actually resets them to None.
        pyos.cloudservers = object()
        pyos.cloudfiles = object()
        pyos.cloud_loadbalancers = object()
        pyos.cloud_databases = object()
        default_region = object()
        self.assertTrue(pyos.identity.authenticated)
        self.assertIsNotNone(pyos.cloudfiles)
        pyos.clear_credentials()
        self.assertIsNone(pyos.identity)
        self.assertIsNone(pyos.cloudservers)
        self.assertIsNone(pyos.cloudfiles)
        self.assertIsNone(pyos.cloud_loadbalancers)
        self.assertIsNone(pyos.cloud_databases)

    def test_get_environment(self):
        env = pyos.get_environment()
        all_envs = pyos.list_environments()
        self.assertTrue(env in all_envs)

    def test_set_environment(self):
        env = "alternate"
        sav = pyos.authenticate
        pyos.authenticate = Mock()
        pyos.set_environment(env)
        self.assertEqual(pyos.get_environment(), env)
        pyos.authenticate = sav

    def test_set_environment_fail(self):
        sav = pyos.authenticate
        pyos.authenticate = Mock()
        env = "doesn't exist"
        self.assertRaises(exc.EnvironmentNotFound, pyos.set_environment, env)
        pyos.authenticate = sav

    def test_set_default_region(self):
        orig_region = pyos.default_region
        new_region = "test"
        pyos.set_default_region(new_region)
        self.assertEqual(pyos.default_region, new_region)
        pyos.default_region = orig_region

    def test_set_region_setting(self):
        ident = pyos.identity
        ident.region = "DFW"
        pyos.set_setting("region", "ORD")
        self.assertEqual(ident.region, "DFW")
        pyos.set_setting("region", "LON")
        self.assertEqual(ident.region, "LON")

    def test_safe_region(self):
        # Pass direct
        reg = utils.random_unicode()
        ret = pyos._safe_region(reg)
        self.assertEqual(reg, ret)
        # From config setting
        orig_reg = pyos.get_setting("region")
        reg = utils.random_unicode()
        pyos.set_setting("region", reg)
        ret = pyos._safe_region()
        self.assertEqual(reg, ret)
        # Identity default
        pyos.set_setting("region", None)
        orig_defreg = pyos.identity.get_default_region
        reg = utils.random_unicode()
        pyos.identity.get_default_region = Mock(return_value=reg)
        ret = pyos._safe_region()
        self.assertEqual(reg, ret)
        pyos.identity.get_default_region = orig_defreg
        pyos.set_setting("region", orig_reg)

    def test_safe_region_no_context(self):
        reg = None
        sav_ident = pyos.identity
        sav_create = pyos._create_identity

        def set_ident():
            pyos.identity = sav_ident

        pyos._create_identity = Mock(side_effect=set_ident)
        sav_get = pyos.settings.get
        pyos.settings.get = Mock(return_value=None)
        pyos.identity = None
        ret = pyos._safe_region(reg)
        self.assertIsNotNone(ret)
        pyos._create_identity = sav_create
        pyos.identity = sav_ident
        pyos.settings.get = sav_get

    def test_make_agent_name(self):
        test_agent = "TEST"
        ret = pyos._make_agent_name(test_agent)
        self.assertTrue(ret.endswith(test_agent))
        self.assertTrue(ret.startswith(pyos.USER_AGENT))

    def test_connect_to_services(self):
        pyos.connect_to_services()
        pyos.connect_to_cloudservers.assert_called_once_with(region=None)
        pyos.connect_to_cloudfiles.assert_called_once_with(region=None)
        pyos.connect_to_cloud_loadbalancers.assert_called_once_with(
                region=None)
        pyos.connect_to_cloud_databases.assert_called_once_with(region=None)

    @patch('pyos._cs_client.Client', new=fakes.FakeCSClient)
    def test_connect_to_cloudservers(self):
        pyos.cloudservers = None
        sav = pyos.connect_to_cloudservers
        pyos.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyos.cloudservers = pyos.connect_to_cloudservers()
        self.assertIsNotNone(pyos.cloudservers)
        pyos.connect_to_cloudservers = sav

    @patch('pyos.StorageClient', new=fakes.FakeService)
    def test_connect_to_cloudfiles(self):
        pyos.cloudfiles = None
        pyos.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        pyos.cloudfiles = pyos.connect_to_cloudfiles(self.identity)
        self.assertIsNotNone(pyos.cloudfiles)

    def test_connect_to_cloudfiles_ServiceNet(self):
        orig = pyos.get_setting("use_servicenet")
        pyos.set_setting("use_servicenet", True)
        pyos.cloudfiles = None
        pyos.connect_to_cloudfiles = self.orig_connect_to_cloudfiles
        sav = pyos._create_client
        pyos._create_client = Mock()
        cf = pyos.connect_to_cloudfiles(public=False)
        pyos._create_client.assert_called_once_with(ep_name="object_store",
                region=None, public=False)
        pyos.set_setting("use_servicenet", orig)
        pyos._create_client = sav

    @patch('pyos.CloudLoadBalancerClient', new=fakes.FakeService)
    def test_connect_to_cloud_loadbalancers(self):
        pyos.cloud_loadbalancers = None
        octclb = self.orig_connect_to_cloud_loadbalancers
        pyos.connect_to_cloud_loadbalancers = octclb
        pyos.cloud_loadbalancers = pyos.connect_to_cloud_loadbalancers()
        self.assertIsNotNone(pyos.cloud_loadbalancers)

    @patch('pyos.CloudDatabaseClient', new=fakes.FakeService)
    def test_connect_to_cloud_databases(self):
        pyos.cloud_databases = None
        pyos.connect_to_cloud_databases = self.orig_connect_to_cloud_databases
        pyos.cloud_databases = pyos.connect_to_cloud_databases()
        self.assertIsNotNone(pyos.cloud_databases)

    def test_set_http_debug(self):
        pyos.cloudservers = None
        sav = pyos.connect_to_cloudservers
        pyos.connect_to_cloudservers = self.orig_connect_to_cloudservers
        pyos.cloudservers = pyos.connect_to_cloudservers()
        pyos.cloudservers.http_log_debug = False
        pyos.set_http_debug(True)
        self.assertTrue(pyos.cloudservers.http_log_debug)
        pyos.set_http_debug(False)
        self.assertFalse(pyos.cloudservers.http_log_debug)
        pyos.connect_to_cloudservers = sav

    def test_get_encoding(self):
        sav = pyos.get_setting
        pyos.get_setting = Mock(return_value=None)
        enc = pyos.get_encoding()
        self.assertEqual(enc, pyos.default_encoding)
        pyos.get_setting = sav

    def test_import_fail(self):
        import __builtin__
        sav_import = __builtin__.__import__

        def fake_import(nm, *args):
            if nm == "identity":
                raise ImportError
            else:
                return sav_import(nm, *args)

        __builtin__.__import__ = fake_import
        self.assertRaises(ImportError, reload, pyos)
        __builtin__.__import__ = sav_import
        reload(pyos)



if __name__ == "__main__":
    unittest.main()
