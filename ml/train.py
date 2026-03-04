import mlflow
import mlflow.sklearn
from mlflow.models import infer_signature

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

from sklearn.metrics import (
    recall_score,
    f1_score,
    precision_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    average_precision_score
)

import matplotlib.pyplot as plt
import seaborn as sns
import hashlib
import os

from text_processor import TextPreprocessor


class Training:
    def __init__(self, df, thresholds, tracking_uri="http://localhost:5000"):
        self.df = df
        self.thresholds = thresholds
        self.tracking_uri = tracking_uri
        self.best_recall = 0
        self.best_model = None
        self.best_X_test = None
        self.best_y_test = None
        self.best_threshold = None

    def _get_dataset_hash(self):
        content = self.df["comment_text"].str.cat(sep="").encode("utf-8")
        return hashlib.md5(content).hexdigest()[:8]

    def training(self):

        mlflow.set_tracking_uri(self.tracking_uri)
        mlflow.set_experiment("MultinomialNB_experiment")

        for threshold in self.thresholds:

            with mlflow.start_run(run_name=f"threshold_{threshold}"):

                X = self.df["comment_text"]
                y = self.df["toxicity"].apply(
                    lambda x: 1 if x >= threshold else 0
                )
                print(X.shape)
                print(y.value_counts())
                print(y.describe())

                X_train_val, X_test, y_train_val, y_test = train_test_split(
                    X, y, test_size=0.2, stratify=y, random_state=42
                )

                X_train, X_val, y_train, y_val = train_test_split(
                    X_train_val, y_train_val,
                    test_size=0.2,
                    stratify=y_train_val,
                    random_state=42
                )

                pipeline = Pipeline([
                    ("cleaning", TextPreprocessor()),
                    ("tfidf", TfidfVectorizer()),
                    ("model", MultinomialNB())
                ])

                pipeline.fit(X_train, y_train)

                y_val_pred = pipeline.predict(X_val)
                y_val_proba = pipeline.predict_proba(X_val)[:, 1]

                # ======================
                # Validation Metrics
                # ======================
                val_recall = recall_score(y_val, y_val_pred)
                val_f1 = f1_score(y_val, y_val_pred)
                val_precision = precision_score(y_val, y_val_pred)
                val_auc = roc_auc_score(y_val, y_val_proba)
                val_avg_precision = average_precision_score(y_val, y_val_proba)

                mlflow.log_param("threshold", threshold)

                mlflow.log_metric("val_recall", val_recall)
                mlflow.log_metric("val_f1", val_f1)
                mlflow.log_metric("val_precision", val_precision)
                mlflow.log_metric("val_roc_auc", val_auc)
                mlflow.log_metric("val_avg_precision", val_avg_precision)

                # ======================
                # Confusion Matrix (Val)
                # ======================
                cm = confusion_matrix(y_val, y_val_pred)

                plt.figure()
                sns.heatmap(cm, annot=True, fmt="d")
                plt.title("Confusion Matrix (Validation)")
                plt.xlabel("Predicted")
                plt.ylabel("Actual")

                cm_path = "confusion_matrix.png"
                plt.savefig(cm_path)
                plt.close()

                mlflow.log_artifact(cm_path)
                os.remove(cm_path)

                # ======================
                # ROC Curve (Val)
                # ======================
                fpr, tpr, _ = roc_curve(y_val, y_val_proba)

                plt.figure()
                plt.plot(fpr, tpr)
                plt.plot([0, 1], [0, 1], linestyle="--")
                plt.xlabel("False Positive Rate")
                plt.ylabel("True Positive Rate")
                plt.title("ROC Curve (Validation)")

                roc_path = "roc_curve.png"
                plt.savefig(roc_path)
                plt.close()

                mlflow.log_artifact(roc_path)
                os.remove(roc_path)

                # ======================
                # PR Curve (Val)
                # ======================
                precision, recall, _ = precision_recall_curve(y_val, y_val_proba)

                plt.figure()
                plt.plot(recall, precision)
                plt.xlabel("Recall")
                plt.ylabel("Precision")
                plt.title("Precision-Recall Curve (Validation)")

                pr_path = "precision_recall_curve.png"
                plt.savefig(pr_path)
                plt.close()

                mlflow.log_artifact(pr_path)
                os.remove(pr_path)

                # ======================
                # Track Best Model
                # ======================
                if val_recall > self.best_recall:
                    self.best_recall = val_recall
                    self.best_model = pipeline
                    self.best_X_test = X_test
                    self.best_y_test = y_test
                    self.best_threshold = threshold

        self.register_best_model()

    def register_best_model(self):
        with mlflow.start_run(run_name="best_model_registration"):

            # ======================
            # Best Threshold Info
            # ======================
            mlflow.log_param("best_threshold", self.best_threshold)

            # ======================
            # Dataset Version
            # ======================
            mlflow.log_param("dataset_row_count", len(self.df))
            mlflow.log_param("dataset_hash", self._get_dataset_hash())

            # ======================
            # Test Metrics
            # ======================
            y_test_pred = self.best_model.predict(self.best_X_test)
            y_test_proba = self.best_model.predict_proba(self.best_X_test)[:, 1]

            test_recall = recall_score(self.best_y_test, y_test_pred)
            test_f1 = f1_score(self.best_y_test, y_test_pred)
            test_precision = precision_score(self.best_y_test, y_test_pred)
            test_auc = roc_auc_score(self.best_y_test, y_test_proba)
            test_avg_precision = average_precision_score(self.best_y_test, y_test_proba)

            mlflow.log_metric("test_recall", test_recall)
            mlflow.log_metric("test_f1", test_f1)
            mlflow.log_metric("test_precision", test_precision)
            mlflow.log_metric("test_roc_auc", test_auc)
            mlflow.log_metric("test_avg_precision", test_avg_precision)

            # ======================
            # Confusion Matrix (Test)
            # ======================
            cm = confusion_matrix(self.best_y_test, y_test_pred)

            plt.figure()
            sns.heatmap(cm, annot=True, fmt="d")
            plt.title("Confusion Matrix (Test)")
            plt.xlabel("Predicted")
            plt.ylabel("Actual")

            cm_path = "confusion_matrix_test.png"
            plt.savefig(cm_path)
            plt.close()

            mlflow.log_artifact(cm_path)
            os.remove(cm_path)

            # ======================
            # ROC Curve (Test)
            # ======================
            fpr, tpr, _ = roc_curve(self.best_y_test, y_test_proba)

            plt.figure()
            plt.plot(fpr, tpr)
            plt.plot([0, 1], [0, 1], linestyle="--")
            plt.xlabel("False Positive Rate")
            plt.ylabel("True Positive Rate")
            plt.title("ROC Curve (Test)")

            roc_path = "roc_curve_test.png"
            plt.savefig(roc_path)
            plt.close()

            mlflow.log_artifact(roc_path)
            os.remove(roc_path)

            # ======================
            # PR Curve (Test)
            # ======================
            precision, recall, _ = precision_recall_curve(self.best_y_test, y_test_proba)

            plt.figure()
            plt.plot(recall, precision)
            plt.xlabel("Recall")
            plt.ylabel("Precision")
            plt.title("Precision-Recall Curve (Test)")

            pr_path = "precision_recall_curve_test.png"
            plt.savefig(pr_path)
            plt.close()

            mlflow.log_artifact(pr_path)
            os.remove(pr_path)

            # ======================
            # Log Model
            # ======================
            sample_input = self.df["comment_text"].iloc[:5]

            signature = infer_signature(
                sample_input,
                self.best_model.predict(sample_input)
            )

            mlflow.sklearn.log_model(
                sk_model=self.best_model,
                artifact_path="model",
                signature=signature,
                registered_model_name="MultinomialNB"
            )

            print("Best model registered successfully.")