# -*- coding:utf-8 -*-
"""
Represents a connection to Outscale FCU API
"""
import contextlib
from functools import wraps
import urlparse

import boto
from boto.vpc import VPCConnection
from osc_cloud_builder.vendor.outscale.fcu.vn import VnOptions
from osc_cloud_builder.vendor.outscale.fcu.snapshot_export_task import SnapshotExportTask
from osc_cloud_builder.vendor.outscale.fcu.product_type import ProductType
from osc_cloud_builder.vendor.outscale.fcu.instance_type import InstanceType
from osc_cloud_builder.vendor.outscale.fcu.quota import ReferenceQuota
from osc_cloud_builder.vendor.outscale.fcu.image_export_task import ImageExportTask

@contextlib.contextmanager
def patch(obj, attribute, decorator):
    original = getattr(obj, attribute)
    setattr(obj, attribute, decorator(original))
    try:
        yield
    finally:
        setattr(obj, attribute, original)


def fcuext(function):
    """
    Decorator to mark a method as part of the FCU ext API.
    Method will be called with a distinct API version
    """
    @wraps(function)
    def wrapper(self, *args, **kwargs):
        current, self.APIVersion = self.APIVersion, self.FCUExtAPIVersion
        try:
            return function(self, *args, **kwargs)
        finally:
            self.APIVersion = current
    return wrapper


def connect_fcu_endpoint(url, aws_access_key_id, aws_secret_access_key, **kwargs):
    """
    Connect to an FCU Api endpoint.  Additional arguments are passed
    through to FCUConnection.

    :type url: string
    :param url: A url for the ec2 api endpoint to connect to

    :type aws_access_key_id: string
    :param aws_access_key_id: Your AWS Access Key ID

    :type aws_secret_access_key: string
    :param aws_secret_access_key: Your AWS Secret Access Key

    :rtype: :class:`osc_cloud_builder.vendor.outscale.fcu.FCUConnection`
    """
    from boto.ec2.regioninfo import RegionInfo

    purl = urlparse.urlparse(url)
    kwargs['port'] = purl.port
    kwargs['host'] = purl.hostname
    kwargs['path'] = purl.path
    if not 'is_secure' in kwargs:
        kwargs['is_secure'] = (purl.scheme == "https")

    kwargs['region'] = RegionInfo(name=purl.hostname,
                                  endpoint=purl.hostname)
    kwargs['aws_access_key_id'] = aws_access_key_id
    kwargs['aws_secret_access_key'] = aws_secret_access_key

    return FCUConnection(**kwargs)


class FCUConnection(VPCConnection):

    FCUExtAPIVersion = boto.config.get('Boto', 'fcuext_version', '2017-02-01')

    @fcuext
    def export_snapshot(self, snapshot_id, bucket, disk_image_format, ak=None, sk=None, prefix=None, dry_run=False):
        """
        Export a snapshot to an OSU(S3) bucket.

        :param snapshot_id: The snapshot to export.
        :type snapshot_id: str
        :param bucket: The bucket to export to, bucket must exist and allow write access to Outscale account.
        :type bucket: str
        :param disk_image_format: The export format: vmdk vdi qcow2
        :type disk_image_format: str
        :param prefix: Prefix of the destination key in the bucket,
                       snapshot will be written to prefix + snapshot_export_task_id + '.' + disk_image_format.
        :type prefix: str
        :param ak: The access key used to create the bucket.
        :type ak: None, str
        :param sk: The secret key used to create the bucket.
        :type sk: None, str
        """
        params = {
            'SnapshotId': snapshot_id,
            'ExportToOsu.OsuBucket': bucket,
            'ExportToOsu.DiskImageFormat': disk_image_format,
        }

        if prefix is not None:
            params['ExportToOsu.OsuPrefix'] = prefix
        if ak and sk:
            params['ExportToOsu.aksk.AccessKey'] = ak
            params['ExportToOsu.aksk.SecretKey'] = sk
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateSnapshotExportTask', params, SnapshotExportTask)

    @fcuext
    def get_all_snapshot_export_tasks(self, snapshot_export_ids=None, filters=None, dry_run=False):
        params = {}
        if snapshot_export_ids:
            self.build_list_params(params, snapshot_export_ids, 'SnapshotExportTaskId')
        if filters:
            self.build_filter_params(params, dict(filters))
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_list('DescribeSnapshotExportTasks', params, [('item', SnapshotExportTask)])

    @fcuext
    def get_product_type(self, snapshot_id=None, image_id=None):
        params = {}
        if snapshot_id:
            params['SnapshotId'] = snapshot_id
        if image_id:
            params['ImageId'] = image_id

        return self.get_object('GetProductType', params, ProductType)

    @fcuext
    def get_product_types(self, snapshot_id=None, image_id=None):
        params = {}
        if snapshot_id:
            params['SnapshotId'] = snapshot_id
        if image_id:
            params['ImageId'] = image_id

        return self.get_list('GetProductTypes', params, [('item', ProductType)])

    @fcuext
    def get_all_instance_types(self, filters=None, dry_run=False):
        params = {}

        if filters:
            self.build_filter_params(params, filters)

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_list('DescribeInstanceTypes', params, [('item', InstanceType)])

    @fcuext
    def get_all_product_types(self, filters=None, dry_run=False):
        params = {}

        if filters:
            self.build_filter_params(params, filters)

        if dry_run:
            params['DryRun'] = 'true'

        return self.get_list('DescribeProductTypes', params, [('item', ProductType)])

    def multi_run_instances(self, private_ip_addresses=None, *args, **kwargs):
        """
        Like boto.ec2.connection.EC2Connection.run_instance, but accept an additional parameter: private_ip_addresses

        :type private_ip_addresses: list
        :param private_ip_addresses: The list of IP to assign to each instance to spawn
           Size of the list must be the same as parameter  `max_count`
           Each instance created will take its private IP address from this list, in sequence
        """
        def hook(function):
            def result(action, params, cls, path='/', parent=None, verb='GET'):
                if private_ip_addresses:
                    self.build_list_params(params, private_ip_addresses, 'PrivateIpAddresses')
                return function(action, params, cls, path, parent, verb)
            return result

        with patch(self, 'get_object', hook):
            return self.run_instances(*args, **kwargs)

    @fcuext
    def modify_instance_keypair(self, instance_id, key_name):
        params = {}
        if instance_id:
            params['InstanceId'] = instance_id
        if key_name:
            params['KeyName'] = key_name
        return self.get_status('ModifyInstanceKeypair', params)

    @fcuext
    def get_all_quotas(self, quota_names=None, max_results=None, next_token=None, filters=None):
        """
        Retrieve all the quotas associated with your account.

        :param list quota_names: Names of quota whose description is required.
        :param int max_results: The maximum number of paginated items per response.
        :param str next_token: A string indicating to get the next paginated set of results.
        :param list filters: one or more filters

        :return list: list of :class:`boto.fcu.quota.ReferenceQuota`
        """
        params = {}
        if quota_names:
            self.build_list_params(params, quota_names, 'QuotaName')
        if max_results is not None:
            params['MaxResults'] = max_results
        if next_token:
            params['NextToken'] = next_token
        if filters:
            self.build_filter_params(params, filters)
        return self.get_list('DescribeQuotas', params, [('item', ReferenceQuota)])

    @fcuext
    def read_vn_options(self, vn_id):
        """
        Retrieve Vn options

        :param str vn_id: ID of the Vn to retrieve
        :resturn: :class:`boto.fcu.vn.VnOptions`
        """
        params = {'VnId': vn_id}

        return self.get_object('ReadVnOptions', params, VnOptions)

    @fcuext
    def update_vn_options(self, vn_id, fwlog=None):
        params = {'VnId': vn_id}

        if fwlog:
            if 'enabled' in fwlog:
                params['FwLog.Enabled'] = 'true' if fwlog['enabled'] else 'false'
            if 'host' in fwlog:
                params['FwLog.Host'] = fwlog['host'] or ''
            if 'rate_limit' in fwlog:
                params['FwLog.RateLimit'] = fwlog['rate_limit'] or ''

        return self.get_object('UpdateVnOptions', params, VnOptions)

    @fcuext
    def export_image(self, image_id, bucket, disk_image_format='qcow2', ak=None, sk=None, prefix=None, dry_run=False):
        """
        Export an image to an OSU(S3) bucket.

        :param str image_id: The image to export.
        :param str bucket: The bucket to export to, bucket must exist
        :param str disk_image_format: The export format: vmdk vdi qcow2
        :param str ak: The access key used to create the bucket.
        :param str sk: The secret key used to create the bucket.
        :param str prefix: Prefix of the destination key in the bucket,
                       image will be written to prefix + image_export_task_id
        """
        params = {
            'ImageId': image_id,
            'ExportToOsu.OsuBucket': bucket,
            'ExportToOsu.DiskImageFormat': disk_image_format,
        }

        if prefix is not None:
            params['ExportToOsu.OsuPrefix'] = prefix
        if ak and sk:
            params['ExportToOsu.OsuAkSk.AccessKey'] = ak
            params['ExportToOsu.OsuAkSk.SecretKey'] = sk
        if dry_run:
            params['DryRun'] = 'true'
        return self.get_object('CreateImageExportTask', params, ImageExportTask)
