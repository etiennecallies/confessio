from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from home.models import Website, Image
from scraping.services.page_service import check_for_orphan_prunings


@receiver(pre_delete, sender=Image)
def image_pre_delete(sender, instance, origin, **kwargs):
    if origin and isinstance(origin, Website):
        print(f'Image pre_delete signal triggered by {type(origin)}. Ignoring signal.')
        return

    prunings = instance.prunings.all()
    if prunings:
        print(f'Image pre_delete signal triggered for image {instance.uuid} {instance.name},'
              f' website {instance.website.name}')
        transaction.on_commit(lambda: check_for_orphan_prunings(prunings, instance.website))
    else:
        print(f'No prunings found for image {instance.uuid} {instance.name}. No action taken.')
