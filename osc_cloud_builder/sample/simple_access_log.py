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
Creates an instance with an ephemeral disk.
See https://wiki.outscale.net/display/DOCU/Ephemeral+Storage
See https://wiki.outscale.net/display/DOCU/Instance+Types
"""

__author__      = "Heckle"
__copyright__   = "BSD"

import uuid
import urllib2
import json
from osc_cloud_builder.OCBase import OCBase
from osc_cloud_builder.sample.vpc.vpc_with_two_subnets import setup_vpc
from osc_cloud_builder.tools.wait_for import wait_state
from boto.ec2.elb.attributes import AccessLogAttribute


def prepare_infra(listeners=[(80, 80, 'TCP')], tag_prefix='', key_name=None, omi_id=None, instance_type='c4.large'):


    """
    :param omi_id: OMI identified
    :type omi_id: str
    """
    ocb = OCBase()
    ocb.activate_stdout_logging()
    vpc, instance_bouncer, instance_private_1 = setup_vpc(tag_prefix=tag_prefix, key_name=key_name, omi_id=omi_id, instance_type=instance_type)
    sg_public = ocb.fcu.get_all_security_groups(group_ids=[instance_bouncer.groups[0].id])[0]
    sg_private = ocb.fcu.get_all_security_groups(group_ids=[instance_private_1.groups[0].id])[0]
    instance_private_2 = ocb.fcu.run_instances(omi_id,
                                               key_name = instance_private_1.key_name,
                                               instance_type = instance_private_1.instance_type,
                                               subnet_id = instance_private_1.subnet_id,
                                               security_group_ids = [sg_private.id]).instances[0]
    wait_state([instance_private_2], 'running')
    ocb.fcu.create_tags([instance_private_2.id], {'Name': tag_prefix})
    #
    lb = ocb.lbu.create_load_balancer('int-fac-{0}'.format(str(uuid.uuid4().fields[0])), None,
                                      listeners=listeners,
                                      subnets=[instance_private_1.subnet_id],
                                      scheme='internet-facing',
                                      security_groups=[sg_public.id])
    lb.register_instances([instance_private_1.id, instance_private_2.id])
    #
    try:
        current_location_ip = urllib2.urlopen('https://ifconfig.io/all.json').read()
        current_location_ip = '{0}/32'.format(json.loads(current_location_ip)['ip'])
    except:
        current_location_ip = '0.0.0.0/0'
    sg_public.authorize(ip_protocol='tcp', from_port=80, to_port=80, cidr_ip=current_location_ip)
    sg_private.authorize(ip_protocol='tcp', from_port=80, to_port=80, src_group=sg_public)
    #
    ocb.log('Start your service on backends {0} and {1} on ports {2} then go to {3}'.format(instance_private_1.id, instance_private_2.id, listeners, lb.dns_name),
            level='info',
            module_name='simple-access-log')
    return lb

def setup_access_log(listeners=[(80, 80, 'TCP')], tag_prefix='', key_name=None, omi_id=None, instance_type='c4.large'):
    ocb = OCBase()
    lb = prepare_infra(listeners, tag_prefix, key_name, omi_id, instance_type)
    lb = ocb.lbu.get_all_load_balancers()[0]
    log_config = AccessLogAttribute()
    log_config.enabled = True
    log_config.s3_bucket_name = 'sample'
    log_config.s3_bucket_prefix = 'simple-access-log'
    log_config.emit_interval = 5
    ocb.lbu.modify_lb_attribute(lb.name, 'accessLog', log_config)
