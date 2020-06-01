# https://docs.python.org/3/library/typing.html
#from typing import Final # restriction on Python > 3.8

import sys, os, platform, psutil
import subprocess as sub
from datetime import datetime

from bson.objectid import ObjectId
from pymongo import MongoClient

from flask import current_app as app
from flask_login import UserMixin

from apscheduler.schedulers.blocking import BlockingScheduler

from windmill import mongo
from windmill import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# === User - Model ============================================================
# SQLite
# The usage of UserMixin is necessary to transform this class into something that uses Login utilities
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)

    # double-underscored methods -> dunder methods -> magic methods
    def __repr__(self):
        return f"User('{self.id}', '{self.username}', '{self.email}')"

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class JobList():
    pass

#from windmill.agents import Agent

# TODO: change to an Enum
STATUS = {}
STATUS['not_running'] = "Not Running"
STATUS['running'] = "Running"
STATUS['scheduled'] = "Scheduled"
STATUS['failed'] = "Failed"
STATUS['success'] = "Success"

# === Job - Model =============================================================
class Job():
    _id = None
    name = None
    entry_point = None

    scheduled = False   # schedule property (boolean) - When the job is scheduled to start
    start_at = None     # schedule property (datetime) - When the job is scheduled to start
    end_at = None        # schedule property (datetime) - When the job is scheduled to end
    schd_hours = 0        # schedule property (int) - Interval of hours in which scheduled job will be executed
    schd_minutes = 0     # schedule property (int) - Interval of minutes in which scheduled job will be executed
    schd_seconds = 0     # schedule property (int) - Interval of seconds in which scheduled job will be executed

    pid = None

    last_exec_status = STATUS['not_running']
    last_exec_started_at = None
    last_exec_ended_at = None

    no_runs = 0

    cron = None

    def __init__(self,
            name, entry_point, _id=None, start_at=None, end_at=None, pid=None, schd_hours=0, schd_minutes=0, schd_seconds=0,
            last_exec_status=STATUS['not_running'], no_runs=0, cron=None
        ):
        self.name = name
        self.entry_point = entry_point
        self._id = _id
        self.start_at = start_at
        self.end_at = end_at
        self.pid = pid
        self.schd_hours = schd_hours
        self.schd_minutes = schd_minutes
        self.schd_seconds = schd_seconds
        self.last_exec_status = last_exec_status
        self.no_runs = no_runs

        self.cron = cron if(cron) else self._cron()

        self.agent = Agent(mongo, self)

    def _cron(self):
        st = 's' if(self.start_at != None) else '-'
        e = 'e' if(self.end_at != None) else '-'
        h = str(self.schd_hours) if(self.schd_hours != 0) else '*'
        m = str(self.schd_minutes) if(self.schd_minutes != 0) else '*'
        s = str(self.schd_seconds) if(self.schd_seconds != 0) else '*'
        return f"/{st} /{h} /{m} /{s} /{e}"


    def isAlive(self):
        return self.agent.isAlive()

    def play(self):
        print("play Agent:", self.agent)
        self.agent.execute_job()

    def stop(self):
        print("stop Agent:", self.agent)
        self.agent.kill_job()

    def schedule(self):
        self.agent.schedule_job()

    def jsonify(self):
        return {
                    '_id': self._id, 'end_at' : self.end_at, 'entry_point': self.entry_point,
                    'last_exec_status': self.last_exec_status, 'name': self.name, 'no_runs' : self.no_runs,
                    'pid': self.pid, 'schd_hours' : self.schd_hours, 'schd_minutes' : self.schd_minutes,
                    'schd_seconds' : self.schd_seconds, 'start_at': self.start_at,
                    'path_to_entry_point' : os.path.sep.join(self.entry_point.split(os.path.sep)[:-1]),
                    'file_of_entry_point' : self.entry_point.split(os.path.sep)[-1]
                }

    def __repr__(self):
        return f"JOB: id[{self._id}] name[{self.name}]"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === Job - Data Access Object ================================================
class JobDAO():
    def __init__(self):
        Exception('This class should not be instantiated')

    @staticmethod
    def insert(job):
        mongo.db.jobs.insert({
            'name' : job.name,
            'entry_point' : job.entry_point,
            'start_at' : job.start_at,
            'end_at' : job.end_at,
            'pid' : job.pid,
            'schd_hours' : job.schd_hours,
            'schd_minutes' : job.schd_minutes,
            'schd_seconds' : job.schd_seconds,
            'last_exec_status' : job.last_exec_status,
            'no_runs' : job.no_runs,
            'cron' : job.cron
        })

    @staticmethod
    def delete(job):
        if(job.isAlive()):
            job.process.kill_job()
        mongo.db.jobs.delete_one( {"_id": ObjectId(job._id)})

    @staticmethod
    def _new_job(job_item):
        return Job(job_item["name"], job_item["entry_point"], job_item["_id"], job_item["start_at"], job_item["end_at"], job_item["pid"],
            job_item["schd_hours"], job_item["schd_minutes"], job_item["schd_seconds"], job_item["last_exec_status"], job_item["no_runs"], job_item["cron"])

    @staticmethod
    def recover():
        job_list = list(mongo.db.jobs.find({}))
        if(len(job_list) == 0):
            return None
        else:
            jobs = []
            for job_item in job_list:
                jobs.append(JobDAO._new_job(job_item))
            return jobs

    @staticmethod
    def update(job):
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            { '$set' : {
                'name' : job.name,
                'entry_point' : job.entry_point,
                'start_at' : job.start_at,
                'end_at' : job.end_at,
                'schd_hours' : job.schd_hours,
                'schd_minutes' : job.schd_minutes,
                'schd_seconds' : job.schd_seconds
            } },
            upsert = True
        )

    @staticmethod
    def update_when_running(job):
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            { '$set' : {'last_exec_status' : "RUNNING", 'pid' : job.pid } },
            upsert = True
        )

    @staticmethod
    def update_when_finish_run(job):
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            {
                '$set' : {'last_exec_status' : job.last_exec_status, 'end_at' : job.end_at },
                '$inc' : { 'quantity' : 1, "no_runs": 1 }
            },
            upsert = True
        )

    @staticmethod
    def recover_by_id(id):
        job_item = mongo.db.jobs.find_one({'_id' : ObjectId(id)})
        if(job_item == None):
            return None
        else:
            return JobDAO._new_job(job_item)

    @staticmethod
    def delete_by_id(id):
        return mongo.db.jobs.delete_one( {"_id": ObjectId(id)})
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === Run - Model =============================================================
class Run():
    _id = None
    job_id = None
    job_name = None
    job_entry_point = None
    started_at = None
    ended_at = None
    status = None
    out = []
    err = []

    def __init__(self,
            job_id, job_name, job_entry_point, _id=None, started_at=None, ended_at=None, status=None, out=[], err=[]
        ):
        self.job_id = job_id
        self.job_name = job_name
        self.job_entry_point = job_entry_point
        self._id = _id
        self.started_at = started_at
        self.ended_at = ended_at
        self.status = status
        self.out = out
        self.err = err

    def jsonify(self):
        return {
                    '_id': self._id, 'ended_at' : self.ended_at, 'err' : self.err, 
                    'job_entry_point': self.job_entry_point, 'job_id': self.job_id, 'job_name': self.job_name,
                    'out': self.out, 'started_at' : self.started_at, 'status' : self.status
                }

    def __repr__(self):
        return f"RUN: id[{self._id}] name[{self.job_name}]"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === Run - Data Access Object ================================================
class RunDAO():
    def __init__(self):
        Exception('This class should not be instantiated')

    @staticmethod
    def _new_run(run_item):
        return Run(run_item["job_id"], run_item["job_name"], run_item["job_entry_point"], run_item["_id"], run_item["started_at"],
                run_item["ended_at"], run_item["status"], run_item["out"], run_item["err"])
    
    @staticmethod
    def _new_run_list(run_list):
        if(len(run_list) == 0):
            return None
        else:
            runs = []
            for run_item in run_list:
                runs.append(RunDAO._new_run(run_item))
            return runs

    @staticmethod
    def insert(run):
        return mongo.db.runs.insert_one({
            'job_id': ObjectId(run.job_id),
            'job_name': run.job_name,
            'job_entry_point': run.job_entry_point,
            'started_at' : datetime.now(),
            'ended_at' : None,
            'status' : None,
            'out' : [],
            'err' : []
        }).inserted_id

    @staticmethod
    def update_add_output(run, output):
        mongo.db.runs.find_one_and_update(
            {'_id': run._id },
            { '$push': { 'out': output.strip() } },
            upsert = True
        )

    @staticmethod
    def update_add_error(run, error):
        mongo.db.runs.find_one_and_update(
            {
                '$and' : [ { '_id': run._id }, { 'status': { '$not': { '$eq': -1 } } } ]
            },
            { '$push': { 'err': '\n'.join([err.strip() for err in error]) } },
            #upsert = True
        )

    @staticmethod
    def update_when_finish_run(run):
        mongo.db.runs.find_one_and_update(
            {
                '$and' : [ { '_id': run._id }, { 'status': { '$not': { '$eq': -1 } } } ]
            },
            { '$set' : {'status' : run.status, 'ended_at' : run.ended_at } },
            upsert = True
        )

    @staticmethod
    def recover():
        run_list = list(mongo.db.runs.find({}))
        return RunDAO._new_run_list(run_list)

    @staticmethod
    def recover_by_job_id(id):
        run_list = list(mongo.db.runs.find({'job_id' : ObjectId(id)}))
        return RunDAO._new_run_list(run_list)

    @staticmethod
    def recover_by_run_id(id):
        run_item = mongo.db.runs.find_one({'_id' : ObjectId(id)})
        if(run_item == None):
            return None
        else:
            return Run(run_item["job_id"], run_item["job_name"], run_item["job_entry_point"], run_item["_id"], run_item["started_at"],
                run_item["ended_at"], run_item["status"], run_item["out"], run_item["err"])
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Agent - Helper Class ====================================================
class Agent:
    """
        This class represents in a high-level way the agent that execute some job
        directly or scheduled
    """
    #PIPENV_CMD:Final = "pipenv" # define the string that represents the pipenv command
    #PYTHON_CMD:Final = "python" if platform.system() == "Windows" else "python3" # define the string that represents the python command

    PIPENV_CMD = "pipenv" # define the string that represents the pipenv command
    PYTHON_CMD = "python" if platform.system() == "Windows" else "python3" # define the string that represents the python command

    def __init__(self, connection, job):
        self.connection:MongoClient = connection
        self.job:Job = job

        self.base_path = app.config['UPLOAD_FOLDER']

        self.run = Run(job._id, job.name, job.entry_point)

        self.interval = 'seconds' #interval
        self.no_interval = 30 #no_interval

    def execute_job(self):
        print("executing job")
        # TODO: database name and collection name should be parameters
        runs_collection = self.connection.db.runs

        # Insert run of a job into database
        self.run._id = RunDAO.insert(self.run)
        
        folder_path = os.path.sep.join(os.path.split(self.job.entry_point)[:-1])
        script_folder = os.path.join(self.base_path, folder_path)
        script_file = os.path.split(self.job.entry_point)[-1]

        #print("EXEC:", f"{Agent.PIPENV_CMD} run {Agent.PYTHON_CMD} -u {script_file}", " ON: ", script_folder)
        
        # Trigger the run of a job in a form of a new subprocess (executing with pipenv to isolate the virtual enviroments)
        process = sub.Popen(f"{Agent.PIPENV_CMD} run {Agent.PYTHON_CMD} -u {script_file}", stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines=True, cwd=script_folder)
        
        #print("process:", process)

        # Update the job info with status "RUNNING"
        self.job.pid = process.pid
        JobDAO.update_when_running(self.job)
        
        # Observe the output of subprocess (stdout and stderr)
        while True:
            output = process.stdout.readline()
            if(process.poll() is not None):
                print("\n\nExiting because the process is no longer alive\n\n")
                break
            if(output):
                print(f"\n\nOUTPUT: >{output}<\n\n")
                RunDAO.update_add_output(self.run ,output.strip())

        return_process_code = process.returncode
        actual_status = None
        run_register = list(runs_collection.find({ '_id': self.run._id } ) ) [0]
        if('status' in run_register):
            actual_status = run_register['status']

        print(f"\n\nActual Status: {actual_status}\n\n")

        if(return_process_code == 1):
            print("\n\n Something goes wrong \n\n")
            error = process.stderr.readlines()
            print(f"\n\n The error {error} will be logged\n\n")
            if(error and len(error) != 0):
                RunDAO.update_add_error(self.run, error)
                print(f"\n\n The error {error} was logged\n\n")
        
        self.job.end_at = datetime.now()
        self.run.ended_at = self.job.end_at
        self.run.status = return_process_code

        RunDAO.update_when_finish_run(self.run)

        self.job.status = STATUS['success'] if(return_process_code == 0) else STATUS['failed']
        
        JobDAO.update_when_finish_run(self.job)

        return return_process_code
    
    def kill_job(self):

        scheduler = app.config['SCHEDULER']
        try:
            scheduler.remove_job(str(self.job._id))
            print(f"Job with id {str(self.job._id)} was Scheduled! but now we are removing it")
            #job.last_exec_status = 15
            #JobDAO.update_when_finish_run(job)
        except:
            print(f"Job with id {str(self.job._id)} was not scheduled")
            print("THIS AGENT:", self)
            process = self._get_process()
            if(process):
                process.kill()

    def schedule_job(self):
        #print("arguments ", sys.argv)
        scheduler = app.config['SCHEDULER']
        #scheduler = BlockingScheduler()
        print("SCHDL ADDRESS:", hex(id(scheduler)))

        kwargs = {
            'id' : str(self.job._id),
            'start_date' : self.job.start_at,
            'end_date' : self.job.start_at,
            'hours' : self.job.schd_hours,
            'minutes' : self.job.schd_minutes,
            'seconds' : self.job.schd_seconds,
        }
        #scheduler.add_interval_job(self.execute_job, 'interval', **kwargs)
        options = {k : v for k,v in kwargs.items() if kwargs[k]}
        print("Options: ", options)
        scheduler.add_job(self.execute_job, 'interval', **options)
        scheduler.start()

    def isAlive(self):
        process = self._get_process()
        return (process != None and process.is_running() == None)

    def _get_process(self):
        try:
            process = psutil.Process(self.job.pid)
        except:
            return None
        return process
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Package:
    _id = None

    def __init__(self, name, version_specifier="", version=""):
        self.name = name
        self.version_specifier = version_specifier
        self.version = version
    
    def __repr__(self):
        return f"{{'name' : '{self.name}', 'version_specifier' : '{self.version_specifier}', 'version' : '{self.version}' }}"

class VEnvironment:
    _id = None

    def __init__(self, _id, name, packages = []):
        self._id = _id
        self.name = name
        self.packages = packages
    
    def add_package(self, package):
        if(package not in self.packages):
            self.packages.append(package)

    def remove_package(self, package):
        if(package in self.packages):
            self.packages.remove(package)

    def update_package(self, package):
        pkgs_list  = list(filter(lambda pkg : pkg.name == package.name), self.packages)

        if(pkgs_list != None):
            pkg_to_update = pkgs_list[0]

        self.packages.remove(pkg_to_update)
        self.packages.append(package)

    def jsonify(self):
        return { '_id': self._id, 'name' : self.name, 'packages' : self.packages }

    def __repr__(self):
        return f"VENV: id[{self._id}] name[{self.name}]"


# === VEnvironment - Data Access Object =======================================
class VEnvironmentDAO():
    def __init__(self):
        Exception('This class should not be instantiated')

    @staticmethod
    def _new_venv(venv_item):
        return VEnvironment(venv_item["_id"], venv_item["name"])#, venv_item["packages"])
    
    @staticmethod
    def _new_venv_list(venv_list):
        if(len(venv_list) == 0):
            return None
        else:
            venvs = []
            for venv_item in venv_list:
                venvs.append(VEnvironmentDAO._new_venv(venv_item))
            return venvs
    
    @staticmethod
    def insert(venv):
        print(venv.packages, type(venv.packages))
        pkgs = [f"{pkg}" for pkg in venv.packages]
        mongo.db.venvs.insert({
            'name' : venv.name,
            'packages' : pkgs
        })

    @staticmethod
    def update(venv):
        mongo.db.venvs.find_one_and_update(
            {
                { '_id': venv._id }
            },
            { '$set' : { 'name' : venv.name, 'packages' : venv.packages } },
            #upsert = True
        )

    @staticmethod
    def delete(id):
        return mongo.db.venvs.delete_one( {"_id": ObjectId(id)})


    @staticmethod
    def recover():
        venv_list = list(mongo.db.venvs.find({}))
        return VEnvironmentDAO._new_venv_list(venv_list)

    @staticmethod
    def recover_by_id(id):
        return mongo.db.venvs.find_one({"_id" : ObjectId(id)})
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# if(__name__ == '__main__'):
#     job = sys.argv[1]
#     agent:Agent = Agent(job)
#     agent.execute_job()