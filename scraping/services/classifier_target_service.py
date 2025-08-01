from typing import Type

from home.models import Classifier
from scraping.extract_v2.models import EventMotion
from scraping.prune.models import Action
from scraping.utils.enum_utils import StringEnum, BooleanStringEnum


def get_target_enum(target: Classifier.Target) -> Type[StringEnum]:
    if target == Classifier.Target.ACTION:
        return Action

    if target == Classifier.Target.SPECIFIER:
        return BooleanStringEnum

    if target == Classifier.Target.SCHEDULE:
        return BooleanStringEnum

    if target == Classifier.Target.CONFESSION:
        return EventMotion

    raise NotImplementedError(f'Target {target} is not supported for different labels extraction')
