from django.db import transaction
from django.db.models.signals import post_delete, pre_delete, pre_save, post_save
from django.dispatch import receiver

from attaching.models import Image, ImageModeration
from attaching.public_service import attaching_recognize_and_extract_image
from attaching.services.file_note_mirror_service import delete_image_mirror, \
    delete_image_moderation_mirror, mirror_image, mirror_image_moderation
from registry.models import Website
from scheduling.public_service import scheduling_init_scheduling


@receiver(pre_delete, sender=Image)
def image_pre_delete(sender, instance, origin, **kwargs):
    if origin and isinstance(origin, Website):
        print(f'Image pre_delete signal triggered by {type(origin)}. Ignoring signal.')
        return

    print(f'Image pre_delete signal triggered for image {instance.uuid} {instance.name},'
          f' website {instance.website.name}')
    transaction.on_commit(lambda: scheduling_init_scheduling(instance.website))


@receiver(pre_save, sender=Image)
def image_pre_save(sender, instance, update_fields=None, **kwargs):
    instance._human_html_changed = False
    if update_fields is None:
        # Full save - need to check against DB value
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.human_html != instance.human_html:
                instance._human_html_changed = True
        except sender.DoesNotExist:
            # we do not trigger any action on creation
            instance._human_html_changed = False
    else:
        if 'human_html' in update_fields:
            instance._human_html_changed = True


@receiver(post_save, sender=Image)
def image_post_save(sender, instance, created, update_fields=None, **kwargs):
    if instance._human_html_changed:
        print(f'Image post_save signal triggered for image {instance.uuid},'
              f' website {instance.website.name}')
        transaction.on_commit(lambda: attaching_recognize_and_extract_image(instance))


@receiver(post_save, sender=Image)
def image_post_save_mirror(sender, instance, **kwargs):
    mirror_image(instance)


@receiver(post_delete, sender=Image)
def image_post_delete_mirror(sender, instance, **kwargs):
    delete_image_mirror(instance)


@receiver(post_save, sender=ImageModeration)
def image_moderation_post_save_mirror(sender, instance, **kwargs):
    mirror_image_moderation(instance)


@receiver(post_delete, sender=ImageModeration)
def image_moderation_post_delete_mirror(sender, instance, **kwargs):
    delete_image_moderation_mirror(instance)
