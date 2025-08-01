from django.db.models import Q
from sklearn.model_selection import train_test_split

from home.models import Sentence, Classifier
from scraping.extract_v2.models import EventMotion
from scraping.prune.models import Source, Action
from scraping.prune.train_and_predict import TensorFlowModel, evaluate
from scraping.services.classifier_target_service import get_target_enum
from scraping.utils.enum_utils import StringEnum, BooleanStringEnum


def build_sentence_dataset(target: Classifier.Target) -> list[Sentence]:
    if target == Classifier.Target.ACTION:
        return Sentence.objects.filter(source=Source.HUMAN).all()
    if target == Classifier.Target.SPECIFIER:
        human_qualified_dataset = Sentence.objects.filter(human_specifier__isnull=False).all()
        if len(human_qualified_dataset) > 200:
            return human_qualified_dataset

        print(f"Not enough human specifier sentences ({len(human_qualified_dataset)}), "
              f"using ML specifier sentences instead")
        return Sentence.objects.filter(Q(human_specifier__isnull=False)
                                       | Q(ml_specifier__isnull=False)).all()

    if target == Classifier.Target.SCHEDULE:
        human_qualified_dataset = Sentence.objects.filter(human_schedule__isnull=False).all()
        if len(human_qualified_dataset) > 200:
            return human_qualified_dataset

        print(f"Not enough human schedule sentences ({len(human_qualified_dataset)}), "
              f"using ML schedule sentences instead")
        return Sentence.objects.filter(Q(human_schedule__isnull=False)
                                       | Q(ml_schedule__isnull=False)).all()

    if target == Classifier.Target.CONFESSION:
        human_qualified_dataset = Sentence.objects.filter(human_confession__isnull=False).all()
        if len(human_qualified_dataset) > 200:
            return human_qualified_dataset

        print(f"Not enough human confession sentences ({len(human_qualified_dataset)}), "
              f"using ML confession sentences instead")
        return Sentence.objects.filter(Q(human_confession__isnull=False)
                                       | Q(ml_confession__isnull=False)).all()

    raise NotImplementedError(f'Target {target} is not supported for sentence dataset building')


def extract_label(sentence: Sentence, target: Classifier.Target) -> StringEnum:
    if target == Classifier.Target.ACTION:
        return Action(sentence.action)

    if target == Classifier.Target.SPECIFIER:
        if sentence.human_specifier is not None:
            return BooleanStringEnum.from_bool(sentence.human_specifier)
        if sentence.ml_specifier is not None:
            return BooleanStringEnum.from_bool(sentence.ml_specifier)
        raise ValueError(f'Sentence {sentence.uuid} has no specifier for target {target}')

    if target == Classifier.Target.SCHEDULE:
        if sentence.human_schedule is not None:
            return BooleanStringEnum.from_bool(sentence.human_schedule)
        if sentence.ml_schedule is not None:
            return BooleanStringEnum.from_bool(sentence.ml_schedule)
        raise ValueError(f'Sentence {sentence.uuid} has no schedule for target {target}')

    if target == Classifier.Target.CONFESSION:
        if sentence.human_confession is not None:
            return EventMotion(sentence.human_confession)
        if sentence.ml_confession is not None:
            return EventMotion(sentence.ml_confession)
        raise ValueError(f'Sentence {sentence.uuid} has no confession for target {target}')

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
