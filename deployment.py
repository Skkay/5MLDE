import config
from workflow import complete_ml

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

training_deployment = Deployment.build_from_flow(
    name='Model Training Deployment',
    flow=complete_ml,
    version='1.0',
    tags=['model', 'training'],
    schedule=CronSchedule(cron=config.CRON_TRAINING),
    parameters={
        'url': config.DATA_URL,
    }
)

if __name__ == '__main__':
    training_deployment.apply()
