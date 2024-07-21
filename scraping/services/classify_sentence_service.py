from typing import Optional

from home.models import Sentence, Classifier, Scraping
from scraping.prune.train_and_predict import TensorFlowModel
from scraping.prune.transform_sentence import get_transformer
from scraping.services.sentence_action_service import action_to_db_action


def classify_sentence(line_without_link: str,
                      scraping: Optional[Scraping]) -> Sentence:
    # 1. Get transformer
    transformer = get_transformer()
    embedding = transformer.transform(line_without_link)

    # 2. Get classifier
    try:
        classifier = Classifier.objects \
            .filter(status=Classifier.Status.PROD) \
            .latest('updated_at')
    except Classifier.DoesNotExist:
        raise ValueError("No classifier in production")

    assert classifier.transformer_name == transformer.get_name(), \
        "Classifier and transformer are not compatible"

    model = TensorFlowModel()
    model.from_pickle(classifier.pickle)

    # 3. Predict action
    action = model.predict([embedding])[0]

    # 4. Save sentence
    db_action = action_to_db_action(action)

    sentence = Sentence(
        line=line_without_link,
        action=db_action,
        source=Sentence.Source.ML,
        scraping=scraping,
        updated_by=None,
        classifier=classifier,
        embedding=embedding,
        transformer_name=transformer.get_name(),
    )
    sentence.save()

    return sentence
