# -*- coding:utf-8 -*-
"""
Represents a connection to Outscale ICU API
"""
import json
import boto
from boto.connection import AWSQueryConnection
from boto.exception import JSONResponseError


class ICUConnection(AWSQueryConnection):

    ICUAPIVersion = boto.config.get('Boto', 'icu_version', '2017-01-11')
    ServiceName = "icu"
    TargetPrefix = "TinaIcuService"
    ResponseError = JSONResponseError

    def __init__(self, **kwargs):
        """
        See osc_cloud_builder.OCbase.__connect_icu for more details
        """
        self.login = kwargs.pop('login', None)
        self.password = kwargs.pop('password', None)
        super(ICUConnection, self).__init__(**kwargs)

    def _required_auth_capability(self):
        return ['hmac-v4']

    def make_request(self, action, body):
        """
        :param action: API Action
        :type action: str
        :param body: payload
        :type body: str
        Rewrite of boto.make_request to match with ICU-API
        """
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.host,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read().decode('utf-8')
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            raise self.ResponseError(response.status, response.reason, json.loads(response_body))

    def create_account(self, email, password, first_name, last_name, city, zipcode, country, company_name,
                       mobile_number=None, phone_number=None, vat_number=None, job_title=None, profile=None):
        """
        Creates a user account

        :param str email: Email of the new account.
        :param str password: Password of the new account.
        :param str first_name: First name of the account holder.
        :param str last_name: Last name of the account holder.
        :param str city: City of the account holder.
        :param str zipcode: Zipcode of the account holder.
        :param str country: Country of the account holder.
        :param str company_name: Company name of the account holder.
        :param str mobile_number: Mobile number of the account holder (optional).
        :param str phone_number: Phone number of the account holder (optional).
        :param str vat_number: Vat number of the account holder (optional).
        :param str job_title: Job title  of the account holder (optional).
        :param str profile: The type of the profile (optional).
                            Valid values are: default | admin | sales.
        """
        params = {
            'Email': email,
            'Password': password,
            'FirstName': first_name,
            'LastName': last_name,
            'City': city,
            'ZipCode': zipcode,
            'Country': country,
            'CompanyName': company_name
        }
        for k, v in params.iteritems():
            if not len(v.strip()):
                raise ValueError('%s must not be empty!'% k)
        if mobile_number:
            params['MobileNumber'] = mobile_number
        if phone_number:
            params['PhoneNumber'] = phone_number
        if vat_number:
            params['VatNumber'] = vat_number
        if job_title:
            params['JobTitle'] = job_title
        if profile:
            params['Profile'] = profile
        return self.make_request(action='CreateAccount',
                                 body=json.dumps(params))

    def get_account(self):
        params = {}
        return self.make_request(action='GetAccount',
                                 body=json.dumps(params))

    def send_reset_password_email(self, email):
        """
        Sends ResetPassword email to the email address provided.

        :param str email: Email to which the ResetPassword mail should be sent
        """
        params = {
            'Email': email
        }
        return self.make_request(action='SendResetPasswordEmail', body=json.dumps(params))

    def reset_account_password(self, token, password):
        """
        Resets tha account password, upon token validation.

        :param str token: Token received in the ResetPassword email, specific to the account
        :param str password: New password for the account
        """
        params = {
            'Token': token,
            'Password': password
        }
        return self.make_request(action='ResetAccountPassword', body=json.dumps(params))

    def authenticate_account(self, login, password):
        """
        Authenticates any account credentials

        :param str login: Email or AccountPid of the account to authenticate
        :param str password: Password of the account holder
        """
        params = {
            'Login': login,
            'Password': password
        }
        return self.make_request(action='AuthenticateAccount',
                                 body=json.dumps(params))

    def update_account(self, email=None, first_name=None, last_name=None, city=None, zipcode=None, country=None,
                       company_name=None, mobile_number=None, phone_number=None, vat_number=None, job_title=None):
        """
        Updates an account holder's details

        :param str email: New email for the account holder (Cannot be empty).
        :param str first_name: New first name for the account holder.
        :param str last_name: New last name for the account holder.
        :param str city: New city for the account holder.
        :param str zipcode: New zipcode for the account holder.
        :param str country: New country for the account holder.
        :param str company_name: New company name for the account holder.
        :param str mobile_number: New mobile number for the account holder.
        :param str phone_number: New phone number for the account holder.
        :param str vat_number: New vat number for the account holder.
        :param str job_title: New job title for the account holder.
        """
        params = {
            'Email': email,
            'FirstName': first_name,
            'LastName': last_name,
            'City': city,
            'ZipCode': zipcode,
            'Country': country,
            'CompanyName': company_name,
            'MobileNumber': mobile_number,
            'PhoneNumber': phone_number,
            'VatNumber': vat_number,
            'JobTitle': job_title
        }
        params = dict((k, v) for k, v in params.iteritems() if v is not None)
        return self.make_request(action='UpdateAccount',
                                 body=json.dumps(params))

    def get_access_key(self, access_key_id):
        """
        Get an access key associated with the account that sent the request.

        :param str access_key_id: The ID of the access key to be retrieved.

        """
        params = {
            'Login': self.login,
            'Password': self.password,
            'AccessKeyId': access_key_id
        }
        if self.login and self.password:
            params['AuthenticationMethod'] = 'password'
        elif self.aws_access_key_id and self.aws_secret_access_key:
            params['AuthenticationMethod'] = 'accesskey'
        else:
            params['AuthenticationMethod'] = ''
        return self.make_request(action='GetAccessKey',
                                 body=json.dumps(params))

    def get_all_access_keys(self, marker=None, max_items=None, tags=[]):
        """
        Get all access keys associated with an account that sent the request.

        :param str marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :param int max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        :param list tags: An array of dictionaries (every dict has keys: 'Key' & 'Value').
                        Today only one tag is supported with Key: `Name` & Value: `Marketplace`
        """
        params = {
            'Login': self.login,
            'Password': self.password
        }
        if self.login and self.password:
            params['AuthenticationMethod'] = 'password'
        elif self.aws_access_key_id and self.aws_secret_access_key:
            params['AuthenticationMethod'] = 'accesskey'
        else:
            params['AuthenticationMethod'] = ''
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        if tags:
            params['Tags'] = tags
        return self.make_request(action='ListAccessKeys',
                                 body=json.dumps(params))

    def create_access_key(self, tags=[]):
        """
        Creates a new Secret Access Key and corresponding Access Key ID
        for the account that sent the request. The default status for new keys is Active

        Tag can be added specifying if the Access key is specifically for Marketplace.

        :param list tags: An array of dictionaries (every dict has keys: 'Key' & 'Value').
                        Today only one tag is supported with Key: `Name` & Value: `Marketplace`
        """
        params = {
            'Login': self.login,
            'Password': self.password
        }
        if self.login and self.password:
            params['AuthenticationMethod'] = 'password'
        elif self.aws_access_key_id and self.aws_secret_access_key:
            params['AuthenticationMethod'] = 'accesskey'
        else:
            params['AuthenticationMethod'] = ''
        if tags:
            params['Tags'] = tags
        return self.make_request(action='CreateAccessKey',
                                 body=json.dumps(params))

    def delete_access_key(self, access_key_id):
        """
        Delete an access key associated with the account that sent the request.

        :param str access_key_id: The ID of the access key to be deleted.

        """
        params = {
            'Login': self.login,
            'Password': self.password,
            'AccessKeyId': access_key_id
        }
        if self.login and self.password:
            params['AuthenticationMethod'] = 'password'
        elif self.aws_access_key_id and self.aws_secret_access_key:
            params['AuthenticationMethod'] = 'accesskey'
        else:
            params['AuthenticationMethod'] = ''
        return self.make_request(action='DeleteAccessKey',
                                 body=json.dumps(params))

    def update_access_key(self, access_key_id, status):
        """
        Changes the status of the specified access key from Active to Inactive
        or vice versa. This action can be used to disable an account's key as
        part of a key rotation workflow.

        :param str access_key_id: The ID of the access key.
        :param str status: Either Active or Inactive.

        """
        params = {
            'Login': self.login,
            'Password': self.password,
            'AccessKeyId': access_key_id,
            'Status': status
        }
        if self.login and self.password:
            params['AuthenticationMethod'] = 'password'
        elif self.aws_access_key_id and self.aws_secret_access_key:
            params['AuthenticationMethod'] = 'accesskey'
        else:
            params['AuthenticationMethod'] = ''
        return self.make_request(action='UpdateAccessKey',
                                 body=json.dumps(params))

    def check_signature(self, access_key_id, signature, string_to_sign, region, service_name, amz_date):
        """
        Validates the authenticity of the signature.

        Whenever client makes http request to OWS (client -> OWS), a unique signature is generated on client side using
        following parameters (AccessKeyId, Region, ServiceName, StringToSign, AmzDate) and sent to OWS.
        Inside OWS the authentication of signature is verified and if successful the request passes through.

        This call will be used by any intermediate portal (client -> <intermediate> -> OWS).
        The signature received from client will be authenticated from OWS and if validated
        the intermediate portal will process the request.

        :param str access_key_id: The ID of the access key which generated the signature.
        :param str signature: The signature generated in http request from client.
        :param str string_to_sign: The string to sign.
        :param str region: The region name.
        :param str service_name: The name of the API service.
        :param str amz_date: The datetime stamp of the sent request in iso8601 format YYYYMMDD.

        """
        params = {
            'AccessKeyId': access_key_id,
            'Signature': signature,
            'StringToSign': string_to_sign,
            'Region': region,
            'ServiceName': service_name,
            'AmzDate': amz_date
        }
        return self.make_request(action='CheckSignature',
                                 body=json.dumps(params))

    def get_consumption_account(self, from_date, to_date):
        """
        Retrieves resources consumption for the given period

        :param datetime from_date: start of period
        :param datetime to_date: end of period
        """
        params = {
            'FromDate': from_date.isoformat(),
            'ToDate': to_date.isoformat()
        }
        return self.make_request(action='ReadConsumptionAccount',
                                 body=json.dumps(params))

    def get_catalog(self, region=None):
        """
        Retrieves the catalog of prices for Outscale products and services

        :param str region: Retrieves prices for the given region, if unset current region is used
        """
        params = {'Region': region}
        return self.make_request(action='ReadCatalog', body=json.dumps(params))

    def get_public_catalog(self, region=None):
        """
        Retrieves the public catalog of prices for Outscale products and services

        :param str region: Retrieves prices for the given region, if unset current region is used
        """
        params = {'Region': region}
        return self.make_request(action='ReadPublicCatalog', body=json.dumps(params))
