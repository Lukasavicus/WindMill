








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
from bson.objectid import ObjectId

from windmill.models import Run, RunDAO
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

runs = Blueprint('runs', __name__)
context = "apl-wm-crm"

# === WRAPPED FUNCTIONS =======================================================
def _runs_handler(request):
    try:
        if(request.method == "GET"):
            print("runs", "home-GET")
        runs_to_return = RunDAO.recover()

        return {'response' : app.config['SUCCESS'], 'data' : runs_to_return}
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("_runs_handler", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@runs.route(f'/{context}/api/runs/', methods=["GET"])
def api_runs():
    ans = _runs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        runs = ans['data']
        runs_json = []
        for run in runs:
            runs_json.append(run.jsonify())
        return jsonify(runs_json)
    else:
        return ans

@runs.route(f'/{context}/api/job/<job_id>/runs', methods=["GET"])
def api_job_runs(job_id):
    try:
        if(request.method == "GET"):
            print("runs", "home-GET")
        #jobs = ans['data'] #
        runs = RunDAO.recover_by_job_id(job_id)
        runs_json = []
        for run in runs:
            runs_json.append(run.jsonify())
        return jsonify(runs_json)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("_runs_handler", "INTERNAL ERROR", e)
        return abort(500)

@runs.route(f'/{context}/api/run/<run_id>', methods=["GET"])
def api_run(run_id):
    try:
        print("runs", "RUNS -> ", request.method, " --> ", run_id)
        run = RunDAO.recover_by_run_id(run_id)
        print("\n\n", run, "\n\n")
        if(run != None):
            if(request.method in ["GET"]):
                return jsonify(run.jsonify())
        else:
            flash({'title' : "Task Action", 'msg' : f"Job id:{run_id} could not be found", 'type' : MsgTypes['ERROR']})
            return abort(404)
        flash({'title' : "Tasks", 'msg' : "/api/run does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
        return abort(405)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("api_run", "INTERNAL ERROR", e)
        return abort(500)

@runs.route(f'/{context}/api/task/info/<job_id>')
def api_info_task(job_id):
    try:
        print("tasks", "INFO invoked")
        job = JobDAO.recover_by_id(job_id)
        if(job != None):
            print("Jobs", "job is not None", job)
            #return jsonify(data)
        else:
            flash({'title' : "Job Action", 'msg' : "Job id:{} could not be found".format(str(job._id)), 'type' : MsgTypes['ERROR']})
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@runs.route(f'/{context}/runs', methods=["GET","POST"]) # TODO: Remove POST, to prevent when F5 pressed make a new request to this endpoint ?
def home():
    ans = _runs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        runs = RunDAO.recover()
        return render_template('runs_view.html', runs=runs)
    else:
        return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
