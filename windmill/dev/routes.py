




# === imports =================================================================
#from flask import current_app as app
from windmill import app, db, bcrypt
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os

import subprocess as sub

from werkzeug.utils import secure_filename
import shutil

from windmill.main.utils import trace, divisor, __resolve_path, uri_sep, MsgTypes
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

dev = Blueprint('dev', __name__)


# =============================================================================
@dev.route('/dev/cmd/', methods=['GET', 'POST'])
def dev_cmd():
    print("dev_cmd")
    try:
        if(request.method == "GET"):
            return render_template("term.html")
        elif(request.method == "POST"):
            command = request.form["cmdTextArea"]
            print(type(command))
            exe = request.form["cmdExecutor"]
            
            print("Testing ", command)

            if(exe == "os"):
                os.system(command)
            elif(exe == "sub"):
                sub.Popen(command) #, cwd="."
            elif(exe == "subsp"):
                cmd = command.split(" ")
                sub.Popen(cmd) #, cwd="."
            print(command, " SUCCESS ")
            return render_template("term.html")
        #return {'response' : app.config['ERROR'], 'err' : "/api/task does not accept this HTTP verb", 'statusCode' : 403}
        flash({'title' : "ERROR", 'msg' : "/api/task does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
        return render_template("term.html")
        #abort(403)
    except Exception as e:
        print("dev", "INTERNAL ERROR", e)
        #return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}
        flash({'title' : "ERROR", 'msg' : str(e), 'type' : MsgTypes['ERROR']})
        #abort(500)
        return render_template("term.html")

def __print_APScheduler_job(job):
    import types
    _repr = []
    for attr in dir(job):
        if(attr[0] != '_' and type(getattr(job, attr)) != types.MethodType):
            _repr.append(f"{attr} : {getattr(job, attr)}")
    return ','.join(_repr)

@dev.route('/dev/process/', methods=['GET'])
def dev_process():
    print("dev_process")
    try:
        if(request.method == "GET"):
            scheduler = app.config['SCHEDULER']
            print(scheduler, dir(scheduler))
            jobs = scheduler.get_jobs()
            print(jobs)
            #json_jobs = [f"id: {job.id}, name: {job.name}, func : {func}, func_ref : {func_ref}, info: {str(job)}" for job in jobs]
            json_jobs = [f"{{ {__print_APScheduler_job(job)} }}" for job in jobs]
            json_scheduler = __print_APScheduler_job(scheduler)
            return jsonify({'jobs' : json_jobs, 'scheduler' : json_scheduler})
        
    except Exception as e:
        print("dev", "INTERNAL ERROR", e)
        flash({'title' : "ERROR", 'msg' : str(e), 'type' : MsgTypes['ERROR']})
        return render_template("term.html")


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++