# https://docs.python.org/3/library/typing.html
from typing import Final

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

# === Job - Model =============================================================
class Job():
	_id = None
	name = None
	entry_point = None
	start_at = None
	end_at = None
	pid = None
	schd_hours = 0
	schd_minutes = 0
	schd_seconds = 0
	last_exec_status = STATUS['not_running']
	no_runs = 0

	def __init__(self,
			name, entry_point, _id=None, start_at=None, end_at=None, pid=None, schd_hours=0, schd_minutes=0, schd_seconds=0,
			last_exec_status=STATUS['not_running'], no_runs=0
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

		self.agent = Agent(mongo, self)

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
					'schd_seconds' : self.schd_seconds, 'start_at': self.start_at
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
			'no_runs' : job.no_runs
		})

	@staticmethod
	def delete(job):
		if(job.isAlive()):
			job.process.kill_job()
		mongo.db.jobs.delete_one( {"_id": ObjectId(job._id)})

	@staticmethod
	def _new_job(job_item):
		return Job(job_item["name"], job_item["entry_point"], job_item["_id"], job_item["start_at"], job_item["end_at"], job_item["pid"],
			job_item["schd_hours"], job_item["schd_minutes"], job_item["schd_seconds"], job_item["last_exec_status"], job_item["no_runs"])

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
	def update_when_running(job):
		mongo.db.jobs.find_one_and_update(
            {'_id': self.job._id },
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
		return mongo.db.runs.insert({
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
			{'_id': self.run._id },
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
    PIPENV_CMD:Final = "pipenv" # define the string that represents the pipenv command
    PYTHON_CMD:Final = "python" if platform.system() == "Windows" else "python3" # define the string that represents the python command

    def __init__(self, connection, job):
        self.connection:MongoClient = connection
        self.job:Job = job

        self.base_path = app.config['UPLOAD_FOLDER']

        self.run = Run(job._id, job.name, job.entry_point)

        self.interval = 'seconds' #interval
        self.no_interval = 30 #no_interval

    def execute_job(self):
        # TODO: database name and collection name should be parameters
        runs_collection = self.connection.db.runs

        # Insert run of a job into database
        self.run._id = RunDAO.insert(self.run)
        
        folder_path = os.path.sep.join(os.path.split(self.job.entry_point)[:-1])
        script_folder = os.path.join(self.base_path, folder_path )
        script_file = os.path.split(self.job.entry_point)[-1]
        
        # Trigger the run of a job in a form of a new subprocess (executing with pipenv to isolate the virtual enviroments)
        process = sub.Popen(f"{Agent.PIPENV_CMD} run {Agent.PYTHON_CMD} -u {script_file}", stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines=True, cwd=script_folder)
        
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

        self.job.status = 'SUCCESS' if(return_process_code == 0) else 'FAILED'
        
        JobDAO.update_when_finish_run(self.job)

        return return_process_code
    
    def kill_job(self):
        print("THIS AGENT:", self)
        process = self._get_process()
        if(process):
            process.kill()

    def schedule_job(self):
        print("arguments ", sys.argv)
        scheduler = BlockingScheduler()

        flag = False
        # Melhorar isso:
        if(self.interval == 'seconds'):
            scheduler.add_job(self.execute_job, 'interval', seconds=self.no_interval)
            flag = True
        elif(self.interval == 'minutes'):
            scheduler.add_job(self.execute_job, 'interval', minutes=self.no_interval)
            flag = True
        elif(self.interval == 'hours'):
            scheduler.add_job(self.execute_job, 'interval', hours=self.no_interval)
            flag = True
        
        if(flag):
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

# if(__name__ == '__main__'):
#     job = sys.argv[1]
#     agent:Agent = Agent(job)
#     agent.execute_job()