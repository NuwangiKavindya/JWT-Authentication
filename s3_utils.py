import os
import boto3
from dotenv import load_dotenv
from fastapi import UploadFile

load_dotenv()

AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = "nuwangi-learning-img"

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION
)

def upload_file_to_s3(file: UploadFile):
    try:
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            file.filename,
            ExtraArgs={"ContentType": file.content_type}
        )
        
        file_url = f"https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/{file.filename}"
        return file_url
        
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None