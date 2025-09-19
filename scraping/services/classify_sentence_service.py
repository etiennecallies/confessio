import threading

from home.models import Sentence, Classifier, Pruning
from scraping.extract_v2.models import EventMotion
from scraping.prune.models import Source, Action
from scraping.prune.train_and_predict import TensorFlowModel
from scraping.prune.transform_sentence import get_transformer, TransformerInterface, \
    TRANSFORMER_NAME
from scraping.services.classifier_target_service import get_target_enum
from scraping.services.train_classifier_service import set_label
from scraping.utils.enum_utils import StringEnum, BooleanStringEnum

_classifier = {}
_classifier_lock = threading.Lock()
_model = {}
_model_lock = threading.Lock()


def get_classifier(target: Classifier.Target
                   ) -> Classifier:
    global _classifier
    if _classifier.get(target, None) is None:
        with _classifier_lock:
            if _classifier.get(target, None) is None:
                print(f'Loading classifier for target {target}...')
                try:
                    _classifier[target] = Classifier.objects \
                        .filter(status=Classifier.Status.PROD, target=target) \
                        .latest('updated_at')
                except Classifier.DoesNotExist:
                    raise ValueError(f"No classifier in production for target {target}")

                assert _classifier[target].transformer_name == TRANSFORMER_NAME, \
                    "Classifier and transformer are not compatible"

    return _classifier[target]


def get_model(classifier: Classifier) -> TensorFlowModel:
    global _model

    target = Classifier.Target(classifier.target)
    if _model.get(target, None) is None:
        with _model_lock:
            if _model.get(target, None) is None:
                target_enum = get_target_enum(target)
                different_labels = target_enum.list_items()
                assert classifier.different_labels == different_labels, \
                    "Classifier and model are not compatible"
                tmp_model = TensorFlowModel[target_enum](different_labels)
                tmp_model.from_pickle(classifier.pickle)
                _model[target] = tmp_model

    return _model[target]


def classify_line(stringified_line: str, target: Classifier.Target
                  ) -> tuple[StringEnum, Classifier, list, TransformerInterface]:
    # 1. Get transformer
    transformer = get_transformer()
    embedding = transformer.transform(stringified_line)

    # 2. Get classifier
    classifier = get_classifier(target)
    model = get_model(classifier)

    # 3. Predict label
    label = model.predict([embedding])[0]

    return label, classifier, embedding, transformer


def classify_existing_sentence(sentence: Sentence, target: Classifier.Target
                               ) -> tuple[StringEnum, Classifier]:
    labels, classifier = classify_existing_sentences([sentence], target)

    return labels[0], classifier


def classify_existing_sentences(sentences: list[Sentence], target: Classifier.Target
                                ) -> tuple[list[StringEnum], Classifier]:
    # 1. Get transformer
    transformer = get_transformer()
    embeddings = []
    for sentence in sentences:
        if sentence.transformer_name != transformer.get_name():
            embeddings.append(transformer.transform(sentence.line))
        else:
            embeddings.append(sentence.embedding)

    # 2. Get classifier
    classifier = get_classifier(target)
    model = get_model(classifier)

    # 3. Predict label
    labels = model.predict(embeddings)

    return labels, classifier


def get_ml_label(sentence: Sentence, target: Classifier.Target) -> StringEnum:
    classifier = get_classifier(target)

    assert target == classifier.target, \
        f"Target {target} does not match classifier target {classifier.target}"

    if target == Classifier.Target.ACTION:
        if sentence.source == Source.ML and sentence.classifier_id == classifier.uuid:
            return Action(sentence.action)
    elif target == Classifier.Target.SPECIFIER:
        if sentence.specifier_classifier_id == classifier.uuid:
            return BooleanStringEnum.from_bool(sentence.ml_specifier)
    elif target == Classifier.Target.SCHEDULE:
        if sentence.schedule_classifier_id == classifier.uuid:
            return BooleanStringEnum.from_bool(sentence.ml_schedule)
    elif target == Classifier.Target.CONFESSION:
        if sentence.confession_classifier_id == classifier.uuid:
            return EventMotion(sentence.ml_confession)
    else:
        raise NotImplementedError(f'Target {target} is not supported for label extraction')

    ml_label, _ = classify_existing_sentence(sentence, target)
    if not (target == Classifier.Target.ACTION and sentence.source == Source.HUMAN):
        set_label(sentence, ml_label, classifier)
        sentence.save()

    return ml_label


def get_sentences_with_wrong_classifier(target: Classifier.Target) -> list[Sentence]:
    classifier = get_classifier(target)

    sentence_query = Sentence.objects

    if target == Classifier.Target.ACTION:
        sentence_query = sentence_query.filter(source=Source.ML).exclude(classifier=classifier)
    if target == Classifier.Target.SCHEDULE:
        sentence_query = sentence_query.exclude(schedule_classifier=classifier)
    if target == Classifier.Target.SPECIFIER:
        sentence_query = sentence_query.exclude(specifier_classifier=classifier)
    if target == Classifier.Target.CONFESSION:
        sentence_query = sentence_query.exclude(confession_classifier=classifier)

    return sentence_query.all()


def classify_and_create_sentence(stringified_line: str,
                                 pruning: Pruning) -> Sentence:
    # Classify line
    action, classifier, embedding, transformer = classify_line(stringified_line,
                                                               Classifier.Target.ACTION)

    # Init sentence with v1 labels
    sentence = Sentence(
        line=stringified_line,
        action=action,
        source=Source.ML,
        updated_on_pruning=pruning,
        updated_by=None,
        classifier=classifier,
        embedding=embedding,
        transformer_name=transformer.get_name(),
    )

    # V2 labels
    ml_specifier, specifier_classifier = classify_existing_sentence(
        sentence, Classifier.Target.SPECIFIER)
    set_label(sentence, ml_specifier, specifier_classifier)
    ml_schedule, schedule_classifier = classify_existing_sentence(sentence,
                                                                  Classifier.Target.SCHEDULE)
    set_label(sentence, ml_schedule, schedule_classifier)
    ml_confession, confession_classifier = classify_existing_sentence(sentence,
                                                                      Classifier.Target.CONFESSION)
    set_label(sentence, ml_confession, confession_classifier)

    try:
        # In the meantime, a sentence with the same line could have been created
        return Sentence.objects.get(line=stringified_line)
    except Sentence.DoesNotExist:
        # Save sentence
        sentence.save()

        return sentence
