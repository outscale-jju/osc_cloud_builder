# -*- coding:utf-8 -*-
"""
Object model for snapshot export tasks
"""
from boto.ec2.ec2object import EC2Object


class ImageExportTask(EC2Object):
    def __init__(self, connection=None):
        """
        Represents a Image export task.

        :ivar id: The unique ID of the export task.
        :ivar image_id: ID of the image being exported
        :ivar state: The current state of the export (active|completed|failed).
        :ivar status_message: Status message in case of error.
        :ivar disk_image_format: Format of the exported snapshot.
        :ivar bucket: Name of the target bucket.
        :ivar str manifest_url: URL to the manifest file.
        :ivar int completion: completion
        """
        super(ImageExportTask, self).__init__(connection)
        self.id = None
        self.image_id = None
        self.state = None
        self.status_message = None
        self.disk_image_format = None
        self.bucket = None
        self.manifest_url = None
        self.access_key = None
        self.secret_key = None
        self.completion = None

    def __repr__(self):
        return 'ImageExportTask:%s' % self.id

    def endElement(self, name, value, connection):
        if name == 'imageExportTaskId':
            self.id = value
        elif name == 'state':
            self.state = value
        elif name == 'statusMessage':
            self.status_message = value
        elif name == 'imageId':
            self.image_id = value
        elif name == 'diskImageFormat':
            self.disk_image_format = value
        elif name == 'osuBucket':
            self.bucket = value
        elif name == 'AccessKey':
            self.access_key = value
        elif name == 'SecretKey':
            self.secret_key = value
        elif name == 'completion':
            self.completion = int(value)
        elif name == 'osuManifestUrl':
            self.manifest_url = value
        elif name in ['imageExport', 'imageExportTask', 'exportToOsu', 'osuAkSk']:
            pass
        else:
            setattr(self, name, value)

    def update(self):
        pass

