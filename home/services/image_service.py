import boto3
from django.conf import settings

from home.models import Website, Image


def upload_image(document, website: Website, comment: str) -> tuple[bool, str | None]:
    # Generate unique filename
    image = Image(
        website=website,
        name=document.name,
        comment=comment,
    )
    image.save()
    unique_filename = f"{image.uuid}/{document.name}"

    s3_success = upload_to_s3(document, unique_filename)
    if s3_success:
        print(f'Document uploaded successfully! URL: {unique_filename}')
        return True, None

    image.delete()

    return False, 'Failed to upload document to S3.'


def upload_to_s3(file, filename) -> bool:
    """Upload file to S3 bucket"""
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    try:
        # Upload file to S3
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            filename,
        )

        return True
    except Exception as e:
        print(e)
        return False


def get_image_public_url(image: Image) -> str:
    """Get the public URL of an image stored in S3."""
    host = f"{settings.AWS_STORAGE_BUCKET_NAME}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com"
    return f"https://{host}/{image.uuid}/{image.name}"
