import os
import mlflow
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

MLFLOW_URI = os.environ.get('MLFLOW_URI')
MODEL_URI = os.environ.get('MODEL_URI')

if MLFLOW_URI == None:
    raise Exception('MLFLOW_URI is not defined')

if MODEL_URI == None:
    raise Exception('MODEL_URI is not defined')

mlflow.set_tracking_uri(MLFLOW_URI)

try:
    pipeline = mlflow.pyfunc.load_model(model_uri=MODEL_URI)
except mlflow.exceptions.RestException as e:
    print('Error: {}'.format(e))
    print('You should run the workflow first to train and register the model.')
    exit(1)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.get('/')
async def root():
    return {
        'metadata': pipeline.metadata,
    }


@app.get('/seven-days-forecast')
async def seven_days_forecast():
    today = datetime.today().date()
    dates = [today + timedelta(days=i) for i in range(1, 8)]

    X = pd.DataFrame({
        'year': [date.year for date in dates],
        'month': [date.month for date in dates],
        'day': [date.day for date in dates]
    })

    predictions = [round(pred) for pred in pipeline.predict(X)]

    response = []
    for date, prediction in zip(dates, predictions):
        response.append({
            'datetime': date.strftime('%Y-%m-%dT%H:%M:%S+00:00'),
            'prediction_rateTenth': prediction,
            'prediction_rate': prediction / 10,
        })

    return response
