import mlflow
import pandas as pd
from fastapi import FastAPI
from datetime import datetime, timedelta

mlflow.set_tracking_uri("http://localhost:5000")
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
    dates = [today + timedelta(days=i) for i in range(7)]

    X = pd.DataFrame({
        'year': [date.year for date in dates],
        'month': [date.month for date in dates],
        'day': [date.day for date in dates]
    })

    predictions = pipeline.predict(X)

    return {
        'seven_days_forecast': [round(v) for v in predictions],
    }
