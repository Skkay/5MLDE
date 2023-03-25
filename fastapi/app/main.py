import mlflow
import pandas as pd
from fastapi import FastAPI
from datetime import datetime, timedelta

mlflow.set_tracking_uri("http://mlflow:5000")
pipeline = mlflow.pyfunc.load_model(model_uri='models:/linear_regression/production')

app = FastAPI()


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
