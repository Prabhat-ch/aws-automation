import boto3

session = boto3.Session(profile_name='pythonAutomation')
s3 = session.resource('s3')

if __name__ == '__main__':
    for bucket in s3.buckets.all():
        print(bucket)
