# -*- coding:utf-8 -*-
"""
Object model for VNets
"""
from boto.ec2.ec2object import EC2Object

class FwLogOptions(EC2Object):
    def __init__(self, connection=None):
        """
        Firewall logging options

        :ivar bool enabled: Whether logging is enabled or not
        :ivar str rate_limit: Rate limitation for loggin
        :ivar str host: Target syslog server
        """
        super(FwLogOptions, self).__init__(connection)
        self.enabled = False
        self.rate_limit = None
        self.host = None

    def endElement(self, name, value, connection):
        if name == 'enabled':
            self.enabled = value.lower() == 'true'
        elif name == 'rateLimit':
            self.rate_limit = value
        elif name == 'host':
            self.host = value
        else:
            setattr(self, name, value)


class VnOptions(EC2Object):
    def __init__(self, connection=None):
        """
        Represents options of a Vn

        :ivar str vn_id: ID of the Vn
        :ivar FwLogOptions fwLog: firewall logging options
        """
        super(VnOptions, self).__init__(connection)
        self.vn_id = None
        self.fwlog = None

    def __repr__(self):
        return 'VnOptions:%s' % self.vn_id

    def startElement(self, name, attrs, connection):
        retval = super(VnOptions, self).startElement(name, attrs, connection)
        if retval is not None:
            return retval
        if name == 'fwLog':
            self.fwlog = FwLogOptions()
            return self.fwlog
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'vnId':
            self.vn_id = value
        elif name == 'fwLog':
            self.description = value
        else:
            setattr(self, name, value)
