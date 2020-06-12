import os
import json
import datetime
from bson.objectid import ObjectId
import platform

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

import json_logging, logging, sys

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

class PrefixMiddleware(object):

    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]

def create_app(test_config=None):
    """
        Factory function to create an instance of the app
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.debug = True

    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'windmill.sqlite'),
    )

    ## SQL Alchemy configs
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    ##

    if(test_config is None):
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #from . import db
    #db.init_app(app)

    app.config.from_object('config')
    
    # Set the application root, by default = "/". Change this to add a "context" to all routes
    app.wsgi_app = PrefixMiddleware(app.wsgi_app, prefix=app.config["APPLICATION_ROOT"])

    if(app.config["LOG_FLAG"] == True):
        json_logging.ENABLE_JSON_LOGGING = True
        json_logging.init_flask()
        json_logging.init_request_instrument(app)
        
        # init the logger as usual
        logger = logging.getLogger(app.config["LOGGER_NAME"])
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler(sys.stdout))

    app.config['UPLOAD_FOLDER'] =  os.path.join(app.root_path, 'uploads')
    app.config['PYTHON_CMD'] = 'python' if platform.system() == 'Windows' else 'python3.7'

    #app.config['SCHEDULER'] = BlockingScheduler()
    app.config['SCHEDULER'] = BackgroundScheduler()
    app.config['SCHEDULER'].start()
    
    print(hex(id(app.config['SCHEDULER'])))

    return app

app = create_app()

# Previous using SQLAlchemy with sqlite
db = SQLAlchemy(app)

# add mongo url to flask config, so that flask_pymongo can use it to make connection
#app.config['MONGO_URI'] = os.environ.get('DB')
mongo = PyMongo(app)

# use the modified encoder class to handle ObjectId & datetime object while jsonifying the response.

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'main.login'
login_manager.login_message_category = 'info'

#from windmill import routes

from windmill.archives.routes import archives
from windmill.main.routes import main
from windmill.runs.routes import runs
from windmill.tasks.routes import tasks
from windmill.venvironments.routes import venvironments
from windmill.dev.routes import dev
from windmill.errors.handlers import errors

app.register_blueprint(archives)
app.register_blueprint(main)
app.register_blueprint(runs)
app.register_blueprint(tasks)
app.register_blueprint(venvironments)
app.register_blueprint(dev)
app.register_blueprint(errors)