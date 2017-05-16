# -*- coding:utf-8 -*-
"""
Object model for quota
"""
from boto.ec2.ec2object import EC2Object
from boto.resultset import ResultSet


class QuotaList(EC2Object):
    def __init__(self, connection=None):
        """
        Represents a quota

        :ivar name: Name of the quota.
        :ivar owner_id: Id of the owner whose quota it is.
        :ivar display_name: display name of the quota.
        :ivar description: description of the quota.
        :ivar group_name: name of the group to which quota belongs to.
        :ivar max_quota_value: maximum value of the quota that owner is allowed to use.
        :ivar used_quota_value: value of the quota that owner has already used.
        """
        super(QuotaList, self).__init__(connection)
        self.owner_id = None
        self.name = None
        self.display_name = None
        self.description = None
        self.group_name = None
        self.max_quota_value = None
        self.used_quota_value = None

    def endElement(self, name, value, connection):
        if name == 'ownerId':
            self.owner_id = value
        elif name == 'name':
            self.name = value
        elif name == 'displayName':
            self.display_name = value
        elif name == 'description':
            self.description = value
        elif name == 'groupName':
            self.group_name = value
        elif name == 'maxQuotaValue':
            self.max_quota_value = int(value)
        elif name == 'usedQuotaValue':
            self.used_quota_value = int(value)
        else:
            setattr(self, name, value)


class ReferenceQuota(EC2Object):
    def __init__(self, connection=None):
        """
        Represents a reference quota

        :ivar reference: Reference for the quota.
            resource id if its a resource specific quota, otherwise 'global'.
        :ivar list quotas: list of quotas.
        """
        super(ReferenceQuota, self).__init__(connection)
        self.reference = None
        self.quotas = ResultSet([('item', QuotaList)])

    def __repr__(self):
        return 'ReferenceQuota:%s' % self.reference

    def startElement(self, name, attrs, connection):
        if name == 'quotaSet':
            return self.quotas
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'reference':
            self.reference = value
        else:
            setattr(self, name, value)
