import os
import boto3
import certifi
from django.core.management.base import BaseCommand
from django.conf import settings
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging



class Command(BaseCommand):
    help = 'Sync local media files to S3 and update file URLs'

    def handle(self, *args, **kwargs):
        # Initialize the S3 client with the MinIO endpoint
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            use_ssl=True,
            verify=certifi.where(),
        )

        # Define local media directory and S3 bucket name
        local_media_dir = settings.MEDIA_ROOT
        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        # Set up logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

        def upload_file(local_path, s3_path):
            try:
                s3_client.upload_file(local_path, bucket_name, s3_path)
                logger.info(f'Successfully uploaded {s3_path}')
            except Exception as e:
                logger.error(f'Failed to upload {s3_path}: {str(e)}')

        # Gather all file paths
        files_to_upload = []
        for root, dirs, files in os.walk(local_media_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                relative_path = os.path.relpath(local_path, local_media_dir)
                s3_path = os.path.join(settings.AWS_PUBLIC_MEDIA_LOCATION, relative_path)
                files_to_upload.append((local_path, s3_path))

        # Upload files using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(upload_file, local_path, s3_path) for local_path, s3_path in files_to_upload]
            for future in as_completed(futures):
                future.result()  # This will re-raise any exceptions caught during upload

        logger.info('Media files have been synced to S3.')