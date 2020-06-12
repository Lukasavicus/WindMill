








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os, sys
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
from bson.objectid import ObjectId

from windmill.models import Job, JobDAO

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

tasks = Blueprint('tasks', __name__)

# === HELPERS functions =======================================================
@tasks.route('/apl-wm-crm/test')
def test():
    sched = app.config['SCHEDULER']
    print("#"*50, "\n\n")
    print("ADDRS: ", hex(id(sched)))
    alljobs = sched.get_jobs()
    for j in alljobs:
        print(j)
    print("\n\n", sched.print_jobs(), "\n\n", "#"*50)
    return "OK" #render_template('running_t.html')
    #return render_template('test.html')
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



# === WRAPPED FUNCTIONS =======================================================
def _jobs_handler(request):
    try:
        if(request.method == "POST"):
            print("tasks", "home-POST", request.form)

            job = Job(
                    request.form['taskName'], __resolve_path(request.form['taskEntry']),
                    start_at=request.form['datetimepicker1_input'],
                    end_at=request.form['datetimepicker2_input'], schd_hours=request.form['taskCronValueHours'],
                    schd_minutes=request.form['taskCronValueMins'],schd_seconds=request.form['taskCronValueSecs']
                )
            JobDAO.insert(job)

            #print("tasks", TASKS)

        elif(request.method == "GET"):
            print("jobs", "home-GET")
        
        _jobs = JobDAO.recover()
        print("jobs", _jobs)
        if(_jobs != None):
            return {'response' : app.config['SUCCESS'], 'data' : _jobs}
        else:
            #raise Exception("Could not query 'tasks' collection. This happened because either the collection don't exist or the database refused connection")
            return {'response' : app.config['SUCCESS'], 'data' : []}
    except Exception as e:
        print("_jobs_handler", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}

def _play_task(job_id):
    try:
        print("tasks", "PLAY invoked")
        job = JobDAO.recover_by_id(job_id)
        print("Job recovered: ", job)
        if(job != None):
            job.play()
            print("Job executed ok: ", job)
            return {'response' : app.config['SUCCESS'], 'msg' : "Job "+job.name+" executed successfully"}
        else:
            return {'response' : app.config['ERROR'], 'err' : "Job with id: "+job_id+" not found", 'statusCode' : 404}
    except Exception as e:
        print("tasks", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}

def _stop_task(job_id):
    try:
        print("tasks", "STOP invoked")
        job = JobDAO.recover_by_id(job_id)
        if(job != None):
            if(job.isAlive()):
                job.stop()
                return {'response' : app.config['SUCCESS'], 'msg' : "Job "+job.name+" is now stopped"}
            else:
                return {'response' : app.config['ERROR'], 'err' : "Job "+job.name+" was not running to be paused", 'statusCode' : 403}
        else:
            return {'response' : app.config['ERROR'], 'err' : "Job with id: "+job_id+" not found", 'statusCode' : 404}
    except Exception as e:
        print("tasks", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}

def _schedule_task(job_id):
    try:
        print("tasks", "SCHEDULE invoked", job_id)
        job = JobDAO.recover_by_id(job_id)
        if(job != None):
            job.schedule()
            return {'response' : app.config['SUCCESS'], 'msg' : "Job "+job.name+" is now scheduled"}
        else:
            return {'response' : app.config['ERROR'], 'err' : "Job with id: "+job_id+" not found", 'statusCode' : 404}
    except Exception as e:
        print("tasks", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
@tasks.route('/api/tasks/', methods=["GET","POST"])
def api_tasks():
    ans = _jobs_handler(request)
    #print("="*100, "\n\n", ans, "\n\n", "="*100)
    if(ans['response'] == app.config['SUCCESS']):
        jobs = ans['data']
        jobs_json = [job.jsonify() for job in jobs]
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
                JobDAO.delete(job)
                return {'response' : app.config['SUCCESS'], 'msg' : f"Job {job.name} deleted successfully"}

            elif(request.method == "PUT"):
                if(job.no_runs != 0):
                    raise Exception("Could not update job '"+job.name+"' because this job already ran once")

                job.name = request.form['taskName'] if(request.form['taskName'].strip() != '') else job.name
                job.entry_point = request.form['taskEntry'] if(request.form['taskEntry'].strip() != '') else job.entry_point
                job.start_at = request.form['datetimepicker1_input'] if(request.form['datetimepicker1_input'].strip() != '') else job.start_at
                job.end_at = request.form['datetimepicker2_input'] if(request.form['datetimepicker2_input'].strip() != '') else job.end_at
                job.schd_hours = int(request.form['taskCronValueHours']) if(request.form['taskCronValueHours'].strip() != '') else job.schd_hours
                job.schd_minutes = int(request.form['taskCronValueMins']) if(request.form['taskCronValueMins'].strip() != '') else job.schd_minutes
                job.schd_seconds = int(request.form['taskCronValueSecs']) if(request.form['taskCronValueSecs'].strip() != '') else job.schd_seconds

                JobDAO.update(job)

            if(request.method in ["GET", "PUT"]): # "DELETE"
                return jsonify(job.jsonify())

        else:
            return {'response' : app.config['ERROR'], 'err' : "Job id: "+job_id+" could not be found", 'statusCode' : 404}
        return {'response' : app.config['ERROR'], 'err' : "/api/task does not accept this HTTP verb", 'statusCode' : 403}
    except Exception as e:
        print("tasks", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}

@tasks.route('/api/task/info/<job_id>')
def api_info_task(job_id):
    try:
        print("tasks", "INFO invoked")
        job = JobDAO.recover_by_id(job_id)
        if(job != None):
            #print("Jobs", "job is not None", job)
            return jsonify(job.jsonify())
        else:
            return {'response' : app.config['ERROR'], 'err' : "The requested job was not found", 'statusCode' : 404}
    except Exception as e:
        print("tasks", "INTERNAL ERROR", e)
        return {'response' : app.config['ERROR'], 'err' : str(e), 'statusCode' : 500}

@tasks.route('/api/task/play/<job_id>')
def api_play_task(job_id):
    ans = _play_task(job_id)
    return ans

@tasks.route('/api/task/stop/<job_id>')
def api_stop_task(job_id):
    ans = _stop_task(job_id)
    return ans

@tasks.route('/api/task/schedule/<task_id>')
def api_schedule_task(task_id):
    ans = _schedule_task(task_id)
    return ans
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@tasks.route('/', methods=["GET","POST"]) # TODO: Remove POST, to prevent when F5 pressed make a new request to this endpoint ?
def home():
    print("tasks - home()")
    ans = _jobs_handler(request)
    print("ANS ", ans)
    if(ans['response'] == app.config['SUCCESS']):
        # flash({'title' : "TASKS", 'msg' : ans['msg'], 'type' : MsgTypes['SUCCESS']})
        return render_template('tasks_view.html', jobs=ans['data'])
    else:
        flash({'title' : "ERROR", 'msg' : ans['err'], 'type' : MsgTypes['ERROR']})
        #return abort(ans['statusCode'])
        return render_template('tasks_view.html', jobs=[])

@tasks.route('/task/play/<task_id>')
def play_task(task_id):
    ans = _play_task(task_id)
    print("ANS", ans)
    if(ans['response'] == app.config['SUCCESS']):
        # flash({'title' : "TASKS", 'msg' : ans['msg'], 'type' : MsgTypes['SUCCESS']})
        return redirect(url_for('tasks.home'))
    else:
        flash({'title' : "ERROR", 'msg' : ans['err'], 'type' : MsgTypes['ERROR']})
        return abort(ans['statusCode'])

@tasks.route('/task/stop/<task_id>')
def stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans['response'] == app.config['SUCCESS']):
        return redirect(url_for('tasks.home'))
    else:
        flash({'title' : "ERROR", 'msg' : ans['err'], 'type' : MsgTypes['ERROR']})
        return abort(ans['statusCode'])

@tasks.route('/task/schedule/<task_id>')
def schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans['response'] == app.config['SUCCESS']):
        return redirect(url_for('tasks.home'))
    else:
        flash({'title' : "ERROR", 'msg' : ans['err'], 'type' : MsgTypes['ERROR']})
        return abort(ans['statusCode'])
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++