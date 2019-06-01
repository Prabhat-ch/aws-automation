import boto3
import click
from botocore.exceptions import ClientError
from pathlib import Path
import mimetypes

session = boto3.Session(profile_name='pythonAutomation')
s3 = session.resource('s3')

@click.group()
def cli():
    "Webotron deploys website to aws"
    pass

@cli.command('list-buckets')
def list_buckets():
    "list all the account in the account"
    for bucket in s3.buckets.all():
        print(bucket)

@cli.command('list-bucket-objects')
def list_bucket_objects(bucket):
    for object in s3.bucket.objects.all():
        print(object)

@cli.command('setup-bucket')
@click.argument('bucket')
def setup_bucket(bucket):
    "Create and setup bucket"

    s3_bucket = None
    try:
        s3_bucket = s3.create_bucket(
            Bucket=bucket
            # CreateBucketConfiguration={'LocationConstraint': session.region_name}
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            s3_bucket = s3.Bucket(bucket)
        else:
            raise e


    # # s3_bucket = s3.create_bucket(
    # #     Bucket=bucket,
    # #     CreateBucketConfiguration={'LocationConstraint': session.region_name}
    # #     )
    # s3_bucket = s3.create_bucket(Bucket=bucket)

    policy = """{
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
    """ %s3_bucket.name

    policy = policy.strip()

    pol = s3_bucket.Policy()
    pol.put(Policy = policy)

    ws = s3_bucket.Website()
    ws.put(WebsiteConfiguration={
        'ErrorDocument': {
            'Key': 'error.html'
        },
        'IndexDocument': {
            'Suffix': 'index.html'
        }
        }
    )

    return


def upload_file(s3_bucket, path, key):
    content_type = mimetypes.guess_type(key)[0] or 'text/plain'
    s3_bucket.upload_file(
        path,
        key,
        ExtraArgs={
            'ContentType': 'text/html'
        }
    )

@cli.command('sync')
@click.argument('pathname', type=click.Path(exists=True))
@click.argument('bucket')
def sync(pathname, bucket):
    "Sync contents of pathname to bucket"

    s3_bucket = s3.Bucket(bucket)

    root = Path(pathname).expanduser().resolve()

    def handle_directory(target):
         for i in target.iterdir():
             if i.is_dir(): handle_directory(i)
             if i.is_file(): upload_file(s3_bucket, str(i), str(i.relative_to(root)))

    handle_directory(root)



if __name__ == '__main__':
    cli()
