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
Simple help to create and save a keypair
"""

__author__      = "Heckle"
__copyright__   = "BSD"

import os
from datetime import datetime
from osc_cloud_builder.OCBase import OCBase


def create_key_pair(key_pair_name=None, key_directory='/tmp/keytest.rsa.d/'):
    """
    :param key_pair_name: Key pair name
    :type key_pair_name: str
    :param key_directory: Directory path where keypair will be saved
    :type key_directory: str
    :return: keypair information
    :rtype: dict
    """
    ocb = OCBase()
    if not os.path.isdir(key_directory):
        os.makedirs(key_directory)
    if not key_pair_name:
        key_pair_name = ''.join(['test_key_', datetime.now().strftime("_%d_%m_%s")])
    kp = ocb.fcu.create_key_pair(key_pair_name)
    kp.save(key_directory)

    return {
        "name": key_pair_name,
        "directory": key_directory,
        "path": ''.join([key_directory, key_pair_name, '.rsa'])
    }
