from django.db.models import Q
from sklearn.model_selection import train_test_split

from scheduling.models.pruning_models import Classifier, Sentence
from scheduling.workflows.pruning.extract_v2.models import Temporal, EventMention
from scheduling.workflows.pruning.models import Source, Action
from scheduling.workflows.pruning.train_and_predict import TensorFlowModel, evaluate
from scheduling.services.classifier_target_service import get_target_enum
from scraping.utils.enum_utils import StringEnum

MIN_DATASET_SIZE = 300


def build_sentence_dataset(target: Classifier.Target) -> list[Sentence]:
    if target == Classifier.Target.ACTION:
        return Sentence.objects.filter(source=Source.HUMAN).all()
    if target == Classifier.Target.TEMPORAL:
        human_qualified_dataset = Sentence.objects.filter(human_temporal__isnull=False).all()
        if len(human_qualified_dataset) >= MIN_DATASET_SIZE:
            return human_qualified_dataset

        print(f"Not enough human temporal sentences ({len(human_qualified_dataset)}), "
              f"using ML temporal sentences instead")
        return Sentence.objects.filter(Q(human_temporal__isnull=False)
                                       | Q(ml_temporal__isnull=False)).all()

    if target == Classifier.Target.CONFESSION:
        human_qualified_dataset = Sentence.objects.filter(
            human_confession__isnull=False).all()
        if len(human_qualified_dataset) >= MIN_DATASET_SIZE:
            return human_qualified_dataset

        print(f"Not enough human confession sentences ({len(human_qualified_dataset)}), "
              f"using ML confession sentences instead")
        return Sentence.objects.filter(Q(human_confession__isnull=False)
                                       | Q(ml_confession__isnull=False)).all()

    raise NotImplementedError(f'Target {target} is not supported for sentence dataset building')


def extract_label(sentence: Sentence, target: Classifier.Target) -> StringEnum:
    if target == Classifier.Target.ACTION:
        return Action(sentence.action)

    if target == Classifier.Target.TEMPORAL:
        if sentence.human_temporal is not None:
            return Temporal(sentence.human_temporal)
        if sentence.ml_temporal is not None:
            return Temporal(sentence.ml_temporal)
        raise ValueError(f'Sentence {sentence.uuid} has no temporal for target {target}')

    if target == Classifier.Target.CONFESSION:
        if sentence.human_confession is not None:
            return EventMention(sentence.human_confession)
        if sentence.ml_confession is not None:
            return EventMention(sentence.ml_confession)
        raise ValueError(f'Sentence {sentence.uuid} has no confession for target {target}')

    raise NotImplementedError(f'Target {target} is not supported for label extraction')


def set_label(sentence: Sentence, label: StringEnum, classifier: Classifier) -> None:
    if classifier.target == Classifier.Target.ACTION:
        sentence.action = label
        sentence.classifier = classifier
        return

    if classifier.target == Classifier.Target.TEMPORAL:
        sentence.ml_temporal = label
        sentence.temporal_classifier = classifier
        return

    if classifier.target == Classifier.Target.CONFESSION:
        sentence.ml_confession = label
        sentence.confession_new_classifier = classifier
        return

    raise NotImplementedError(f'Target {classifier.target} is not supported for label setting')


def get_test_size(dataset_size: int) -> int:
    assert dataset_size >= MIN_DATASET_SIZE

    third_size = dataset_size // 3
    test_size = 100
    while 2 * test_size < third_size:
        test_size *= 2

    return test_size


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
    test_size = get_test_size(len(sentence_dataset))
    print(f"Dataset size: {len(sentence_dataset)}, test size: {test_size}")
    embeddings_train, embeddings_test, \
        labels_train, labels_test, \
        = train_test_split(embeddings, labels, test_size=test_size,
                           # random_state=41
                           )

    # Train model
    target_enum = get_target_enum(target)
    different_labels = target_enum.list_items()
    model = TensorFlowModel[target_enum](different_labels)
    model.fit(embeddings_train, labels_train)

    # Evaluate model
    accuracy = evaluate(model, embeddings_test, labels_test)

    # Save classifier
    classifier = Classifier(
        transformer_name=first_transformer_name,
        pickle=model.to_pickle(),
        status=Classifier.Status.DRAFT,
        target=target,
        different_labels=different_labels,
        accuracy=accuracy,
        test_size=test_size,
    )
    classifier.save()

    return classifier
