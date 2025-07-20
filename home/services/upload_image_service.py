import boto3
from django.conf import settings
from django.urls import reverse

from home.models import Website, Image
from home.services.admin_email_service import send_email_to_admin
from home.utils.web_utils import get_user_user_agent_and_ip


def upload_image(document, website: Website, request) -> tuple[bool, str | None]:
    # Generate unique filename
    image_name = document.name.replace(' ', '_').replace('/', '_')
    comment = request.POST.get('comment', None)
    user, user_agent, ip_address_hash = get_user_user_agent_and_ip(request)

    image = Image(
        website=website,
        name=image_name,
        comment=comment,
        user=user,
        user_agent=user_agent,
        ip_address_hash=ip_address_hash,
    )
    image.save()
    unique_filename = f"{image.uuid}/{image_name}"

    s3_success = upload_to_s3(document, unique_filename)
    if s3_success:
        print(f'Document uploaded successfully! unique_filename: {unique_filename}')

        if not user:
            website_url = request.build_absolute_uri(
                reverse('website_view', kwargs={'website_uuid': website.uuid})
            )
            email_body = (f"New image on website {website.name}\n"
                          f"url: {website_url}\n"
                          f"\n\ncomment:\n{comment}")
            subject = f'New image on confessio for {website.name}'
            send_email_to_admin(subject, email_body)

        return True, None

    image.delete()

    return False, 'Une erreur est survenue lors du chargement du fichier.'


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
