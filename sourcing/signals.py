from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from home.models import Church, Website, Parish
from scheduling.process import init_scheduling


@receiver(pre_save, sender=Church)
def church_pre_save(sender, instance, update_fields=None, **kwargs):
    instance._name_changed = False
    instance._city_changed = False
    instance._old_parish_id = None
    if update_fields is None:
        # Full save - need to check against DB value
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.name != instance.name:
                instance._name_changed = True
            if old_instance.city != instance.city:
                instance._city_changed = True
            if old_instance.parish_id != instance.parish_id:
                instance._old_parish_id = old_instance.parish_id
        except sender.DoesNotExist:
            instance._name_changed = True
            instance._city_changed = True
    else:
        if 'name' in update_fields:
            instance._name_changed = True
        if 'city' in update_fields:
            instance._city_changed = True
        if 'parish' in update_fields or 'parish_id' in update_fields:
            instance._old_parish_id = sender.objects.get(pk=instance.pk).parish_id


@receiver(post_save, sender=Church)
def church_post_save(sender, instance, created, update_fields=None, **kwargs):
    if instance._old_parish_id is not None:
        old_parish = Parish.objects.filter(uuid=instance._old_parish_id).first()
        old_website = old_parish.website if old_parish else None
        new_website = instance.parish.website
        print(f'Church post_save signal triggered for church {instance.name},'
              f' {old_website=}, {new_website=}')

        if old_website and new_website and old_website.uuid != new_website.uuid:
            print(f'website differs, reinitializing scheduling for both websites,'
                  f' deindexing old website')
            transaction.on_commit(lambda:
                                  init_scheduling(old_website, instant_deindex=True)
                                  and init_scheduling(new_website))
        elif old_website or new_website:
            transaction.on_commit(lambda: init_scheduling(old_website or new_website))
        return

    if instance._name_changed or instance._city_changed:
        website = instance.parish.website
        if website:
            print(f'Church post_save signal triggered for church {instance.name},'
                  f' website {website.name}')
            transaction.on_commit(lambda: init_scheduling(website))


@receiver(post_delete, sender=Church)
def church_post_delete(sender, instance, origin, **kwargs):
    if origin and isinstance(origin, Website) or isinstance(origin, Parish):
        print(f'Church post_delete signal triggered by {type(origin)}. Ignoring signal.')
        return

    website = instance.parish.website
    if website:
        print(f'Church post_delete signal triggered for church {instance.name},'
              f' website {website.name}')
        transaction.on_commit(lambda: init_scheduling(website))
