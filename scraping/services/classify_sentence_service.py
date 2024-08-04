from home.models import Sentence, Classifier, Scraping, Pruning
from scraping.prune.models import Action
from scraping.prune.train_and_predict import TensorFlowModel
from scraping.prune.transform_sentence import get_transformer, TransformerInterface
from scraping.services.sentence_action_service import action_to_db_action

_classifier = None
_model = None


def get_classifier(transformer: TransformerInterface) -> Classifier:
    global _classifier
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
        _model = TensorFlowModel()
        _model.from_pickle(classifier.pickle)

    return _model


def classify_line(line_without_link: str
                  ) -> tuple[Action, Classifier, list, TransformerInterface]:
    # 1. Get transformer
    transformer = get_transformer()
    embedding = transformer.transform(line_without_link)

    # 2. Get classifier
    classifier = get_classifier(transformer)
    model = get_model(classifier)

    # 3. Predict action
    action = model.predict([embedding])[0]

    return action, classifier, embedding, transformer


def classify_sentence(line_without_link: str,
                      pruning: Pruning) -> Sentence:
    # Classify line
    action, classifier, embedding, transformer = classify_line(line_without_link)

    # Save sentence
    db_action = action_to_db_action(action)

    sentence = Sentence(
        line=line_without_link,
        action=db_action,
        source=Sentence.Source.ML,
        pruning=pruning,
        updated_by=None,
        classifier=classifier,
        embedding=embedding,
        transformer_name=transformer.get_name(),
    )
    sentence.save()

    return sentence
