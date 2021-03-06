DEBUG = True # Turns on debugging features in Flask
SECRET_KEY = "safra-dev-app"

ALLOWED_EXTENSIONS = {'zip', 'py'}
SUCCESS = {'status' : "OK"}
ERROR = {'status' : "ERROR"}

PIPENV_IGNORE_VIRTUALENVS=1

MONGO_URI =  "mongodb://127.0.0.1:27017/wm" # windmill

APPLICATION_ROOT = "/apl-wm-crm"

LOG_FLAG = False
LOGGER_NAME = "wm-logger"

#BCRYPT_LOG_ROUNDS = 12 # Configuration for the Flask-Bcrypt extension
#MAIL_FROM_EMAIL = "lukasavicus@gmail.com" # For use in application emails