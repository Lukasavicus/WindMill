








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
from bson.objectid import ObjectId

from windmill.daos import JobDAO
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === globals and config ======================================================
JOBS = [] #THIS SHOULD BE CHANGED IN FUTURE FOR SOME DATABASE MODEL DATA REPRESENTATION
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

tasks = Blueprint('tasks', __name__)

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


# === HELPERS functions =======================================================
@tasks.route('/test')
def test():
    return render_template('running_t.html')
    #return render_template('test.html')

def _filter_job_by_id(_id):
    print("_filter_job_by_id")
    global JOBS
    selected_job_arr = list(filter(lambda job : (job._id == ObjectId(_id)), JOBS))
    selected_job = None
    if(len(selected_job_arr) > 0):
        selected_job = selected_job_arr[0]
    return (selected_job_arr, selected_job)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



# === WRAPPED FUNCTIONS =======================================================
def _jobs_handler(request):
    global JOBS
    try:
        if(request.method == "POST"):
            #print("tasks", "home-POST", request.form)

            jobDAO = JobDAO(
                    request.form['taskName'], __resolve_path(request.form['taskEntry'])
                )
            jobDAO.insert()

            _load_jobs() # TODO: eliminate the need of query all jobs by getting the _id of inserted job

            flash({'title' : "Task", 'msg' : "Task {} created.".format(jobDAO.name), 'type' : MsgTypes['SUCCESS']})
            #print("tasks", TASKS)

        elif(request.method == "GET"):
            #print("tasks", "home-GET")

            for job in JOBS:
                job.last_exec_status = "running" if(job.isAlive()) else "not running"
        
        #print("tasks", divisor)
        #print("tasks", " --> TASKS", TASKS)
        #print("tasks", divisor)

        jobs_to_return = JobDAO.recover()

        return {'response' : app.config['SUCCESS'], 'data' : jobs_to_return}
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)

def _play_task(job_id):
    global JOBS
    try:
        print("tasks", divisor)
        print("tasks", "PLAY invoked ", job_id)
        print("tasks", divisor)
        (_, job) = _filter_job_by_id(job_id)
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
    global JOBS
    try:
        print("tasks", "STOP invoked")
        (_, job) = _filter_job_by_id(job_id)

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

def _schedule_task(task_id):
    global TASKS
    try:
        print("tasks", "SCHEDULE invoked")
        (_, task) = _filter_job_by_id(task_id)

        if(task != None):
            print("tasks", "task is not None")
            p = sub.Popen([(app.config['python_cmd'] + ' '), '.\executor.py', (os.path.join(app.config['UPLOAD_FOLDER'], task["entry_point"])), "seconds", "90"])
            TASKS[task_id]["pointer"] = p
            TASKS[task_id]["pid"] = p.pid
            TASKS[task_id]["status"] = "running (schdl)"
            print("tasks", "SCHEDULED .. ", (os.path.join(app.config['UPLOAD_FOLDER'], task["entry_point"])))
            return app.config['SUCCESS']
        else:
            flash({'title' : "Task Action", 'msg' : "Task id:{} could not be found".format(str(task['_id'])), 'type' : MsgTypes['ERROR']})
            return abort(404)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@tasks.route('/api/tasks/', methods=["GET","POST"])
def api_tasks():
    global TASKS
    ans = _jobs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        return jsonify(ans['data'])
    else:
        return ans

@tasks.route('/api/task/<job_id>', methods=["DELETE", "GET", "PUT"])
def api_task(job_id):
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

@tasks.route('/api/task/info/<int:task_id>')
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

@tasks.route('/api/task/play/<int:task_id>')
def api_play_task(task_id):
    ans = _play_task(task_id)
    print("tasks", "PLAY return", ans, app.config['SUCCESS'], ans == app.config['SUCCESS'])
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans

@tasks.route('/api/task/stop/<int:task_id>')
def api_stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans == app.config['SUCCESS']):
        return jsonify(success=True)
    else:
        return ans

@tasks.route('/api/task/schedule/<int:task_id>')
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
    global TASKS
    ans = _jobs_handler(request)
    if(ans['response'] == app.config['SUCCESS']):
        return render_template('tasks_view.html', tasks=ans['data'])
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

_load_jobs()
print("\n\nJOBS>>", JOBS, "\n\n\n")