DATA_URL = 'http://51.75.204.199:9002/ogrineRates?sort=desc'
DROP_COLUMNS = ['id', 'datetime', 'rate']
TARGET_COLUMN = 'rateTenth'
TRAIN_TEST_OFFSET = 30
LOCAL_STORAGE = '/home/skkay/dev/project/5MLDE/exam'

CRON_TRAINING = '0 1 * * 1'  # every monday at 1am
