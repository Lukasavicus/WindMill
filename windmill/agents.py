# https://docs.python.org/3/library/typing.html
from typing import Final

import sys, os
import subprocess as sub
from flask import current_app as app

from pymongo import MongoClient
from bson.objectid import ObjectId
from apscheduler.schedulers.blocking import BlockingScheduler

import platform

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

        folder_path = os.path.sep.join(os.path.split(self.job.entry_point)[:-1])
        self.script_folder = os.path.join(app.config['UPLOAD_FOLDER'], folder_path )
        self.script_file = os.path.split(self.job.entry_point)[-1]

        self.interval = None #interval
        self.no_interval = None #no_interval

    def execute_job(self):
        # TODO: database name and collection name should be parameters
        collection = self.connection.db.jobs

        collection.find_one_and_update(
            {'_id': ObjectId(self.job._id) },
            { '$push': { 'runs' : {
                '_id' : 1,
                'started_at' : 'now()',
                'ended_at' : 'now()',
                'status' : 'ok',
                'out' : [],
                'err' : []
            } } }
        )
        
        process = sub.Popen(f"{Agent.PIPENV_CMD} run {Agent.PYTHON_CMD} -u {self.script_file}", stdout=sub.PIPE, universal_newlines=True, cwd=self.script_folder)

        while True:
            output = process.stdout.readline()
            if(process.poll() is not None):
                break
            if(output):
                collection.find_one_and_update(
                    {'_id': ObjectId(self.job._id) },
                    { '$push': { 'msgs': output.strip() } },
                    upsert = True
                )
        rc = process.poll()
        print(f"RC:>> |{rc}|")
        return rc
    
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