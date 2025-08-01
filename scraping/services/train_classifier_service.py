from sklearn.model_selection import train_test_split

from home.models import Sentence, Classifier
from scraping.prune.models import Source, Action
from scraping.prune.train_and_predict import TensorFlowModel, evaluate


def build_sentence_dataset() -> list[Sentence]:
    return Sentence.objects.filter(source=Source.HUMAN).all()


def train_classifier(sentence_dataset: list[Sentence]) -> Classifier:
    if not sentence_dataset:
        raise ValueError("No sentence dataset to train classifier")

    first_transformer_name = sentence_dataset[0].transformer_name
    assert all([s.transformer_name == first_transformer_name for s in sentence_dataset]), \
        "All sentences must have the same transformer"

    # Get embeddings and actions
    embeddings = [sentence.embedding for sentence in sentence_dataset]
    actions = [Action(sentence.action) for sentence in sentence_dataset]

    # Split dataset
    test_size = 800
    embeddings_train, embeddings_test, \
        actions_train, actions_test, \
        = train_test_split(embeddings, actions, test_size=test_size,
                           # random_state=41
                           )

    # Train model
    model = TensorFlowModel[Action](Action.list_items())
    model.fit(embeddings_train, actions_train)

    # Evaluate model
    accuracy = evaluate(model, embeddings_test, actions_test)

    # Save classifier
    classifier = Classifier(
        transformer_name=first_transformer_name,
        pickle=model.to_pickle(),
        status=Classifier.Status.DRAFT,
        target=Classifier.Target.ACTION,
        different_labels=Action.list_items(),
        accuracy=accuracy,
        test_size=test_size,
    )
    classifier.save()

    return classifier
