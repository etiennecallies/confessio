from sklearn.model_selection import train_test_split

from home.models import Sentence, Classifier
from scraping.prune.models import Source, Action
from scraping.prune.train_and_predict import TensorFlowModel, evaluate
from scraping.services.classifier_target_service import get_target_enum
from scraping.utils.enum_utils import StringEnum


def build_sentence_dataset(target: Classifier.Target) -> list[Sentence]:
    if target == Classifier.Target.ACTION:
        return Sentence.objects.filter(source=Source.HUMAN).all()

    raise NotImplementedError(f'Target {target} is not supported for sentence dataset building')


def extract_label(sentence: Sentence, target: Classifier.Target) -> StringEnum:
    if target == Classifier.Target.ACTION:
        return Action(sentence.action)

    raise NotImplementedError(f'Target {target} is not supported for label extraction')


def train_classifier(sentence_dataset: list[Sentence], target: Classifier.Target) -> Classifier:
    if not sentence_dataset:
        raise ValueError("No sentence dataset to train classifier")

    first_transformer_name = sentence_dataset[0].transformer_name
    assert all([s.transformer_name == first_transformer_name for s in sentence_dataset]), \
        "All sentences must have the same transformer"

    # Get embeddings and labels
    embeddings = [sentence.embedding for sentence in sentence_dataset]
    labels = [extract_label(sentence, target) for sentence in sentence_dataset]

    # Split dataset
    test_size = 800
    embeddings_train, embeddings_test, \
        labels_train, labels_test, \
        = train_test_split(embeddings, labels, test_size=test_size,
                           # random_state=41
                           )

    # Train model
    model = TensorFlowModel[Action](Action.list_items())
    model.fit(embeddings_train, labels_train)

    # Evaluate model
    accuracy = evaluate(model, embeddings_test, labels_test)

    # Save classifier
    classifier = Classifier(
        transformer_name=first_transformer_name,
        pickle=model.to_pickle(),
        status=Classifier.Status.DRAFT,
        target=target,
        different_labels=get_target_enum(target).list_items(),
        accuracy=accuracy,
        test_size=test_size,
    )
    classifier.save()

    return classifier
