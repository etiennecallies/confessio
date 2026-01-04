from django.db import transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from home.models import Website, Image
from scheduling.process import init_scheduling


@receiver(pre_delete, sender=Image)
def image_pre_delete(sender, instance, origin, **kwargs):
    if origin and isinstance(origin, Website):
        print(f'Image pre_delete signal triggered by {type(origin)}. Ignoring signal.')
        return

    print(f'Image pre_delete signal triggered for image {instance.uuid} {instance.name},'
          f' website {instance.website.name}')
    transaction.on_commit(lambda: init_scheduling(instance.website))
