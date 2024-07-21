from home.models import Sentence
from scraping.prune.models import Action


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