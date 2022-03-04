# -*- coding: utf-8 -*-
import unittest

from alibabacloud_credentials.models import Config
from alibabacloud_credentials.utils import auth_constant
from alibabacloud_credentials.client import Client
from alibabacloud_credentials import credentials
from alibabacloud_credentials import providers


class TestClient(unittest.TestCase):
    def test_ak_client(self):
        conf = Config()
        conf.type = auth_constant.ACCESS_KEY
        conf.access_key_id = '123456'
        conf.access_key_secret = '654321'
        cred = Client(conf)
        self.assertEqual('123456', cred.get_access_key_id())
        self.assertEqual('654321', cred.get_access_key_secret())
        self.assertEqual(auth_constant.ACCESS_KEY, cred.get_type())
        self.assertIsNone(cred.get_security_token())
        try:
            cred = Client()
            cred.get_access_key_id()
        except Exception as e:
            self.assertEqual(e.message, 'not found credentials')

        conf = Config(type='sts')
        cred = Client(conf)
        self.assertIsInstance(cred.cloud_credential, credentials.StsCredential)

        conf = Config(type='bearer')
        cred = Client(conf)
        self.assertIsInstance(cred.cloud_credential, credentials.BearerTokenCredential)

        conf = Config(type='ecs_ram_role')
        self.assertIsInstance(Client.get_provider(conf), providers.EcsRamRoleCredentialProvider)

        conf = Config(type='ram_role_arn')
        self.assertIsInstance(Client.get_provider(conf), providers.RamRoleArnCredentialProvider)

        conf = Config(type='oidc_role_arn', oidc_token_file_path='oidc_token_file_path')
        self.assertIsInstance(Client.get_provider(conf), providers.OIDCRoleArnCredentialProvider)

        conf = Config(type='rsa_key_pair')
        self.assertIsInstance(Client.get_provider(conf), providers.RsaKeyPairCredentialProvider)

        conf = Config(type='test')
        self.assertIsInstance(Client.get_provider(conf), providers.DefaultCredentialsProvider)
