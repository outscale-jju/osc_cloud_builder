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
Collection of generic functions
"""

__author__      = "Heckle"
__copyright__   = "BSD"

import time
from osc_cloud_builder.OCBase import SLEEP_SHORT

def wait_state(objs, state_name, timeout=120):
    """
    Wait for cloud ressources to be in a given state.
    :param objs: list of boto object with update() method
    :type: list
    :param state_name: Instance state name expected
    :type state_name: str
    :param timeout: Timeout for instances to reach state_name
    :type timeout: int
    :return: boto objects which are not in the expected state_name
    :rtype: list

    """
    objs = [obj for obj in objs if hasattr(obj, 'update')]

    timeout = time.time() + timeout
    while time.time() < timeout and objs:
        for obj in objs:
            if obj.update() == state_name:
                objs.remove(obj)
            time.sleep(SLEEP_SHORT)

    return objs
