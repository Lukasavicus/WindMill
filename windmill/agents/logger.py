from pymongo import MongoClient
from bson.objectid import ObjectId
import subprocess as sub
import sys
import os

def execute_job(path_to_script, verbose=False):

    client = MongoClient('mongodb://localhost:27017/') # TODO parametizer it
    db = client.test
    collection = db.log

    _id = collection.insert_one({
        'msgs' : []
    }).inserted_id

    if(verbose):
        print(f"script {path_to_script} is about to start")
    
    #process = sub.Popen(f"python -u {script}", stdout=sub.PIPE, universal_newlines=True) # outputter.py
    script_folder = os.path.sep.join(os.path.split(path_to_script)[:-1])
    script_file = os.path.split(path_to_script)[-1]

    process = sub.Popen(f"pipenv run python -u {script_file}", stdout=sub.PIPE, universal_newlines=True, cwd=script_folder) # outputter.py
    while True:
        output = process.stdout.readline()
        if(process.poll() is not None):
            break
        if(output):
            res = collection.find_one_and_update(
                {'_id': ObjectId(_id) },
                { '$push': { 'msgs': output.strip() } },
                upsert = True
            )
            if(verbose):
                print("Operation result: ", res)
    rc = process.poll()
    return rc

def main(job):
    execute_job(job)

if(__name__ == '__main__'):
    job = sys.argv[1]
    main(job)