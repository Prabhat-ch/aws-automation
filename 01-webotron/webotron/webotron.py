import boto3
import click
from botocore.exceptions import ClientError

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
            Bucket=bucket,
            CreateBucketConfiguration={'LocationConstraint': session.region_name}
        )
    except botocore.exceptions.ClientError as e:
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


if __name__ == '__main__':
    cli()
