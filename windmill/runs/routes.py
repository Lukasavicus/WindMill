








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
from bson.objectid import ObjectId

from windmill.models import Run, RunDAO, JobDAO
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

runs = Blueprint('runs', __name__)
context = "apl-wm-crm"

# === WRAPPED FUNCTIONS =======================================================
def _runs_handler(request):
    """
        Function that receives a request and return a response accordly the
        following rules:
        GET: Execute the method RunDAO.recover() and return a list of all jobs
        runnings.
        ERROR: This errors may occur depending on these scenarios:
            AssertionError: If the connection is refused by the database or the
            collection 'runs' don't exist.
            DatabaseError: If something goes wrong with RunDAO
    """
    try:
        if(request.method == "GET"):
            print("runs", "home-GET")
        _runs = RunDAO.recover()
        print("runs", _runs)
        if(_runs != None):
            return {'response' : app.config['SUCCESS'], 'data' : _runs}
        else:
            #raise Exception("Could not query 'runs' collection. This happened because either the collection don't exist or the database refused connection")
            return {'response' : app.config['SUCCESS'], 'data' : []}
    except Exception as e:
        print("_runs_handler", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@runs.route('/api/runs/', methods=["GET"])
def api_runs():
    ans = _runs_handler(request)
    print("api_runs", ans, jsonify(ans))
    if(ans['response'] == app.config['SUCCESS']):
        runs = ans['data']
        runs_json = [run.jsonify() for run in runs]
        return jsonify(runs_json)
    else:
        return ans

@runs.route('/api/job/<job_id>/runs', methods=["GET"])
def api_job_runs(job_id):
    try:
        if(request.method == "GET"):
            print("runs", "home-GET")
        runs = RunDAO.recover_by_job_id(job_id)
        assert runs != None, "Could not query 'runs' collection. This happened because either the collection don't exist or the database refused connection"
        runs_json = [run.jsonify() for run in runs]
        print("runs_json", runs_json)
        return jsonify(runs_json)
    except Exception as e:
        print("runs", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}

@runs.route('/api/run/<run_id>', methods=["GET"])
def api_run(run_id):
    try:
        print("runs", "RUNS -> ", request.method, " --> ", run_id)
        run = RunDAO.recover_by_run_id(run_id)
        print("\n\n> ", run, "\n\n")
        if(run != None):
            if(request.method in ["GET"]):
                return jsonify(run.jsonify())
        else:
            return {'response' : app.config['ERROR'], 'err' : "The requested run was not found", 'statusCode' : 404}
        return {'response' : app.config['ERROR'], 'err' : "/api/run does not accept this HTTP verb", 'statusCode' : 403}
    except Exception as e:
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@runs.route('/runs', methods=["GET","POST"]) # TODO: Remove POST, to prevent when F5 pressed make a new request to this endpoint ?
def home():
    ans = _runs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        return render_template('runs_view.html', runs=ans['data'])
    else:
        flash({'title' : "ERROR", 'msg' : ans['err'], 'type' : MsgTypes['ERROR']})
        return render_template('runs_view.html', runs=[])
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
