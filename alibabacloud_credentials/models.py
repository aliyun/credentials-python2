# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from Tea.model import TeaModel
from Tea.converter import TeaConverter


class Config(TeaModel):
    """
    Model for initing credential
    """
    def __init__(self, access_key_id='', access_key_secret='', security_token='', bearer_token='',
                 duration_seconds=3600, role_arn='', policy='', role_session_expiration=3600, role_session_name='',
                 public_key_id='', private_key_file='', role_name='', type='', host='', timeout=1000,
                 connect_timeout=1000, proxy=''):
        # accesskey id
        self.access_key_id = TeaConverter.to_unicode(access_key_id)  # type: unicode
        # accesskey secret
        self.access_key_secret = TeaConverter.to_unicode(access_key_secret)  # type: unicode
        # security token
        self.security_token = TeaConverter.to_unicode(security_token)  # type: unicode
        # bearer token
        self.bearer_token = TeaConverter.to_unicode(bearer_token)  # type: unicode
        # duration seconds
        self.duration_seconds = duration_seconds  # type: int
        # role arn
        self.role_arn = TeaConverter.to_unicode(role_arn)  # type: unicode
        # policy
        self.policy = TeaConverter.to_unicode(policy)  # type: unicode
        # role session expiration
        self.role_session_expiration = role_session_expiration  # type: int
        # role session name
        self.role_session_name = TeaConverter.to_unicode(role_session_name)  # type: unicode
        # publicKey id
        self.public_key_id = TeaConverter.to_unicode(public_key_id)  # type: unicode
        # privateKey file
        self.private_key_file = TeaConverter.to_unicode(private_key_file)  # type: unicode
        # role name
        self.role_name = TeaConverter.to_unicode(role_name)  # type: unicode
        # credential type
        self.type = TeaConverter.to_unicode(type)  # type: unicode
        self.host = TeaConverter.to_unicode(host)  # type: unicode
        self.timeout = timeout  # type: int
        self.connect_timeout = connect_timeout  # type: int
        self.proxy = TeaConverter.to_unicode(proxy)  # type: unicode

    def validate(self):
        pass

    def to_map(self):
        result = dict()
        if self.access_key_id is not None:
            result['accessKeyId'] = self.access_key_id
        if self.access_key_secret is not None:
            result['accessKeySecret'] = self.access_key_secret
        if self.security_token is not None:
            result['securityToken'] = self.security_token
        if self.bearer_token is not None:
            result['bearerToken'] = self.bearer_token
        if self.duration_seconds is not None:
            result['durationSeconds'] = self.duration_seconds
        if self.role_arn is not None:
            result['roleArn'] = self.role_arn
        if self.policy is not None:
            result['policy'] = self.policy
        if self.role_session_expiration is not None:
            result['roleSessionExpiration'] = self.role_session_expiration
        if self.role_session_name is not None:
            result['roleSessionName'] = self.role_session_name
        if self.public_key_id is not None:
            result['publicKeyId'] = self.public_key_id
        if self.private_key_file is not None:
            result['privateKeyFile'] = self.private_key_file
        if self.role_name is not None:
            result['roleName'] = self.role_name
        if self.type is not None:
            result['type'] = self.type
        if self.host is not None:
            result['host'] = self.host
        if self.timeout is not None:
            result['timeout'] = self.timeout
        if self.connect_timeout is not None:
            result['connectTimeout'] = self.connect_timeout
        if self.proxy is not None:
            result['proxy'] = self.proxy
        return result

    def from_map(self, m=None):
        m = m or dict()
        if m.get('accessKeyId') is not None:
            self.access_key_id = m.get('accessKeyId')
        if m.get('accessKeySecret') is not None:
            self.access_key_secret = m.get('accessKeySecret')
        if m.get('securityToken') is not None:
            self.security_token = m.get('securityToken')
        if m.get('bearerToken') is not None:
            self.bearer_token = m.get('bearerToken')
        if m.get('durationSeconds') is not None:
            self.duration_seconds = m.get('durationSeconds')
        if m.get('roleArn') is not None:
            self.role_arn = m.get('roleArn')
        if m.get('policy') is not None:
            self.policy = m.get('policy')
        if m.get('roleSessionExpiration') is not None:
            self.role_session_expiration = m.get('roleSessionExpiration')
        if m.get('roleSessionName') is not None:
            self.role_session_name = m.get('roleSessionName')
        if m.get('publicKeyId') is not None:
            self.public_key_id = m.get('publicKeyId')
        if m.get('privateKeyFile') is not None:
            self.private_key_file = m.get('privateKeyFile')
        if m.get('roleName') is not None:
            self.role_name = m.get('roleName')
        if m.get('type') is not None:
            self.type = m.get('type')
        if m.get('host') is not None:
            self.host = m.get('host')
        if m.get('timeout') is not None:
            self.timeout = m.get('timeout')
        if m.get('connectTimeout') is not None:
            self.connect_timeout = m.get('connectTimeout')
        if m.get('proxy') is not None:
            self.proxy = m.get('proxy')
        return self


