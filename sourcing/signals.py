import asyncio

from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver

from home.models import Church, Pruning, Website, Parish
from scraping.services.parse_pruning_service import parse_pruning_for_website


@receiver(pre_save, sender=Church)
def church_pre_save(sender, instance, update_fields=None, **kwargs):
    instance._name_changed = False
    instance._city_changed = False
    if update_fields is None:
        # Full save - need to check against DB value
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            if old_instance.name != instance.name:
                instance._name_changed = True
            if old_instance.city != instance.city:
                instance._city_changed = True
        except sender.DoesNotExist:
            instance._name_changed = True
            instance._city_changed = True
    else:
        if 'name' in update_fields:
            instance._name_changed = True
        if 'city' in update_fields:
            instance._city_changed = True


@receiver(post_save, sender=Church)
def church_post_save(sender, instance, created, update_fields=None, **kwargs):
    if instance._name_changed or instance._city_changed:
        website = instance.parish.website
        if website:
            print(f'Church post_save signal triggered for church {instance.name},'
                  f' website {website.name}')
            transaction.on_commit(lambda: reparse_website(website))


@receiver(post_delete, sender=Church)
def church_post_delete(sender, instance, origin, **kwargs):
    if origin and isinstance(origin, Website) or isinstance(origin, Parish):
        print(f'Church post_delete signal triggered by {type(origin)}. Ignoring signal.')
        return

    website = instance.parish.website
    if website:
        print(f'Church post_delete signal triggered for church {instance.name},'
              f' website {website.name}')
        transaction.on_commit(lambda: reparse_website(website))


def reparse_website(website: Website):
    prunings = Pruning.objects.filter(scrapings__page__website=website).all()
    for pruning in prunings:
        with asyncio.Runner() as runner:
            runner.run(parse_pruning_for_website(pruning, website))
