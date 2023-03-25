import config

import requests
import pandas as pd
import numpy as np
import mlflow

from prefect import task, flow
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

mlflow.set_tracking_uri("http://mlflow:5000")


@task()
def download_data(url: str) -> str:
    """Download data from a given URL"""
    res = requests.get(url)

    return res.json()


@task()
def load_data(data: str) -> pd.DataFrame:
    """Load data into a pandas DataFrame"""

    return pd.DataFrame(data)


@task()
def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocess data"""

    # Convert ISO 8601 datetime to three columns : year, month, day
    splitted_datetime = df['datetime'].str.split('T', expand=True)[0]
    splitted_date = splitted_datetime.str.split('-', expand=True)

    df['year'] = splitted_date[0].astype('int')
    df['month'] = splitted_date[1].astype('int')
    df['day'] = splitted_date[2].astype('int')

    # Keep only needed columns
    df = df.drop(config.DROP_COLUMNS, axis=1)

    return df


@task()
def train_model(X_train, y_train) -> LinearRegression:
    """Train a model"""

    lr = LinearRegression()
    lr.fit(X_train, y_train)

    return lr


@task()
def predict(model: LinearRegression, input_data) -> np.ndarray:
    """Predict price"""

    return model.predict(input_data)


@task()
def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate mean squared error for two arrays"""

    return mean_squared_error(y_true, y_pred, squared=False)


@task()
def extract_X_y(df):
    """Extract X and y from a DataFrame"""

    X = df.drop(config.TARGET_COLUMN, axis=1)
    y = df[config.TARGET_COLUMN]

    return X, y


@flow()
def train_and_predict(X_train, y_train, X_test, y_test) -> dict:
    """Train model, predict values and calculate error"""

    with mlflow.start_run() as run:
        model = train_model(X_train, y_train)
        prediction = predict(model, X_test)
        mse = evaluate_model(y_test, prediction)

        mlflow.log_param('train_set_size', X_train.shape[0])
        mlflow.log_param('test_set_size', X_test.shape[0])
        mlflow.log_metric('test_mse', mse)

        mlflow.sklearn.log_model(model, 'model')

        mlflow.register_model(f'runs:/{run.info.run_id}/model', 'linear_regression')

    return {
        'model': model,
        'mse': mse,
    }


@task()
def build_new_data(data):
    res = []
    for d in data:
        res.append({
            'id': None,
            'datetime': d,
            'rate': None,
            'rateTenth': None,
        })

    return res


@flow()
def complete_ml(url: str):
    """Complete ML pipeline"""

    # Download data from URL
    raw_data = download_data(url)

    # Load data into a DataFrame
    df = load_data(raw_data['rates'])

    # Preprocess data
    df = preprocess_data(df)

    # Split data into train and test
    X, y = extract_X_y(df)

    X_train = X[config.TRAIN_TEST_OFFSET:]
    x_test = X[:config.TRAIN_TEST_OFFSET]
    y_train = y[config.TRAIN_TEST_OFFSET:]
    y_test = y[:config.TRAIN_TEST_OFFSET]

    # Train model, predict values and calculate error
    results = train_and_predict(X_train, y_train, x_test, y_test)
    print(f'MSE: {results["mse"]:.2f}')

    return results


@flow()
def batch_inference(data, model=None):
    data = build_new_data(data)

    df = load_data(data)
    df = preprocess_data(df)
    X, _ = extract_X_y(df)

    predictions = predict(model, X)

    return [round(v) for v in predictions]
