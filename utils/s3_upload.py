import os
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app
from werkzeug.utils import secure_filename


def upload_file_to_s3(file_obj, username):
    bucket_name = current_app.config.get("AWS_S3_BUCKET") or os.getenv("AWS_S3_BUCKET")
    region = current_app.config.get("AWS_REGION") or os.getenv("AWS_REGION", "ap-south-1")
    object_prefix = current_app.config.get("AWS_S3_OBJECT_PREFIX", "task_uploads")
    use_acl = bool(current_app.config.get("AWS_S3_USE_ACL", False))
    acl_name = current_app.config.get("AWS_S3_ACL", "public-read")
    custom_domain = current_app.config.get("AWS_S3_CUSTOM_DOMAIN", "")

    if not bucket_name:
        current_app.logger.warning("AWS_S3_BUCKET missing, skipping upload")
        return None

    access_key = current_app.config.get("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = current_app.config.get("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    # random filename so clashes are less likely
    safe_name = secure_filename(file_obj.filename or "")
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else "dat"
    safe_username = secure_filename(username or "user")
    s3_key = f"{object_prefix}/{safe_username}/{uuid.uuid4()}.{ext}"
    extra_args = {}
    if file_obj.mimetype:
        extra_args["ContentType"] = file_obj.mimetype
    if use_acl and acl_name:
        extra_args["ACL"] = acl_name

    try:
        if extra_args:
            s3_client.upload_fileobj(file_obj, bucket_name, s3_key, ExtraArgs=extra_args)
        else:
            s3_client.upload_fileobj(file_obj, bucket_name, s3_key)
        if custom_domain:
            file_url = f"https://{custom_domain}/{s3_key}"
        elif region == "us-east-1":
            file_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        else:
            file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"
        current_app.logger.info("file uploaded to s3: %s", file_url)
        return file_url
    except NoCredentialsError:
        current_app.logger.error("AWS credentials not found")
        return None
    except ClientError as e:
        current_app.logger.error("S3 upload failed: %s", e)
        return None
