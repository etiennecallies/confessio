from typing import Type

from home.models import Classifier
from scraping.extract_v2.models import EventMotion, Temporal, EventMention
from scraping.prune.models import Action
from scraping.utils.enum_utils import StringEnum


def get_target_enum(target: Classifier.Target) -> Type[StringEnum]:
    if target == Classifier.Target.ACTION:
        return Action

    if target == Classifier.Target.TEMPORAL:
        return Temporal

    if target == Classifier.Target.CONFESSION_LEGACY:
        return EventMotion

    if target == Classifier.Target.CONFESSION:
        return EventMention

    raise NotImplementedError(f'Target {target} is not supported for different labels extraction')
