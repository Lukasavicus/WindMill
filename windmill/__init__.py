import os
import json
import datetime
from bson.objectid import ObjectId
import platform

from apscheduler.schedulers.blocking import BlockingScheduler

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

def create_app(test_config=None):
    """
        Factory function to create an instance of the app
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'windmill.sqlite'),
    )
    app.config['SECRET_KEY'] = ''

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
    app.secret_key = 'safra_dev_app'
    #app.config['UPLOAD_FOLDER'] = os.path.join('windmill', 'uploads')
    app.config['UPLOAD_FOLDER'] =  os.path.join(app.root_path, 'uploads')
    app.config['python_cmd'] = 'python' if platform.system() == 'Windows' else 'python3'

    app.config['SCHEDULER'] = BlockingScheduler()
    print(hex(id(app.config['SCHEDULER'])))

    return app

app = create_app()

# Previous using SQLAlchemy with sqlite
db = SQLAlchemy(app)

# add mongo url to flask config, so that flask_pymongo can use it to make connection
#app.config['MONGO_URI'] = os.environ.get('DB')
#app.config['MONGO_URI'] =  "mongodb://127.0.0.1:27017/wm" # windmill
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
from windmill.errors.handlers import errors

app.register_blueprint(archives)
app.register_blueprint(main)
app.register_blueprint(runs)
app.register_blueprint(tasks)
app.register_blueprint(venvironments)
app.register_blueprint(errors)