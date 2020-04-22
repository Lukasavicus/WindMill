# https://docs.python.org/3/library/typing.html
from typing import Final

import sys, os
import subprocess as sub
from flask import current_app as app

from pymongo import MongoClient
from bson.objectid import ObjectId
from apscheduler.schedulers.blocking import BlockingScheduler

import platform
from datetime import datetime

#from windmill.daos import JobDAO

class Agent:
    """
        This class represents in a high-level way the agent that execute some job
        directly or scheduled
    """

    PIPENV_CMD:Final = "pipenv" # define the string that represents the pipenv command
    PYTHON_CMD:Final = "python" if platform.system() == "Windows" else "python3" # define the string that represents the python command

    def __init__(self, connection, job):
        self.connection:MongoClient = connection
        self.job:JobDAO = job
        self.run_id = None
        self.process = None

        self.interval = None #interval
        self.no_interval = None #no_interval

    def execute_job(self):
        # TODO: database name and collection name should be parameters

        jobs_collection = self.connection.db.jobs
        runs_collection = self.connection.db.runs

        # Insert run of a job into database
        self.run_id = runs_collection.insert_one({
            'job_id': ObjectId(self.job._id) ,
            'started_at' : datetime.now(),
            'ended_at' : None,
            'status' : None,
            'out' : [],
            'err' : []
        }).inserted_id
        
        folder_path = os.path.sep.join(os.path.split(self.job.entry_point)[:-1])
        script_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_path )
        script_file = os.path.split(self.job.entry_point)[-1]

        # Trigger the run of a job in a form of a new subprocess (executing with pipenv to isolate the virtual enviroments)
        self.process = sub.Popen(f"{Agent.PIPENV_CMD} run {Agent.PYTHON_CMD} -u {script_file}", stdout=sub.PIPE, stderr=sub.PIPE, universal_newlines=True, cwd=script_folder)

        # Update the job info with status "RUNNING"
        jobs_collection.find_one_and_update(
            {'_id': self.job._id },
            { '$set' : {'last_exec_status' : "RUNNING" } },
            upsert = True
        )

        ended_at = None

        # Observe the output of subprocess (stdout and stderr)
        while True:
            output = self.process.stdout.readline()
            if(self.process.poll() is not None):
                print("\n\nExiting because the process is no longer alive\n\n")
                break
            if(output):
                print(f"\n\nOUTPUT: >{output}<\n\n")
                runs_collection.find_one_and_update(
                    {'_id': self.run_id },
                    { '$push': { 'out': output.strip() } },
                    upsert = True
                )

        return_proc = self.process.poll()
        actual_status = None
        run_register = list(runs_collection.find({ '_id': self.run_id } ) ) [0]
        if('status' in run_register):
            actual_status = run_register['status']

        print(f"\n\nActual Status: {actual_status}\n\n")

        if(actual_status != -1):
            if(return_proc == 1):
                print("\n\n Something goes wrong \n\n")
                error = self.process.stderr.readlines()
                print(f"\n\n The error {error} will be logged\n\n")
                if(error and len(error) != 0):
                    runs_collection.find_one_and_update(
                        {
                            '$and' : [ { '_id': self.run_id }, { 'status': { '$not': { '$eq': -1 } } } ]
                        },
                        { '$push': { 'err': '\n'.join([err.strip() for err in error]) } },
                        #upsert = True
                    )
                    print(f"\n\n The error {error} was logged\n\n")

            ended_at = datetime.now()
            runs_collection.find_one_and_update(
                {
                    '$and' : [ { '_id': self.run_id }, { 'status': { '$not': { '$eq': -1 } } } ]
                },
                { '$set' : {'status' : return_proc, 'ended_at' : ended_at } },
                upsert = True
            )

            status_str = 'SUCCESS' if(return_proc == 0) else 'FAILED'
            
            jobs_collection.find_one_and_update(
                {'_id': self.job._id },
                {
                    '$set' : {'last_exec_status' : status_str, 'end_at' : ended_at },
                    '$inc' : { 'quantity' : 1, "no_runs": 1 }
                },
                upsert = True
            )
            return return_proc
        else:
            return -1
    
    def kill_job(self):
        self.process.kill()

        jobs_collection = self.connection.db.jobs
        runs_collection = self.connection.db.runs

        ended_at = datetime.now()
        runs_collection.find_one_and_update(
            {'_id': self.run_id },
            { '$set' : {'status' : -1, 'ended_at' : ended_at } },
            upsert = True
        )

        jobs_collection.find_one_and_update(
            {'_id': self.job._id },
            { '$set' : {'last_exec_status' : "STOPPED", 'end_at' : ended_at } },
            upsert = True
        )
        print(f"\n\nJob {self.job._id} is now killed -> run_id({self.run_id}) :'( \n\n")

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


if(__name__ == '__main__'):
    job = sys.argv[1]
    agent:Agent = Agent(job)
    agent.execute_job()