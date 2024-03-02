import os
import sys
import time
import boto3
import argparse
from botocore.exceptions import NoCredentialsError, ClientError

def create_bucket(s3_client, bucket_name):
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Bucket {bucket_name} created successfully.")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket {bucket_name} already owned by you.")
    except s3_client.exceptions.BucketAlreadyExists:
        print(f"Bucket {bucket_name} already exists.")
    except Exception as e:
        print(f"An error occurred when creating the bucket: {e}")
        sys.exit(1)

def sync_folder_to_bucket(s3_client, local_folder, bucket_name):
    for root, dirs, files in os.walk(local_folder):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_folder)
            s3_path = relative_path

            try:
                s3_client.upload_file(local_path, bucket_name, s3_path)
                print(f"File {local_path} uploaded to {s3_path} in bucket {bucket_name}.")
            except NoCredentialsError:
                print("Credentials not available.")
                sys.exit(1)
            except Exception as e:
                print(f"Failed to upload {local_path} to {s3_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Sync a local folder to an S3 bucket.")
    parser.add_argument("local_folder", help="Local folder to sync")
    parser.add_argument("access_key", help="S3 Access Key ID")
    parser.add_argument("secret_key", help="S3 Secret Access Key")
    parser.add_argument("endpoint_url", help="S3 Endpoint URL")
    parser.add_argument("bucket_name", help="S3 Bucket Name", default="book", nargs="?")

    args = parser.parse_args()

    session = boto3.session.Session()
    s3_client = session.client(
        service_name='s3',
        aws_access_key_id=args.access_key,
        aws_secret_access_key=args.secret_key,
        endpoint_url=args.endpoint_url
    )

    # Check if the bucket exists, if not, create it
    try:
        s3_client.head_bucket(Bucket=args.bucket_name)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            create_bucket(s3_client, args.bucket_name)
        else:
            print(f"An error occurred: {e}")
            sys.exit(1)

    while True:
        sync_folder_to_bucket(s3_client, args.local_folder, args.bucket_name)
        print(f"Next sync in 5 minutes...")
        time.sleep(300)  # Sleep for 5 minutes


if __name__ == "__main__":
    main()