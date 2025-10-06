# ===============================================================
# Random Forest Model - CSV Input (Classification or Regression)
# ===============================================================

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, mean_squared_error, r2_score
import argparse
import sys

# ---------------------------------------------------------------
# 1. Load Data
# ---------------------------------------------------------------
def load_data(train_path, test_path, target_column):
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    if target_column not in train_df.columns:
        sys.exit(f"Error: '{target_column}' not found in training data columns")

    X_train = train_df.drop(columns=[target_column])
    y_train = train_df[target_column]

    if target_column in test_df.columns:
        X_test = test_df.drop(columns=[target_column])
        y_test = test_df[target_column]
    else:
        X_test = test_df.copy()
        y_test = None

    return X_train, y_train, X_test, y_test


# ---------------------------------------------------------------
# 2. Train Random Forest
# ---------------------------------------------------------------
def train_random_forest(X_train, y_train, model_type="classification", n_estimators=200, max_depth=None, random_state=42):
    if model_type == "classification":
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
    elif model_type == "regression":
        model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1
        )
    else:
        sys.exit("Error: model_type must be 'classification' or 'regression'")

    model.fit(X_train, y_train)
    return model


# ---------------------------------------------------------------
# 3. Evaluate Model
# ---------------------------------------------------------------
def evaluate_model(model, X_test, y_test, model_type):
    preds = model.predict(X_test)

    if model_type == "classification":
        acc = accuracy_score(y_test, preds)
        cm = confusion_matrix(y_test, preds)
        report = classification_report(y_test, preds)
        print(f"\n Accuracy: {acc:.4f}")
        print("\nConfusion Matrix:")
        print(cm)
        print("\nClassification Report:")
        print(report)

    elif model_type == "regression":
        mse = mean_squared_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        print(f"\n Mean Squared Error: {mse:.4f}")
        print(f" R² Score: {r2:.4f}")

    return preds


# ---------------------------------------------------------------
# 4. Main Entry Point
# ---------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a Random Forest model on CSV data.")
    parser.add_argument("--train", required=True, help="Path to training CSV file")
    parser.add_argument("--test", required=True, help="Path to test CSV file")
    parser.add_argument("--target", required=True, help="Name of target column")
    parser.add_argument("--type", choices=["classification", "regression"], default="classification", help="Model type")
    args = parser.parse_args()

    # Load data
    X_train, y_train, X_test, y_test = load_data(args.train, args.test, args.target)

    # Train model
    model = train_random_forest(X_train, y_train, model_type=args.type)

    # Evaluate if test labels are available
    if y_test is not None:
        evaluate_model(model, X_test, y_test, model_type=args.type)
    else:
        preds = model.predict(X_test)
        pd.DataFrame({"prediction": preds}).to_csv("predictions.csv", index=False)
        print(" Predictions saved to predictions.csv")
