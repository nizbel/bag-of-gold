from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from storages.backends.dropbox import DropBoxStorage

class StaticStorage(S3Boto3Storage):
    location = settings.AWS_STATIC_LOCATION

class MediaStorage(S3Boto3Storage):
    location = settings.AWS_MEDIA_LOCATION
    file_overwrite = False
    default_acl = 'private'
    custom_domain = False

class BackupStorage(DropBoxStorage):
    location = settings.BACKUP_FILE_STORAGE