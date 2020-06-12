# https://docs.python.org/3/library/typing.html
#from typing import Final # restriction on Python > 3.8

import sys, os, platform, psutil
import subprocess as sub
from datetime import datetime
import json

from bson.objectid import ObjectId
from pymongo import MongoClient

from flask import current_app as app
from flask_login import UserMixin

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers import SchedulerAlreadyRunningError

from windmill import mongo
from windmill import db, login_manager

#import sys
#import uwsgi


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
        return "User('"+self.id+"', '"+self.username+"', '"+self.email+"')"

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

#from windmill.agents import Agent

# TODO: change to an Enum
STATUS = {}
STATUS['not_running'] = "Not Running"
STATUS['running'] = "Running"
STATUS['scheduled'] = "Scheduled"

STATUS['none'] = "-"
STATUS['failed'] = "Failed"
STATUS['success'] = "Success"
STATUS['stopped'] = "stopped"

# === Job - Model =============================================================
class Job():
    """
        This class represents in a high-level way the Job Entity, that holds
        informations about a job created by user.
    """
    _id = None
    name = None
    entry_point = None
    status = STATUS['not_running']

    scheduled = False                   # schedule property (boolean) - Flag True if Job is scheduled False otherwise
    start_at = None                     # schedule property (datetime) - When the job is scheduled to start
    end_at = None                       # schedule property (datetime) - When the job is scheduled to end
    schd_hours = 0                      # schedule property (int) - Interval of hours in which scheduled job will be executed
    schd_minutes = 0                    # schedule property (int) - Interval of minutes in which scheduled job will be executed
    schd_seconds = 0                    # schedule property (int) - Interval of seconds in which scheduled job will be executed

    pid = None                          # process property (int) - Integer number assigned by OS to identify the process

    last_exec_status = STATUS['none']    # run property - status of last execution of this job
    last_exec_started_at = None          # run property - start datetime of last execution of this job
    last_exec_ended_at = None            # run property - end datetime of last execution of this job

    no_runs = 0

    cron = None

    def __init__(self,
            name, entry_point, _id=None, status=STATUS['not_running'], scheduled=False, start_at=None, end_at=None, 
            schd_hours=0, schd_minutes=0, schd_seconds=0, pid=None, last_exec_status=STATUS['none'],
            last_exec_started_at=last_exec_started_at, last_exec_ended_at=last_exec_ended_at, no_runs=0,
            cron=None
        ):
        self.name = name
        self.entry_point = entry_point
        self._id = _id
        self.status = status
        self.scheduled = scheduled
        self.start_at = start_at
        self.end_at = end_at
        self.schd_hours = schd_hours
        self.schd_minutes = schd_minutes
        self.schd_seconds = schd_seconds
        self.pid = pid
        self.last_exec_status = last_exec_status
        self.last_exec_started_at = last_exec_started_at
        self.last_exec_ended_at = last_exec_ended_at
        self.no_runs = no_runs

        self.cron = cron if(cron) else self._cron()

        self.agent = Agent(mongo, self)

    def _cron(self):
        h = f"*/{str(self.schd_hours)}" if(self.schd_hours != 0) else '*'
        m = f"*/{str(self.schd_minutes)}" if(self.schd_minutes != 0) else '*'
        s = f"*/{str(self.schd_seconds)}" if(self.schd_seconds != 0) else '*'
        return f"{h} {m} {s} * *"

    def isAlive(self):
        """ Returns if a Job still running or if is scheduled"""
        print("isAlive: ", self.agent.isRunning(), self.agent.isScheduled())
        print("the Running Agent:", self.agent)
        print("AGENT ADDRESS:", hex(id(self.agent)))
        return self.agent.isRunning() or self.agent.isScheduled()

    def play(self):
        """ Call the agent function to execute the Job """
        print("Job - play:", self.agent)
        self.agent.execute_job()

    def stop(self):
        """ Call the agent function to kill the Job """
        print("Job - stop:", self.agent)
        self.agent.kill_job()

    def schedule(self):
        """ Call the agent function to execute the scheduling the Job """
        print("Job - schedule:", self.agent)
        self.agent.schedule_job()

    def jsonify(self):
        """ Return a JSON representation of the Job """
        return {
                    '_id': str(self._id), 'name': self.name, 'entry_point': self.entry_point,
                    'status': self.status, 'start_at': self.start_at, 'end_at': self.end_at,
                    'no_runs': self.no_runs, 'pid': self.pid, 'last_exec_status': self.last_exec_status,
                    'last_exec_started_at': self.last_exec_started_at, 'last_exec_ended_at': self.last_exec_ended_at,
                    'schd_hours': self.schd_hours, 'schd_minutes': self.schd_minutes, 'schd_seconds': self.schd_seconds, 
                    'cron': self.cron, 'path_to_entry_point': os.path.sep.join(self.entry_point.split(os.path.sep)[:-1]),
                    'file_of_entry_point': self.entry_point.split(os.path.sep)[-1]
                }

    def __repr__(self):
        return "JOB: id["+str(self._id)+"] name["+self.name+"] scheduled["+str(self.scheduled)+"]"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === Job - Data Access Object ================================================
class JobDAO():
    """
        Class that holds all methods to access data of Job in DataBase.
    """
    def __init__(self):
        Exception('This class should not be instantiated')

    @staticmethod
    def insert(job):
        """ Insert a instance of Job into database """
        mongo.db.jobs.insert({
            'name' : job.name,
            'entry_point' : job.entry_point,
            'status' : job.status,
            'scheduled' : job.scheduled,
            'start_at' : job.start_at,
            'end_at' : job.end_at,
            'no_runs' : job.no_runs,
            'pid' : job.pid,
            'schd_hours' : job.schd_hours,
            'schd_minutes' : job.schd_minutes,
            'schd_seconds' : job.schd_seconds,
            'last_exec_status' : job.last_exec_status,
            'last_exec_started_at' : job.last_exec_started_at,
            'last_exec_ended_at' : job.last_exec_ended_at,
            'cron' : job.cron
        })
    
    @staticmethod
    def _mark_job_to_delete(job):
        """
            >private< update the registry of a Job to 'deleted' as none Job is
            really deleted (for audition reasons)
        """
        return mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            { '$set' : {'deleted_flag' : True } },
            upsert = True
        ) and RunDAO._mark_associated_runs_of_a_job_to_delete(job)

    @staticmethod
    def delete(job):
        """ delete a Job of database """
        if(job.isAlive() and hasattr(job, 'process') and job.process != None):
            job.process.kill_job()
        #print("Delete by id:", job)
        return JobDAO._mark_job_to_delete(job)
        #mongo.db.jobs.delete_one( {"_id": ObjectId(job._id)})

    @staticmethod
    def _new_job(job_item):
        """ Create a new instance of Job based on database-object (job_item) """
        return Job(job_item["name"], job_item["entry_point"], job_item["_id"], job_item["status"], job_item["scheduled"],
            job_item["start_at"], job_item["end_at"], job_item["schd_hours"], job_item["schd_minutes"], job_item["schd_seconds"],
            job_item["pid"], job_item["last_exec_status"], job_item["last_exec_started_at"], job_item["last_exec_ended_at"],
            job_item["no_runs"], job_item["cron"])

    @staticmethod
    def recover():
        """ Returns a list of Jobs (filter every 'non deleted' Job) """
        job_list = list(mongo.db.jobs.find({"deleted_flag" : {"$ne" : True}}))
        if(len(job_list) == 0):
            return None
        else:
            jobs = [JobDAO._new_job(job_item) for job_item in job_list]
            return jobs

    @staticmethod
    def update(job):
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            { '$set' : {
                'name' : job.name,
                'entry_point' : job.entry_point,
                'status' : job.status,
                'scheduled' : job.scheduled,
                'start_at' : job.start_at,
                'end_at' : job.end_at,
                'no_runs' : job.no_runs,
                'pid' : job.pid,
                'schd_hours' : job.schd_hours,
                'schd_minutes' : job.schd_minutes,
                'schd_seconds' : job.schd_seconds,
                'last_exec_status' : job.last_exec_status,
                'last_exec_started_at' : job.last_exec_started_at,
                'last_exec_ended_at' : job.last_exec_ended_at,
                'cron' : job.cron
            } },
            upsert = True
        )

    @staticmethod
    def update_when_running(job):
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            { '$set' : {'status' : STATUS['running'], 'pid' : job.pid, 'last_exec_started_at' : datetime.now() } },
            upsert = True
        )

    @staticmethod
    def update_when_finish_run(job):
        print("update_when_finish_run", job)
        status = STATUS['not_running'] if job.scheduled == False else STATUS['scheduled']
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            {
                '$set' : {
                    'status' : status,
                    'last_exec_status' : job.last_exec_status,
                    'last_exec_ended_at' : job.last_exec_ended_at
                },
                '$inc' : { 'quantity' : 1, "no_runs": 1 }
            },
            upsert = True
        )

    @staticmethod
    def update_when_schedule_change(job):
        print("update_when_schedule_change", job)
        status = STATUS['not_running'] if job.scheduled == False else STATUS['scheduled']
        mongo.db.jobs.find_one_and_update(
            {'_id': job._id },
            { '$set' : { 'status' : status } },
            upsert = True
        )

    @staticmethod
    def recover_by_id(id):
        job_item = mongo.db.jobs.find_one({"$and" : [ {'_id' : ObjectId(id)}, { "deleted_flag" : {"$ne" : True} } ] })
        if(job_item == None):
            return None
        else:
            return JobDAO._new_job(job_item)

    @staticmethod
    def delete_by_id(job):
        return JobDAO._mark_job_to_delete(job)
        #return mongo.db.jobs.delete_one( {"_id": ObjectId(id)})
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

    def __init__(self, job_id, job_name, job_entry_point, _id=None, started_at=None, ended_at=None, status=None, out=[], err=[]):
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
        """ Return a JSON representation of the Run """
        return {
                    '_id': str(self._id), 'ended_at' : self.ended_at, 'err' : self.err, 
                    'job_entry_point': self.job_entry_point, 'job_id': str(self.job_id), 'job_name': self.job_name,
                    'out': self.out, 'started_at' : self.started_at, 'status' : self.status
                }

    def __repr__(self):
        return "RUN: id["+str(self._id)+"] name["+self.job_name+"]"
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
        if(run_list == None or len(run_list) == 0):
            return None
        else:
            runs = [RunDAO._new_run(run_item) for run_item in run_list]
            return runs

    @staticmethod
    def _mark_associated_runs_of_a_job_to_delete(job):
        return mongo.db.runs.update_many(
            {"job_id": ObjectId(job._id)},
            { '$set' : {'deleted_flag' : True } },
            upsert = True
        )

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
        run_list = list(mongo.db.runs.find({"deleted_flag" : {"$ne" : True}}))
        return RunDAO._new_run_list(run_list)

    @staticmethod
    def recover_by_job_id(id):
        run_list = list(mongo.db.runs.find({"$and" : [ {"job_id" : ObjectId(id)}, { "deleted_flag" : {"$ne" : True} } ] }))
        return RunDAO._new_run_list(run_list)

    @staticmethod
    def recover_by_run_id(id):
        run_item = mongo.db.jobs.find_one({"$and" : [ {'_id' : ObjectId(id)}, { "deleted_flag" : {"$ne" : True} } ] })
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
    PYTHON_CMD = "python" if platform.system() == "Windows" else "python3.7" # define the string that represents the python command

    def __init__(self, connection, job):
        self.connection = connection
        self.job = job

        self.base_path = app.config['UPLOAD_FOLDER']

        self.run = Run(job._id, job.name, job.entry_point)

        self.interval = 'seconds' #interval
        self.no_interval = 30 #no_interval


    def _set_status(self, return_code):
        if(return_code == 0):
            return STATUS['success']
        elif(return_code == 1):
            return STATUS['failed']
        elif(return_code == 15):
            return STATUS['stopped']
        else:
            return STATUS['failed']

    def execute_job(self):
        print("Agent - execute_job")
        # TODO: database name and collection name should be parameters
        runs_collection = self.connection.db.runs

        # Insert run of a job into database
        self.run._id = RunDAO.insert(self.run)
        
        folder_path = os.path.sep.join(os.path.split(self.job.entry_point)[:-1])
        script_folder = os.path.join(self.base_path, folder_path)
        script_file = os.path.split(self.job.entry_point)[-1]

        args = [
            #Agent.PIPENV_CMD, "run",
            Agent.PYTHON_CMD, "-u", script_file]

        print("EXEC:", f"{Agent.PIPENV_CMD} run {Agent.PYTHON_CMD} -u {script_file}", " ON: ", script_folder)
        
        # Trigger the run of a job in a form of a new subprocess (executing with pipenv to isolate the virtual enviroments)
        #process = sub.Popen(Agent.PIPENV_CMD+" run "+Agent.PYTHON_CMD+" -u "+script_file, stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines=True, cwd=script_folder)
        process = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines=True, cwd=script_folder)        
		
        #print("process:", process)

        # Update the job info with status "RUNNING"
        self.job.pid = process.pid
        JobDAO.update_when_running(self.job)
        
        # Observe the output of subprocess (stdout and stderr)
        while True:
            output = process.stdout.readline()
            if(process.poll() is not None):
                #print("\n\nExiting because the process is no longer alive\n\n")
                break
            if(output):
                #print("\n\nOUTPUT: >", output, "<\n\n")
                RunDAO.update_add_output(self.run ,output.strip())

        return_process_code = process.returncode
        actual_status = None
        run_register = list(runs_collection.find({ '_id': self.run._id } ) ) [0]
        if('status' in run_register):
            actual_status = run_register['status']
            #print("\n\nActual Status: ", actual_status)

        print(">> ", return_process_code, actual_status, run_register)

        if(return_process_code == 1):
            #print("\n\n Something goes wrong \n\n")
            error = process.stderr.readlines()
            #print("\n\n The error ", error, " will be logged\n\n")
            if(error and len(error) != 0):
                RunDAO.update_add_error(self.run, error)
                #print("\n\n The error ", error, " was logged\n\n")
        
        self.job.last_exec_ended_at = datetime.now()
        self.run.ended_at = self.job.last_exec_ended_at
        self.run.status = self._set_status(return_process_code)

        RunDAO.update_when_finish_run(self.run)

        self.job.last_exec_status = self._set_status(return_process_code)
        
        JobDAO.update_when_finish_run(self.job)

        return return_process_code
    
    def kill_job(self):
        """
            obs.: Notice that we don't need to set the Job status neither the
            Run status, because an interruption of the process will be captured
            in the execute_job method
        """
        # If the job agent is running try to stop it
        print(f"\n\nkilling job: running? {self.isRunning()} scheduled? {self.isScheduled()}", "\n\n")
        if(self.isRunning()):
            process = self._get_process()
            if(process):
                process.kill()

        if(self.isScheduled()):
            scheduler = app.config['SCHEDULER']
            try:
                scheduler.remove_job(str(self.job._id))
                #print("Job with id "+str(self.job._id)+" was Scheduled! but now we are removing it")
                self.job.scheduled = False
                JobDAO.update_when_schedule_change(self.job)
            except Exception as e:
                print("models - Agent:kill_job: Error: ", e)
                raise Exception("Job with id "+str(self.job._id)+" was not scheduled")

    def schedule_job(self):
        #print("models - Agent:schedule_job ")
        scheduler = app.config['SCHEDULER']
        # TODO: Fix integer conversion (when hour or min or secs is '*')
        kwargs = {
            'id' : str(self.job._id),
            'start_date' : self.job.start_at,
            'end_date' : self.job.start_at,
            'hours' : int(self.job.schd_hours),
            'minutes' : int(self.job.schd_minutes),
            'seconds' : int(self.job.schd_seconds),
        }
        #scheduler.add_interval_job(self.execute_job, 'interval', **kwargs)
        options = {k : v for k,v in kwargs.items() if kwargs[k]}
        #print("Options: ", options)

        self.job.scheduled = True
        JobDAO.update_when_schedule_change(self.job)

        # TODO: add identifier for job
        scheduler.add_job(self.execute_job, 'interval', **options)

    def isScheduled(self):
        scheduler = app.config['SCHEDULER']
        try:
            returned_job = scheduler.get_job(str(self.job._id))
            #return True
            return returned_job != None
        except:
            return False

    def isRunning(self):
        process = self._get_process()
        return (process != None and hasattr(process, 'is_running') and process.is_running())

    def _get_process(self):
        try:
            process = psutil.Process(self.job.pid)
        except:
            return None
        return process
    
    def __repr__(self):
        return f"Agent: {{ Job: {self.job}; Run: {self.run}; interval: {self.interval}; no_interval: {self.no_interval} }}"
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

class Package:
    _id = None

    def __init__(self, name, version_specifier="", version=""):
        self.name = name
        self.version_specifier = version_specifier
        self.version = version
    
    def jsonify(self):
        return {'name' : self.name, 'version_specifier' : self.version_specifier, 'version' : self.version}

    def __repr__(self):
        return dict("{'name' : '"+self.name+"', 'version_specifier' : '"+self.version_specifier+"', 'version' : '"+self.version+"'}")

class VEnvironment:
    _id = None

    def __init__(self, name, _id=None, packages=[]):
        self.name = name
        self._id = _id
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
        return { '_id': str(self._id), 'name' : self.name, 'packages' : self.packages }

    def __repr__(self):
        return "VENV: id["+str(self._id)+"] name["+self.name+"] pakgs[" + ''.join([str(pkg) for pkg in self.packages]) + "]"


# === VEnvironment - Data Access Object =======================================
class VEnvironmentDAO():
    def __init__(self):
        Exception('This class should not be instantiated')

    @staticmethod
    def _new_venv(venv_item):
        # TODO: Investigate why I can't print the packages
        packages = [Package(pkg_dict['name'], pkg_dict['version_specifier'], pkg_dict['version']) for pkg_dict in venv_item["packages"]]
        venv = VEnvironment(venv_item["name"], venv_item["_id"], packages)
        return venv
    
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
        pkgs = [dict(pkg) for pkg in venv.packages]
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