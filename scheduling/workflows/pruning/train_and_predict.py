import base64
import pickle
from abc import abstractmethod
from typing import TypeVar, Generic

import numpy as np

from scraping.utils.enum_utils import StringEnum

E = TypeVar('E', bound=StringEnum)


class MachineLearningInterface(Generic[E]):
    different_labels: list[E]

    @abstractmethod
    def fit(self, embeddings, labels: list[E]):
        """Learning method"""
        pass

    @abstractmethod
    def predict(self, embeddings) -> list[E]:
        """Prediction method"""
        pass

    @abstractmethod
    def from_pickle(self, pickle_as_str: str):
        pass

    @abstractmethod
    def to_pickle(self) -> str:
        pass


def evaluate(model: MachineLearningInterface, vectors_test, labels_test):
    print('import sklearn.metrics.accuracy_score')
    from sklearn.metrics import accuracy_score
    print('starting evaluation')
    labels_pred = model.predict(vectors_test)
    assert len(labels_pred) == len(labels_test), \
        "Number of predicted labels must be equal to number of test labels"

    for label in model.different_labels:
        test_indices = [i for i, lab in enumerate(labels_test) if lab == label]
        print(f'Label {label} ({len(test_indices)}):')
        pred_values = {}
        for i in test_indices:
            pred_lab = labels_pred[i]
            if pred_lab not in pred_values:
                pred_values[pred_lab] = 0
            pred_values[pred_lab] += 1
        for pred_lab, count in sorted(pred_values.items(), key=lambda x: x[1], reverse=True):
            print(f'  got {pred_lab}: {count} ({count / len(test_indices) * 100:.2f}%)')

    return accuracy_score(list(map(str, labels_test)), list(map(str, labels_pred)))


class TensorFlowModel(MachineLearningInterface[E], Generic[E]):
    def __init__(self, different_labels: list[E], epochs=90, max_neurones=240, optimizer='adam',
                 loss='sparse_categorical_crossentropy'):
        self.model = None
        self.different_labels = different_labels
        self.epochs = epochs
        self.max_neurones = max_neurones
        self.optimizer = optimizer
        self.loss = loss

    def fit(self, embeddings, labels: list[E]):
        print('import tensorflow')
        import tensorflow as tf
        print('import keras')
        import keras
        print('import pandas')
        import pandas as pd
        print('starting fit')
        vector_length = len(embeddings[0])
        nb_neurones = min(vector_length, self.max_neurones)
        self.model = keras.Sequential([
            keras.layers.Input(shape=(vector_length,)),
            keras.layers.Dense(nb_neurones,
                               activation='relu'),
            keras.layers.Dense(nb_neurones,
                               activation='relu'),
            keras.layers.Dense(len(self.different_labels),
                               activation='softmax')
        ])
        self.model.compile(
            optimizer=self.optimizer,
            loss=self.loss,
            metrics=[keras.metrics.Accuracy()]
        )
        labels_indices = list(map(self.different_labels.index, labels))
        self.model.fit(tf.convert_to_tensor(pd.DataFrame(embeddings)),
                       tf.convert_to_tensor(pd.DataFrame(labels_indices)),
                       epochs=self.epochs,
                       verbose=False)

    def predict(self, vectors) -> list[E]:
        import pandas as pd
        predictions = self.model.predict(pd.DataFrame(vectors),
                                         verbose=False)

        # Convert probability distributions to class indices
        predicted_classes = np.argmax(predictions, axis=1)

        # Map class indices to actual labels
        return [self.different_labels[class_idx] for class_idx in predicted_classes]

    def to_pickle(self) -> str:
        model_json = self.model.to_json()
        model_weights = self.model.get_weights()

        model_data = {
            'model_json': model_json,
            'model_weights': model_weights
        }

        byte_string = pickle.dumps(model_data)
        encoded_string = base64.b64encode(byte_string).decode('utf-8')

        return encoded_string

    def from_pickle(self, pickle_as_str: str):
        print('import keras.src.models.model')
        from keras.src.models.model import model_from_json
        print('loading model')
        byte_string = base64.b64decode(pickle_as_str)
        model_data = pickle.loads(byte_string)

        self.model = model_from_json(model_data['model_json'])
        self.model.set_weights(model_data['model_weights'])
