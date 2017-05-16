# -*- coding: utf-8 -*-

# Copyright (c) 2016, Outscale SAS
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
OCBase setup FCU, OSU, EIM and LBU connection objects to Outscale Cloud.
"""

__author__      = "Heckle"
__copyright__   = "BSD"


import sys
import logging
import boto
import ConfigParser
import os.path
import os
import urlparse
import boto.s3.connection
from boto.ec2.regioninfo import EC2RegionInfo
from boto.ec2.regioninfo import RegionInfo
from boto.iam.connection import IAMConnection
from boto.ec2.elb import ELBConnection

from osc_cloud_builder.vendor.outscale.icu import ICUConnection
from osc_cloud_builder.vendor.outscale.fcu import FCUConnection


SLEEP_SHORT = 5

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class OCBError(RuntimeError):
    """
    OCB error class
    """
    pass


class OCBase(object):
    """
    Manage API connections (FCU, OSU, EIM, LBU) and provide centralized logging system
    """

    __metaclass__ = Singleton

    def __init__(self, region='eu-west-2', settings_paths=['~/.osc_cloud_builder/services.ini', '/etc/osc_cloud_builder/services.ini'], is_secure=True, boto_debug=0, debug_filename='/tmp/ocb.log', debug_level='INFO'):
        """
        :param region: region choosen for loading settings.ini section
        :type region: str
        :param settings_paths: paths where services.init should be if needed
        :type settings_paths: list
        :param is_secure: allow connector without ssl
        :type is_secure: bool
        :param boto_debug: debug level for boto
        :type boto_debug: int
        :param debug_filename: File to store logs
        :type debug_filename: str
        """
        self.__logger_setup(debug_filename, debug_level)
        self.region = region
        self.settings_paths = settings_paths
        self.__connections_setup(is_secure, boto_debug)

    def __logger_setup(self, debug_filename, debug_level):
        """
        Logger setup
        :param debug_filename: File to store logs
        :type debug_filename: str
        :param debug_level: level debug
        :type debug_level: str
        """
        debug_level = getattr(logging, debug_level)
        self.__logger = logging.getLogger()
        logging.basicConfig(filename=debug_filename,
                            filemode='a',
                            level=debug_level,
                            format='%(asctime)s.%(msecs)d %(levelname)s - %(message)s',
                            datefmt="%Y-%m-%d %H:%M:%S")

    def __load_config(self):
        """
        Load Cloud configuration from services.ini OR environment
        """
        endpoints = {}
        endpoints['fcu'] = None
        endpoints['lbu'] = None
        endpoints['eim'] = None
        endpoints['osu'] = None
        settings = ConfigParser.ConfigParser()
        settings_path = None

        for set_path in self.settings_paths:
            if os.path.exists(set_path):
                settings_path = set_path
        if not settings_path:
            full_path = os.path.realpath(__file__)
            base_path = os.path.dirname(full_path)
            settings_path = '{0}/../services.ini'.format(base_path)
        settings.read(filenames=settings_path)


        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID', None)
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY', None)
        if not access_key_id or not secret_access_key:
            try:
                access_key_id = settings.get(self.region, 'access_key_id', None)
                secret_access_key = settings.get(self.region, 'secret_access_key', None)
            except ConfigParser.Error:
                self.__logger.critical('You must setup both AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variable or in your settings.ini file')
                raise OCBError('Bad credential (access_key_id, secret_access_key) setup')

        endpoints['fcu'] = os.environ.get('FCU_ENDPOINT', None)
        if not endpoints['fcu']:
            try:
                endpoints['fcu'] = settings.get(self.region, 'fcu_endpoint')
            except ConfigParser.Error:
                self.log('No fcu_endpoint set', 'warning')

        endpoints['lbu'] = os.environ.get('LBU_ENDPOINT', None)
        if not endpoints['lbu']:
            try:
                endpoints['lbu'] = settings.get(self.region, 'lbu_endpoint')
            except ConfigParser.Error:
                self.log('No lbu_endpoint set', 'warning')

        endpoints['eim'] = os.environ.get('EIM_ENDPOINT', None)
        if not endpoints['eim']:
            try:
                endpoints['eim'] = settings.get(self.region, 'eim_endpoint')
            except ConfigParser.Error:
                self.log('No eim_endpoint set', 'warning')

        endpoints['osu'] = os.environ.get('OSU_ENDPOINT', None)
        if not endpoints['osu']:
            try:
                endpoints['osu'] = settings.get(self.region, 'osu_endpoint')
            except ConfigParser.Error:
                self.log('No osu_endpoint set', 'warning')

        icu = {}
        icu['endpoint'] = os.environ.get('ICU_ENDPOINT', None)
        icu['login'] = os.environ.get('ICU_LOGIN', '')
        icu['password'] = os.environ.get('ICU_PASSWORD', '')
        if not icu['endpoint']:
            try:
                icu['endpoint'] = settings.get(self.region, 'icu_endpoint')
                icu['login'] = settings.get(self.region, 'icu_login')
                icu['endpoint'] = settings.get(self.region, 'icu_password')
            except ConfigParser.Error:
                self.log('No icu_endpoint set', 'warning')

        return access_key_id, secret_access_key, endpoints, icu

    def __connect_icu(self, url, aws_access_key_id='', aws_secret_access_key='', login='', password='', **kwargs):
        """
        Connect to an ICU Api endpoint.
        Additional arguments are passed to ICUConnection.

        :param str url: Url for the icu api endpoint to connect to
        :param str aws_access_key_id: Your AWS Access Key ID
        :param str aws_secret_access_key: Your AWS Secret Access Key
        :param str login: Your login email ID
        :param str password: Your raw password to login
        :param dict kwargs:
        :return class: `outscale.boto.icu.ICUConnection`
        """
        if not url.startswith('https://'):
            url = 'https://{0}'.format(url)
        purl = urlparse.urlparse(url)
        kwargs['port'] = purl.port
        kwargs['path'] = purl.path
        if not 'is_secure' in kwargs:
            kwargs['is_secure'] = (purl.scheme == "https")

        kwargs['host'] = RegionInfo(name=purl.hostname, endpoint=purl.hostname).endpoint
        kwargs['aws_access_key_id'] = aws_access_key_id
        kwargs['aws_secret_access_key'] = aws_secret_access_key
        kwargs['login'] = login
        kwargs['password'] = password

        return ICUConnection(**kwargs)


    def __connections_setup(self, is_secure, boto_debug):
        """
        Creates FCU, OSU and EIM connections if endpoints are configured
        :param is_secure: allow connection without SSL
        :type is_secure: bool
        :param boto_debug: debug level for boto
        :type boto_debug: int
        :raises OCBError: When connections can not be created because AK and SK are not set up in environment variable
        """

        access_key_id, secret_access_key, endpoints, icu_conn = self.__load_config()

        if endpoints['fcu']:
            fcu_endpoint = EC2RegionInfo(endpoint=endpoints['fcu'])
            self.fcu = FCUConnection(access_key_id, secret_access_key, region=fcu_endpoint, is_secure=is_secure, debug=boto_debug)
        else:
            self.__logger.info('No FCU connection configured')
            self.fcu = None

        if endpoints['lbu']:
            lbu_endpoint = EC2RegionInfo(endpoint=endpoints['lbu'])
            self.lbu = ELBConnection(access_key_id, secret_access_key, region=lbu_endpoint, debug=boto_debug)
        else:
            self.__logger.info('No LBU connection configured')
            self.lbu = None

        if endpoints['eim']:
            self.eim = IAMConnection(access_key_id, secret_access_key, host=endpoints['eim'], debug=boto_debug)
        else:
            self.__logger.info('No EIM connection configured')
            self.eim = None

        if endpoints['osu']:
            self.osu = boto.connect_s3(access_key_id, secret_access_key, host=endpoints['osu'],
                                       calling_format=boto.s3.connection.ProtocolIndependentOrdinaryCallingFormat())
        else:
            self.__logger.info('No OSU connection configured')
            self.osu = None

        if icu_conn['endpoint']:
            self.icu = self.__connect_icu(icu_conn['endpoint'], access_key_id, secret_access_key, icu_conn['login'], icu_conn['password'])
        else:
            self.__logger.info('No ICU connection configured')
            self.icu = None


    def log(self, message, level='debug', module_name=''):
        """
        Centralized log system
        :param message: Message to be logged
        :type message: str
        :param module_name: Module name where the message is coming
        :type module_name: str
        :param level: message level
        :type level: str
        """
        try:
            log = getattr(self.__logger, level)
        except AttributeError:
            log = getattr(self.__logger, 'debug')
        log('{0} - {1}'.format(module_name, message))


    def activate_stdout_logging(self):
        """
        Display logging messages in stdout
        """
        ch = logging.StreamHandler(sys.stdout)
        logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.__logger.addHandler(ch)
