from home.models import Sentence
from scraping.prune.models import Action, Source


def action_to_db_action(action: Action) -> Sentence.Action:
    return {
        Action.SHOW: Sentence.Action.SHOW,
        Action.HIDE: Sentence.Action.HIDE,
        Action.STOP: Sentence.Action.STOP,
    }[action]


def get_sentence_action(sentence: Sentence) -> Action:
    db_action = sentence.action

    return {
        Sentence.Action.SHOW.value: Action.SHOW,
        Sentence.Action.HIDE.value: Action.HIDE,
        Sentence.Action.STOP.value: Action.STOP,
    }[db_action]


def get_sentence_source(sentence: Sentence) -> Source:
    db_source = sentence.source

    return {
        Sentence.Source.HUMAN.value: Source.HUMAN,
        Sentence.Source.ML.value: Source.ML,
    }[db_source]
