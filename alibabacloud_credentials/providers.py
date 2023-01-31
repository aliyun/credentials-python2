# -*- coding: utf-8 -*-
import json
import time
import calendar
import os

try:
    from ConfigParser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from Tea.vendored import requests
from Tea.core import TeaCore
from Tea.request import TeaRequest

from alibabacloud_credentials.utils import auth_util as au, \
    auth_constant as ac, \
    parameter_helper as ph
from alibabacloud_credentials.exceptions import CredentialException
from alibabacloud_credentials.models import Config
from alibabacloud_credentials import credentials


class AlibabaCloudCredentialsProvider(object):
    """BaseProvider class"""
    duration_seconds = 3600
    timeout = 2000
    region_id = 'cn-hangzhou'

    def __init__(self, config=None):
        if isinstance(config, Config):
            self.type = config.type
            self.access_key_id = config.access_key_id
            self.access_key_secret = config.access_key_secret
            self.role_arn = config.role_arn
            self.oidc_provider_arn = config.oidc_provider_arn
            self.oidc_token_file_path = config.oidc_token_file_path
            self.role_session_name = config.role_session_name
            self.public_key_id = config.public_key_id
            self.role_name = config.role_name
            self.oidc_provider_arn = config.oidc_provider_arn
            self.oidc_token_file_path = config.oidc_token_file_path
            self.private_key_file = config.private_key_file
            self.bearer_token = config.bearer_token
            self.security_token = config.security_token
            self.host = config.host
            self.timeout = config.timeout + config.connect_timeout
            self.connect_timeout = config.connect_timeout
            self.proxy = config.proxy

    def _set_arg(self, key, value):
        if value is not None:
            setattr(self, key, value)

        val = getattr(self, key, None)
        if val is None:
            setattr(self, key, None)

    def _verify_empty_args(self, config=None, *args):
        if None in args and config is None:
            raise CredentialException(
                '"%s" needs to receive a "model.Config" object or other necessary args' % self.__class__
            )

    def get_credentials(self):
        raise NotImplementedError('get_credentials() must be overridden')


class DefaultCredentialsProvider(AlibabaCloudCredentialsProvider):
    def __init__(self):
        super(DefaultCredentialsProvider, self).__init__()
        self.user_configuration_providers = [
            EnvironmentVariableCredentialsProvider()
        ]
        if au.enable_oidc_credential:
            self.user_configuration_providers.append(OIDCRoleArnCredentialProvider(
                role_session_name=au.environment_role_session_name,
                role_arn=au.environment_role_arn,
                oidc_provider_arn=au.environment_oidc_provider_arn,
                oidc_token_file_path=au.environment_oidc_token_file
            ))

        self.user_configuration_providers.append(ProfileCredentialsProvider())
        role_name = au.environment_ECSMeta_data
        if role_name is not None:
            self.user_configuration_providers.append(EcsRamRoleCredentialProvider(role_name))

    def get_credentials(self):
        for provider in self.user_configuration_providers:
            credential = provider.get_credentials()
            if credential is not None:
                return credential
        raise CredentialException("not found credentials")

    def add_credentials_provider(self, p):
        self.user_configuration_providers.append(p)

    def remove_credentials_provider(self, p):
        self.user_configuration_providers.remove(p)

    def contains_credentials_provider(self, p):
        return self.user_configuration_providers.__contains__(p)

    def clear_credentials_provider(self):
        self.user_configuration_providers = []


class EcsRamRoleCredentialProvider(AlibabaCloudCredentialsProvider):
    """EcsRamRoleCredentialProvider"""

    def __init__(self, role_name=None, config=None):
        self._verify_empty_args(config, role_name)
        super(EcsRamRoleCredentialProvider, self).__init__(config)
        self.__url_in_ecs_metadata = "/latest/meta-data/ram/security-credentials/"
        self.__ecs_metadata_fetch_error_msg = "Failed to get RAM session credentials from ECS metadata service."
        self.__metadata_service_host = "100.100.100.200"
        self._set_arg('role_name', role_name)
        self._set_credential_url()

    def _get_role_name(self, url=None):
        url = url if url else self.credential_url
        response = requests.get(url, timeout=self.timeout / 1000)
        if response.status_code != 200:
            raise CredentialException(self.__ecs_metadata_fetch_error_msg + " HttpCode=" + str(response.status_code))
        response.encoding = 'utf-8'
        self.role_name = response.text

    def _create_credential(self, url=None):
        tea_request = TeaRequest()
        tea_request.headers['host'] = url if url else self.credential_url
        # request
        response = TeaCore.do_action(tea_request)

        if response.status_code != 200:
            raise CredentialException(self.__ecs_metadata_fetch_error_msg + " HttpCode=" + str(response.status_code))

        dic = json.loads(response.body.decode('utf-8'))
        content_code = dic.get('Code')
        content_access_key_id = dic.get('AccessKeyId')
        content_access_key_secret = dic.get('AccessKeySecret')
        content_security_token = dic.get('SecurityToken')
        content_expiration = dic.get('Expiration')

        if content_code != "Success":
            raise CredentialException(self.__ecs_metadata_fetch_error_msg)

        # 先转换为时间数组
        time_array = time.strptime(content_expiration, "%Y-%m-%dT%H:%M:%SZ")
        # 转换为时间戳
        time_stamp = calendar.timegm(time_array)
        return credentials.EcsRamRoleCredential(content_access_key_id, content_access_key_secret,
                                                content_security_token, time_stamp, self)

    def get_credentials(self):
        if self.role_name == "":
            self._get_role_name()
            self._set_credential_url()
        return self._create_credential()

    def _set_credential_url(self):
        self.credential_url = "http://" + self.__metadata_service_host + self.__url_in_ecs_metadata + self.role_name


class RamRoleArnCredentialProvider(AlibabaCloudCredentialsProvider):
    """RamRoleArnCredentialProvider"""

    def __init__(self, access_key_id=None, access_key_secret=None, role_session_name=None, role_arn=None,
                 region_id=None,
                 policy=None, config=None):
        self._verify_empty_args(config, access_key_id, access_key_secret)
        super(RamRoleArnCredentialProvider, self).__init__(config)
        self._set_arg('role_arn', role_arn)
        self._set_arg('access_key_id', access_key_id)
        self._set_arg('access_key_secret', access_key_secret)
        self._set_arg('region_id', region_id)
        self._set_arg('role_session_name', role_session_name)
        self._set_arg('policy', policy)

    def get_credentials(self):
        return self._create_credentials()

    def _create_credentials(self, turl=None):
        # 获取credential 先实现签名用工具类
        tea_request = TeaRequest()
        tea_request.query = {
            'Action': 'AssumeRole',
            'Format': 'JSON',
            'Version': '2015-04-01',
            'DurationSeconds': str(self.duration_seconds),
            'RoleArn': self.role_arn,
            'AccessKeyId': self.access_key_id,
            'RegionId': self.region_id,
            'RoleSessionName': self.role_session_name,
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0'
        }
        tea_request.query["Timestamp"] = ph.get_iso_8061_date()
        tea_request.query["SignatureNonce"] = ph.get_uuid()
        if self.policy is not None:
            tea_request.query["Policy"] = self.policy
        string_to_sign = ph.compose_string_to_sign("GET", tea_request.query)
        signature = ph.sign_string(string_to_sign, self.access_key_secret + "&")
        tea_request.query["Signature"] = signature
        tea_request.protocol = 'https'
        tea_request.headers['host'] = turl if turl else 'sts.aliyuncs.com'
        # request
        response = TeaCore.do_action(tea_request)
        if response.status_code == 200:
            dic = json.loads(response.body.decode('utf-8'))
            if "Credentials" in dic:
                cre = dic.get("Credentials")
                # 先转换为时间数组
                time_array = time.strptime(cre.get("Expiration"), "%Y-%m-%dT%H:%M:%SZ")
                # 转换为时间戳
                expiration = calendar.timegm(time_array)
                return credentials.RamRoleArnCredential(cre.get("AccessKeyId"), cre.get("AccessKeySecret"),
                                                        cre.get("SecurityToken"), expiration, self)
        raise CredentialException(response.body.decode('utf-8'))


class OIDCRoleArnCredentialProvider(AlibabaCloudCredentialsProvider):
    """OIDCRoleArnCredentialProvider"""

    def __init__(self, access_key_id=None, access_key_secret=None, role_session_name=None, role_arn=None,
                 oidc_provider_arn=None,
                 oidc_token_file_path=None,
                 region_id=None,
                 policy=None, config=None):
        self._verify_empty_args(config, role_arn, oidc_provider_arn, oidc_token_file_path)
        super(OIDCRoleArnCredentialProvider, self).__init__(config)
        self._set_arg('role_arn', role_arn)
        self._set_arg('oidc_provider_arn', oidc_provider_arn)
        if oidc_token_file_path is not None:
            self._set_arg('oidc_token_file_path', oidc_token_file_path)
        elif config.oidc_token_file_path is not None:
            self._set_arg('oidc_token_file_path', oidc_token_file_path)
        elif au.environment_oidc_token_file is not None:
            self._set_arg('oidc_token_file_path', au.environment_oidc_token_file)
        else:
            raise CredentialException(
                'The oidc_token_file_path does not exist and env ALIBABA_CLOUD_OIDC_TOKEN_FILE is none.')
        self._set_arg('region_id', region_id)
        self._set_arg('role_session_name', role_session_name)
        self._set_arg('policy', policy)

    def get_credentials(self):
        return self._create_credentials()

    def _create_credentials(self, turl=None):
        # 获取credential 先实现签名用工具类
        oidc_token = au.get_private_key(self.oidc_token_file_path)
        tea_request = TeaRequest()
        tea_request.query = {
            'Action': 'AssumeRoleWithOIDC',
            'Format': 'JSON',
            'Version': '2015-04-01',
            'DurationSeconds': str(self.duration_seconds),
            'RoleArn': self.role_arn,
            'OIDCProviderArn': self.oidc_provider_arn,
            'OIDCToken': oidc_token,
            'RegionId': self.region_id,
            'RoleSessionName': self.role_session_name if self.role_session_name else 'defaultSessionName'
        }
        tea_request.query["Timestamp"] = ph.get_iso_8061_date()
        tea_request.query["SignatureNonce"] = ph.get_uuid()
        if self.policy is not None:
            tea_request.query["Policy"] = self.policy
        tea_request.protocol = 'https'
        tea_request.headers['host'] = turl if turl else 'sts.aliyuncs.com'
        # request
        response = TeaCore.do_action(tea_request)
        if response.status_code == 200:
            dic = json.loads(response.body.decode('utf-8'))
            if "Credentials" in dic:
                cre = dic.get("Credentials")
                # 先转换为时间数组
                time_array = time.strptime(cre.get("Expiration"), "%Y-%m-%dT%H:%M:%SZ")
                # 转换为时间戳
                expiration = calendar.timegm(time_array)
                return credentials.OIDCRoleArnCredential(cre.get("AccessKeyId"), cre.get("AccessKeySecret"),
                                                         cre.get("SecurityToken"), expiration, self)
        raise CredentialException(response.body.decode('utf-8'))


class RsaKeyPairCredentialProvider(AlibabaCloudCredentialsProvider):

    def __init__(self, access_key_id=None, access_key_secret=None, region_id=None, config=None):
        self._verify_empty_args(config, access_key_id, access_key_secret)
        super(RsaKeyPairCredentialProvider, self).__init__(config)
        self._set_arg('access_key_id', access_key_id)
        self._set_arg('access_key_secret', access_key_secret)
        self._set_arg('region_id', region_id)

    def get_credentials(self):
        return self._create_credential()

    def _create_credential(self, turl=None):
        tea_request = TeaRequest()
        tea_request.query = {
            'Action': 'GenerateSessionAccessKey',
            'Format': 'JSON',
            'Version': '2015-04-01',
            'DurationSeconds': str(self.duration_seconds),
            'AccessKeyId': self.access_key_id,
            'RegionId': self.region_id,
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0'
        }
        tea_request.query["Timestamp"] = ph.get_iso_8061_date()
        tea_request.query["SignatureNonce"] = ph.get_uuid()

        str_to_sign = ph.compose_string_to_sign('GET', tea_request.query)
        signature = ph.sign_string(str_to_sign, self.access_key_id + '&')
        tea_request.query['Signature'] = signature
        tea_request.protocol = 'https'
        tea_request.headers['host'] = turl if turl else 'sts.aliyuncs.com'
        # request
        response = TeaCore.do_action(tea_request)
        if response.status_code == 200:
            dic = json.loads(response.body.decode('utf-8'))
            if "SessionAccessKey" in dic:
                cre = dic.get("SessionAccessKey")
                time_array = time.strptime(cre.get("Expiration"), "%Y-%m-%dT%H:%M:%SZ")
                expiration = calendar.timegm(time_array)
                return credentials.RsaKeyPairCredential(cre.get("SessionAccessKeyId"),
                                                        cre.get("SessionAccessKeySecret"),
                                                        expiration, self)
        raise CredentialException(response.body.decode('utf-8'))


class ProfileCredentialsProvider(AlibabaCloudCredentialsProvider):
    def __init__(self, path=None):
        super(ProfileCredentialsProvider, self).__init__()
        self._set_arg('file_path', path)

    def get_credentials(self):
        file_path = self.file_path if self.file_path else au.environment_credentials_file
        if file_path is None:
            if not ac.HOME:
                return
            file_path = os.path.join(ac.HOME, "/.alibabacloud/credentials.ini")
        if len(file_path) == 0:
            raise CredentialException("The specified credentials file is empty")

        # loads ini
        conf = ConfigParser()
        conf.read(file_path)
        ini_map = dict(conf._sections)
        for k in dict(conf._sections):
            option = dict(ini_map[k])
            for key, value in dict(ini_map[k]).items():
                if '#' in value:
                    option[key] = value.split('#')[0].strip()
                else:
                    option[key] = value.strip()
            ini_map[k] = option
        client_config = ini_map.get(au.client_type)
        if client_config is None:
            return
        return self._create_credential(client_config)

    def _create_credential(self, config):
        config_type = config.get(ac.INI_TYPE)
        if not config_type:
            raise CredentialException("The configured client type is empty")
        elif ac.INI_TYPE_ARN == config_type:
            return self._get_sts_assume_role_session_credentials(config)
        elif ac.INI_TYPE_OIDC == config_type:
            return self._get_sts_oidc_role_session_provider(config).get_credentials()
        elif ac.INI_TYPE_KEY_PAIR == config_type:
            return self._get_sts_get_session_access_key_credentials(config)
        elif ac.INI_TYPE_RAM == config_type:
            return self._get_instance_profile_credentials(config)

        access_key_id = config.get(ac.INI_ACCESS_KEY_ID)
        access_key_secret = config.get(ac.INI_ACCESS_KEY_IDSECRET)
        if not access_key_id or not access_key_secret:
            return
        return credentials.AccessKeyCredential(access_key_id, access_key_secret)

    @staticmethod
    def _get_sts_assume_role_session_credentials(config):
        access_key_id = config.get(ac.INI_ACCESS_KEY_ID)
        access_key_secret = config.get(ac.INI_ACCESS_KEY_IDSECRET)
        role_session_name = config.get(ac.INI_ROLE_SESSION_NAME)
        role_arn = config.get(ac.INI_ROLE_ARN)
        region_id = config.get(ac.DEFAULT_REGION)
        policy = config.get(ac.INI_POLICY)

        if not access_key_id or not access_key_secret:
            raise CredentialException("The configured access_key_id or access_key_secret is empty")
        if not role_session_name or not role_arn:
            raise CredentialException("The configured role_session_name or role_arn is empty")
        provider = RamRoleArnCredentialProvider(
            access_key_id, access_key_secret, role_session_name, role_arn, region_id, policy
        )
        return provider.get_credentials()

    @staticmethod
    def _get_sts_oidc_role_session_provider(config):
        access_key_id = config.get(ac.INI_ACCESS_KEY_ID)
        access_key_secret = config.get(ac.INI_ACCESS_KEY_IDSECRET)
        role_session_name = config.get(ac.INI_ROLE_SESSION_NAME)
        role_arn = config.get(ac.INI_ROLE_ARN)
        oidc_provider_arn = config.get(ac.INI_OIDC_PROVIDER_ARN)
        oidc_token_file_path = config.get(ac.INI_OIDC_TOKEN_FILE_PATH)
        region_id = config.get(ac.DEFAULT_REGION)
        policy = config.get(ac.INI_POLICY)

        if not role_arn:
            raise CredentialException("The configured role_arn is empty")
        if not oidc_provider_arn:
            raise CredentialException("The configured oidc_provider_arn is empty")
        return OIDCRoleArnCredentialProvider(
            access_key_id, access_key_secret, role_session_name, role_arn, oidc_provider_arn, oidc_token_file_path, region_id, policy
        )

    @staticmethod
    def _get_sts_get_session_access_key_credentials(config):
        public_key_id = config.get(ac.INI_PUBLIC_KEY_ID)
        private_key_file = config.get(ac.INI_PRIVATE_KEY_FILE)
        if not private_key_file:
            raise CredentialException("The configured private_key_file is empty")
        private_key = au.get_private_key(private_key_file)
        if not public_key_id or not private_key:
            raise CredentialException("The configured public_key_id or private_key_file content is empty")

        provider = RsaKeyPairCredentialProvider(public_key_id, private_key)
        return provider.get_credentials()

    @staticmethod
    def _get_instance_profile_credentials(config):
        role_name = config.get(ac.INI_ROLE_NAME)
        if not role_name:
            raise CredentialException("The configured role_name is empty")
        provider = EcsRamRoleCredentialProvider(role_name)
        return provider.get_credentials()


class EnvironmentVariableCredentialsProvider(AlibabaCloudCredentialsProvider):
    def get_credentials(self):
        if 'default' != au.client_type:
            return
        access_key_id = au.environment_access_key_id
        access_key_secret = au.environment_access_key_secret
        if access_key_id is None or access_key_secret is None:
            return
        if len(access_key_id) == 0:
            raise CredentialException("Environment variable accessKeyId cannot be empty")
        if len(access_key_secret) == 0:
            raise CredentialException("Environment variable accessKeySecret cannot be empty")
        return credentials.AccessKeyCredential(access_key_id, access_key_secret)
