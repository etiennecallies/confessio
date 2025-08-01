import threading

from home.models import Sentence, Classifier, Pruning
from scraping.prune.models import Source
from scraping.prune.train_and_predict import TensorFlowModel
from scraping.prune.transform_sentence import get_transformer, TransformerInterface
from scraping.services.classifier_target_service import get_target_enum
from scraping.services.train_classifier_service import set_label
from scraping.utils.enum_utils import StringEnum

_classifier = {}
_classifier_lock = threading.Lock()
_model = {}
_model_lock = threading.Lock()


def get_classifier(transformer: TransformerInterface,
                   target: Classifier.Target
                   ) -> Classifier:
    global _classifier
    if _classifier.get(target, None) is None:
        with _classifier_lock:
            if _classifier.get(target, None) is None:
                try:
                    _classifier[target] = Classifier.objects \
                        .filter(status=Classifier.Status.PROD, target=target) \
                        .latest('updated_at')
                except Classifier.DoesNotExist:
                    raise ValueError(f"No classifier in production for target {target}")

                assert _classifier[target].transformer_name == transformer.get_name(), \
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
    classifier = get_classifier(transformer, target)
    model = get_model(classifier)

    # 3. Predict label
    label = model.predict([embedding])[0]

    return label, classifier, embedding, transformer


def classify_existing_sentence(sentence: Sentence, target: Classifier.Target
                               ) -> tuple[StringEnum, Classifier]:
    # 1. Get transformer
    transformer = get_transformer()
    if sentence.transformer_name != transformer.get_name():
        embedding = transformer.transform(sentence.line)
    else:
        embedding = sentence.embedding

    # 2. Get classifier
    classifier = get_classifier(transformer, target)
    model = get_model(classifier)

    # 3. Predict label
    label = model.predict([embedding])[0]

    return label, classifier


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

    # Save sentence
    sentence.save()

    return sentence
