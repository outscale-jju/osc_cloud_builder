#!/usr/bin/python
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
Create a VPC and connect it with Fabric
Requirements:
    pip install Fabric
"""

__author__      = "Heckle"
__copyright__   = "BSD"

from osc_cloud_builder.OCBase import OCBase
from osc_cloud_builder.tools.create_key_pair import create_key_pair
from vpc import vpc_with_two_subnets, vpc_teardown
from fabric.api import run, env


def connect_to_instance_in_ssh(address, keypair_path, user='root'):
    """
    Run the command LS on a given instance
    :param address: ip or dns name of a machine
    :type address: str
    :param keypair_path: keypair path
    :type keypair_path: str
    """

    env.host_string = address
    env.user = user
    env.parallel = False
    env.key_filename = keypair_path
    env.disable_known_hosts = True
    env.connection_attempts = 10
    env.timeout = 120

    ocb.log(run('ls -la /root'), level='INFO')

if __name__ == '__main__':
    ocb = OCBase(debug_level='INFO')
    ocb.activate_stdout_logging()
    omi = ocb.fcu.get_all_images(filters={'root-device-type': 'ebs',
                                          'architecture': 'x86_64',
                                          'name': ['centos6*', 'centos-7*', 'Centos7*', 'Centos-7*']})[0]
    kp = create_key_pair()
    vpc, instance_nat, instance_bouncer, instance_private = vpc_with_two_subnets.setup_vpc('ami-2472c655', kp['name'])
    ocb.log('vpc {0} created'.format(vpc.id), level='INFO')
    try:
        connect_to_instance_in_ssh(instance_bouncer.ip_address, kp['path'], tag_prefix='test-connect-to-instance')
    except Exception as err:
        ocb.log('Can not connect to instance {0} with address {1} because {2}'.format(instance_bouncer.id, instance_bouncer.ip_address, err), level='INFO')
    if raw_input('Teardown VPC {0} ? [Y/n] '.format(vpc.id)) != 'n':
        vpc_teardown.teardown(vpc.id, terminate_instances=True)

