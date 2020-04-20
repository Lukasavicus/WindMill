








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
from bson.objectid import ObjectId

from windmill.daos import RunDAO
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

runs = Blueprint('runs', __name__)

# =============================================================================
def _load_jobs():
    global JOBS
    jobs_list = JobDAO.recover()
    for job_in_list in jobs_list:
        job = JobDAO(job_in_list['name'], job_in_list['entry_point'], job_in_list['start_at'], job_in_list['end_at'], job_in_list['schd_hours'], job_in_list['schd_minutes'], job_in_list['schd_seconds'])
        job._id = job_in_list['_id']
        job.last_exec_status = job_in_list['last_exec_status']
        job.no_runs = job_in_list['no_runs']
        JOBS.append(job)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === WRAPPED FUNCTIONS =======================================================
def _runs_handler(request):
    try:
        if(request.method == "GET"):
            #print("tasks", "home-GET")
            #print("tasks", divisor)
            #print("tasks", " --> TASKS", TASKS)
            #print("tasks", divisor)

            runs_to_return = RunDAO.recover()

            return {'response' : app.config['SUCCESS'], 'data' : runs_to_return}
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@runs.route('/api/runs/', methods=["GET","POST"])
def api_runs():
    ans = _runs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        return jsonify(ans['data'])
    else:
        return ans

@runs.route('/api/task/<job_id>/runs', methods=["DELETE", "GET", "PUT"])
def api_run(job_id):
    global JOBS
    try:
        print("tasks", "TASK -> ", request.method, " --> ", job_id)
        (_, job) = _filter_job_by_id(job_id)
        print("\n\n", job, "\n\n")
        if(job != None):
            
            if(request.method == "DELETE"):
                for idx, job in enumerate(JOBS):
                    if(job._id == job_id):
                        del JOBS[idx]
                job.delete()
                return app.config['SUCCESS']

            elif(request.method == "PUT"):

                # if('taskName' in request.form):
                #     task["name"] = request.form['taskName']
                # if('taskEntry' in request.form):
                #     task["entry_point"] = __resolve_path(request.form['taskEntry'])
                # task["cron"] = None
                # task["status"] = "not running"
                # task["started_at"] = datetime.now().strftime("%Y-%d-%m %H:%M:%S")

                flash({'title' : "Jobs", 'msg' : f"Job {job.name} updated with id: {job._id}.", 'type' : MsgTypes['SUCCESS']})
                
            if(request.method in ["DELETE", "GET", "PUT"]):
                return jsonify({
                    '_id': job._id, 'pid': job._pid, 'name': job.name, 'entry_point': job.entry_point,
                    'last_exec_status': job.last_exec_status, 'start_at': job.start_at})

        else:
            flash({'title' : "Task Action", 'msg' : f"Job id:{job_id} could not be found", 'type' : MsgTypes['ERROR']})
            return abort(404)
        flash({'title' : "Tasks", 'msg' : "/api/task does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
        return abort(405)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

@runs.route('/api/task/info/<int:task_id>')
def api_info_task(task_id):
    global TASKS
    try:
        print("tasks", "INFO invoked")
        (_, task) = _filter_job_by_id(task_id)
        data = ""
        if(task != None):
            print("tasks", "task is not None")
            with open((task["name"]+'.txt'), 'r') as task_file:
                data = task_file.read()
            return jsonify(data)
        else:
            flash({'title' : "Task Action", 'msg' : "Task id:{} could not be found".format(str(task['_id'])), 'type' : MsgTypes['ERROR']})
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@runs.route('/runs', methods=["GET","POST"]) # TODO: Remove POST, to prevent when F5 pressed make a new request to this endpoint ?
def home():
    ans = _runs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        return render_template('runs_view.html', runs=ans['data'])
    else:
        return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
