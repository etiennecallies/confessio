from home.models import Sentence


def build_sentence_dataset() -> list[Sentence]:
    return Sentence.objects.filter(source=Sentence.Source.HUMAN).all()
