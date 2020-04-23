








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
from bson.objectid import ObjectId

from windmill.models import Job, JobDAO
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

tasks = Blueprint('tasks', __name__)

# === HELPERS functions =======================================================
@tasks.route('/test')
def test():
    return render_template('running_t.html')
    #return render_template('test.html')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



# === WRAPPED FUNCTIONS =======================================================
def _jobs_handler(request):
    try:
        if(request.method == "POST"):
            #print("tasks", "home-POST", request.form)

            job = Job(
                    request.form['taskName'], __resolve_path(request.form['taskEntry'])
                )
            JobDAO.insert(job)

            flash({'title' : "Task", 'msg' : "Task {} created.".format(job.name), 'type' : MsgTypes['SUCCESS']})
            #print("tasks", TASKS)

        elif(request.method == "GET"):
            print("jobs", "home-GET")
        jobs_to_return = JobDAO.recover()

        return {'response' : app.config['SUCCESS'], 'data' : jobs_to_return}
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("_jobs_handler", "INTERNAL ERROR", e)
        return abort(500)

def _play_task(job_id):
    try:
        #print("tasks", divisor)
        #print("tasks", "PLAY invoked ", job_id)
        #print("tasks", divisor)
        job = JobDAO.recover_by_id(job_id)
        print("jobs", "PLAY> ", job)

        if(job != None):
            
            job.play()
            
            print("tasks", "EXECUTING .. ", (os.path.join(app.config['UPLOAD_FOLDER'], job.entry_point)))
            flash({'title' : "", 'msg' : f"Job {job.name} is now running", 'type' : MsgTypes['SUCCESS']})
            return app.config['SUCCESS']
        else:
            flash({'title' : "Task Action", 'msg' : f"Job with id:{job_id} not found", 'type' : MsgTypes['ERROR']})
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

def _stop_task(job_id):
    try:
        print("tasks", "STOP invoked")
        job = JobDAO.recover_by_id(job_id)

        if(job != None):
            
            job.stop()

            print("jobs", "KILLING .. ", job.entry_point)
            flash({'title' : "Task Action", 'msg' : f"Job {job.name} is now stoped", 'type' : MsgTypes['SUCCESS']})
            return app.config['SUCCESS']
        else:
            flash({'title' : "Task Action", 'msg' : f"Job with id:{job_id} not found", 'type' : MsgTypes['ERROR']})
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

def _schedule_task(job_id):
    try:
        print("tasks", "SCHEDULE invoked")
        job = JobDAO.recover_by_id(job_id)

        if(job != None):
            print("jobs", "job is not None")
            job.schedule()
            print("tasks", "SCHEDULED .. ", (os.path.join(app.config['UPLOAD_FOLDER'], job.entry_point)))
            return app.config['SUCCESS']
        else:
            flash({'title' : "Task Action", 'msg' : "Task id:{} could not be found".format(str(job._id)), 'type' : MsgTypes['ERROR']})
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@tasks.route('/api/tasks/', methods=["GET","POST"])
def api_tasks():
    ans = _jobs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        jobs = ans['data']
        jobs_json = []
        for job in jobs:
            jobs_json.append(job.jsonify())
        return jsonify(jobs_json)
    else:
        return ans

@tasks.route('/api/task/<job_id>', methods=["DELETE", "GET", "PUT"])
def api_task(job_id):
    try:
        print("tasks", "TASK -> ", request.method, " --> ", job_id)
        job = JobDAO.recover_by_id(job_id)
        print("\n\n", job, "\n\n")
        if(job != None):
            if(request.method == "DELETE"):
                #JobDAO.delete(job)
                return app.config['SUCCESS']

            elif(request.method == "PUT"):

                # if('taskName' in request.form):
                #     task["name"] = request.form['taskName']
                # if('taskEntry' in request.form):
                #     task["entry_point"] = __resolve_path(request.form['taskEntry'])
                # task["cron"] = None
                # task["status"] = "not running"
                # task["started_at"] = datetime.now().strftime("%Y-%d-%m %H:%M:%S")

                return app.config['SUCCESS']
                
            if(request.method in ["DELETE", "GET", "PUT"]):
                return jsonify(job.jsonify())

        else:
            flash({'title' : "Task Action", 'msg' : f"Job id:{job_id} could not be found", 'type' : MsgTypes['ERROR']})
            return abort(404)
        flash({'title' : "Tasks", 'msg' : "/api/task does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
        return abort(405)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

@tasks.route('/api/task/info/<job_id>')
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

@tasks.route('/api/task/play/<job_id>')
def api_play_task(job_id):
    ans = _play_task(job_id)
    print("tasks", "PLAY return", ans, app.config['SUCCESS'], ans == app.config['SUCCESS'])
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans

@tasks.route('/api/task/stop/<job_id>')
def api_stop_task(job_id):
    ans = _stop_task(job_id)
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans

@tasks.route('/api/task/schedule/<task_id>')
def api_schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@tasks.route('/', methods=["GET","POST"]) # TODO: Remove POST, to prevent when F5 pressed make a new request to this endpoint ?
def home():
    ans = _jobs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        jobs = JobDAO.recover()
        return render_template('tasks_view.html', jobs=jobs)
    else:
        return ans

@tasks.route('/task/play/<int:task_id>')
def play_task(task_id):
    ans = _play_task(task_id)
    if(ans == app.config['SUCCESS']):
        return redirect(url_for('tasks.home'))
    else:
        return ans

@tasks.route('/task/stop/<int:task_id>')
def stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans == app.config['SUCCESS']):
        return redirect(url_for('tasks.home'))
    else:
        return ans

@tasks.route('/task/schedule/<int:task_id>')
def schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans == app.config['SUCCESS']):
        return redirect(url_for('tasks.home'))
    else:
        return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
