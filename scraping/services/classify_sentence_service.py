import threading

from home.models import Sentence, Classifier, Pruning
from scraping.prune.models import Action, Source
from scraping.prune.train_and_predict import TensorFlowModel
from scraping.prune.transform_sentence import get_transformer, TransformerInterface

_classifier = None
_classifier_lock = threading.Lock()
_model = None
_model_lock = threading.Lock()


def get_classifier(transformer: TransformerInterface) -> Classifier:
    global _classifier
    if _classifier is None:
        with _classifier_lock:
            if _classifier is None:
                try:
                    _classifier = Classifier.objects \
                        .filter(status=Classifier.Status.PROD) \
                        .latest('updated_at')
                except Classifier.DoesNotExist:
                    raise ValueError("No classifier in production")

                assert _classifier.transformer_name == transformer.get_name(), \
                    "Classifier and transformer are not compatible"

    return _classifier


def get_model(classifier: Classifier) -> TensorFlowModel:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                different_labels = Action.list_items()
                assert classifier.different_labels == different_labels, \
                    "Classifier and model are not compatible"
                tmp_model = TensorFlowModel[Action](different_labels)
                tmp_model.from_pickle(classifier.pickle)
                _model = tmp_model

    return _model


def classify_line(stringified_line: str
                  ) -> tuple[Action, Classifier, list, TransformerInterface]:
    # 1. Get transformer
    transformer = get_transformer()
    embedding = transformer.transform(stringified_line)

    # 2. Get classifier
    classifier = get_classifier(transformer)
    model = get_model(classifier)

    # 3. Predict action
    action = model.predict([embedding])[0]

    return action, classifier, embedding, transformer


def classify_existing_sentence(sentence: Sentence) -> Action:
    # 1. Get transformer
    transformer = get_transformer()
    if sentence.transformer_name != transformer.get_name():
        embedding = transformer.transform(sentence.line)
    else:
        embedding = sentence.embedding

    # 2. Get classifier
    classifier = get_classifier(transformer)
    model = get_model(classifier)

    # 3. Predict action
    action = model.predict([embedding])[0]

    return action


def classify_and_create_sentence(stringified_line: str,
                                 pruning: Pruning) -> Sentence:
    # Classify line
    action, classifier, embedding, transformer = classify_line(stringified_line)

    # Save sentence
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
    sentence.save()

    return sentence
