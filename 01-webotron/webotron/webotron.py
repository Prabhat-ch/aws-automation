# /user/bin/python
# -*- coding: utf-8 -*-

"""
Webotron: Deploys static website in AWS.

Webotron features include:
- Creating and configuring s3 list_buckets
- Syncing folder to the s3 buckets
- configuring route53
"""


import boto3
import click

from bucket import BucketManager

SESSION = None
bucket_manager = None


@click.group()
@click.option('--profile', default=None, help='Use a given AWS profile.')
def cli(profile):
    """Webotron deploys website to aws"""

    global SESSION, bucket_manager
    session_cfg = {};
    if profile:
        session_cfg['profile_name'] = profile

    SESSION = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(SESSION)


@cli.command('list-buckets')
def list_buckets():
    """List all the buckets in the account."""
    for bucket in bucket_manager.all_buckets():
        print(bucket)


@cli.command('list-bucket-objects')
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List all the objects in the bucket."""
    for object in bucket_manager.all_objects(bucket):
        print(object)


@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    """Initialize the bucket, set public policy and configure it to host static website."""
    s3_bucket = bucket_manager.init_bucket(bucket)
    bucket_manager.set_policy(s3_bucket)
    bucket_manager.configure_website(s3_bucket)


@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    """Sync contents of pathname to bucket."""
    bucket_manager.sync(pathname, bucket)
    print(bucket_manager.bucket_url(bucket_manager.s3.Bucket(bucket)))


if __name__ == '__main__':
    cli()
