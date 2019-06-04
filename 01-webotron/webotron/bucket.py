# -*- coding: utf-8 -*-

"""Moduel for s3 bucket management."""

from pathlib import Path
import mimetypes
from functools import reduce
import boto3

from botocore.exceptions import ClientError

from hashlib import md5

import util


class BucketManager:
    """Manage bucket."""

    CHUNK_SIZE = 8388608

    def __init__(self, session):
        """Create BucketManager object."""
        self.session = session
        self.s3 = session.resource('s3')
        self.manifest = {}
        self.transfer_config = boto3.s3.transfer.TransferConfig(
            multipart_chunksize=self.CHUNK_SIZE,
            multipart_threshold=self.CHUNK_SIZE
        )

    def all_buckets(self):
        """Iterator for all buckets."""
        return self.s3.buckets.all()

    def all_objects(self, bucket_name):
        """Iterator for all object in bucket."""
        return self.s3.Bucket(bucket_name).objects.all()

    def get_region_name(self, bucket):
        """Get bucket region"""
        bucket_location =  self.s3.meta.client.get_bucket_location(Bucket=bucket.name)
        return bucket_location['LocationConstraint'] or 'us-east-1'

    def bucket_url(self, bucket):
        """Returns bucket url"""
        return "http://{}.{}".format(bucket.name,
            util.get_endpoint(self.get_region_name(bucket)).host)


    def init_bucket(self, bucket_name):
        """Create and setup bucket."""

        s3_bucket = None
        try:
            s3_bucket = self.s3.create_bucket(
                Bucket=bucket_name
                # CreateBucketConfiguration={
                # 'LocationConstraint': SESSION.region_name
                # }
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                s3_bucket = self.s3.Bucket(bucket_name)
            else:
                raise e

        return s3_bucket


    def load_manifest(self, bucket):
        """Etag for the file to be uploaded"""
        paginator = self.s3.meta.client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket.name):
            for obj in page.get('Contents', []):
                self.manifest[obj['Key']] = obj['ETag']


    @staticmethod
    def hash_data(data):
        """Generate hash value for data"""
        hash = md5()
        hash.update(data)

        return hash


    def gen_etag(self, path):
        hashes = []

        with open(path, 'rb') as f:
            while True:
                data = f.read(self.CHUNK_SIZE)

                if not data:
                    break

                hashes.append(self.hash_data(data))

        if not hashes:
            return

        elif len(hashes) == 1:
            return '"{}"'.format(hashes[0].hexdigest())
        else:
            hash = self.hash_data(reduce(lambda x,y: x+y, (h.digest() for h in hashes)))
            return '"{}-{}"'.format(hash.hexdigest(), len(hashes))


    def upload_file(self, bucket, path, key):
        """Upload file in s3."""
        content_type = mimetypes.guess_type(key)[0] or 'text/plain'

        etag = self.gen_etag(path)
        if self.manifest.get(key, '') == etag:
            return

        return bucket.upload_file(
            path,
            key,
            ExtraArgs={
                'ContentType': content_type
            },
            Config=self.transfer_config
        )


    def set_policy(self, bucket):
        """Set public access policy on the bucket."""
        policy = """
        {
            "Version":"2012-10-17",
            "Statement":[{
                "Sid":"PublicReadGetObject",
                "Effect":"Allow",
                "Principal": "*",
                "Action":["s3:GetObject"],
                "Resource":["arn:aws:s3:::%s/*"
              ]
            }
          ]
        }
        """ % bucket.name

        policy = policy.strip()

        pol = bucket.Policy()
        pol.put(Policy=policy)


    def sync(self, pathname, bucket_name):
        """Sync content in the path/folder to bucket """
        bucket = self.s3.Bucket(bucket_name)
        self.load_manifest(bucket)

        root = Path(pathname).expanduser().resolve()

        def handle_directory(target):
            for i in target.iterdir():
                if i.is_dir():
                    handle_directory(i)
                if i.is_file():
                    self.upload_file(bucket, str(i), str(i.relative_to(root)))

        handle_directory(root)


    def configure_website(self, bucket):
        """Configure s3 website hosting for bucket."""
        bucket.Website().put(WebsiteConfiguration={
            'ErrorDocument': {
                'Key': 'error.html'
            },
            'IndexDocument': {
                'Suffix': 'index.html'
            }
        })
