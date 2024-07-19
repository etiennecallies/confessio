import base64
import pickle
from abc import abstractmethod

import tensorflow as tf
import keras
from keras.src.models.model import model_from_json
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np

from scraping.prune.models import Action


class MachineLearningInterface:
    @abstractmethod
    def fit(self, embeddings, actions: list[Action]):
        """Learning method"""
        pass

    @abstractmethod
    def predict(self, embeddings) -> list[Action]:
        """Prediction method"""
        pass

    @abstractmethod
    def from_pickle(self, pickle_as_str: str):
        pass

    @abstractmethod
    def to_pickle(self) -> str:
        pass


def evaluate(model: MachineLearningInterface, vectors_test, labels_test):
    labels_pred = model.predict(vectors_test)

    return accuracy_score(labels_test, labels_pred)


class TensorFlowModel(MachineLearningInterface):
    def __init__(self, epochs=90, max_neurones=240, optimizer='adam',
                 loss='sparse_categorical_crossentropy', metric='accuracy'):
        self.model = None
        self.different_labels = [
            Action.SHOW,
            Action.HIDE,
            Action.STOP,
        ]
        self.epochs = epochs
        self.max_neurones = max_neurones
        self.optimizer = optimizer
        self.loss = loss
        self.metric = metric

    def get_metric(self):
        if self.metric == 'accuracy':
            return keras.metrics.Accuracy()
        if self.metric == 'binary_accuracy':
            return keras.metrics.BinaryAccuracy()
        if self.metric == 'binary_crossentropy':
            return keras.metrics.BinaryCrossentropy()
        if self.metric == 'categorical_accuracy':
            return keras.metrics.CategoricalAccuracy()
        if self.metric == 'categorical_xentropy':
            return keras.metrics.CategoricalCrossentropy()
        if self.metric == 'false_positives':
            return keras.metrics.FalsePositives()
        if self.metric == 'false_negatives':
            return keras.metrics.FalseNegatives()
        if self.metric == 'true_positives':
            return keras.metrics.TruePositives()
        if self.metric == 'true_negatives':
            return keras.metrics.TrueNegatives()
        if self.metric == 'mean_squared_error':
            return keras.metrics.MeanSquaredError()
        if self.metric == 'precision':
            return keras.metrics.Precision()
        if self.metric == 'recall':
            return keras.metrics.Recall()
        if self.metric == 'auc':
            return keras.metrics.AUC()
        raise ValueError(f'unrecognized metric {self.metric}')

    def fit(self, embeddings, actions: list[Action]):
        vector_length = len(embeddings[0])
        nb_neurones = min(vector_length, self.max_neurones)
        self.model = keras.Sequential([
            keras.layers.Dense(nb_neurones,
                               input_shape=(vector_length,),
                               activation='relu'),
            keras.layers.Dense(nb_neurones,
                               activation='relu'),
            keras.layers.Dense(3,
                               activation='softmax')
        ])
        self.model.compile(
            optimizer=self.optimizer,
            loss=self.loss,
            metrics=[self.get_metric()]
        )
        actions_indices = list(map(self.different_labels.index, actions))
        self.model.fit(tf.convert_to_tensor(pd.DataFrame(embeddings)),
                       tf.convert_to_tensor(pd.DataFrame(actions_indices)),
                       epochs=self.epochs,
                       verbose=False)

    def predict(self, vectors) -> list:
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
        byte_string = base64.b64decode(pickle_as_str)
        model_data = pickle.loads(byte_string)

        self.model = model_from_json(model_data['model_json'])
        self.model.set_weights(model_data['model_weights'])
