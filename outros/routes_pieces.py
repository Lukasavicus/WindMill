
# === imports =================================================================
#from flask import *
from flask import flash, render_template, redirect, abort, jsonify, request, url_for
from flask import send_file
import os
import sys
import subprocess as sub
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from zipfile import ZipFile
import shutil

from windmill import app
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === globals and config ======================================================
tasks = [] #THIS SHOULD BE CHANGED IN FUTURE FOR SOME DATABASE MODEL DATA REPRESENTATION
TRACE = True
divisor = "\n"*3+"="*50+"\n"*3
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === HELPERS functions =======================================================
@app.route('/test')
def test():
    return render_template('running_t.html')
    #return render_template('test.html')

def _filter_task_by_id_or_name(name_id):
    global tasks
    selected_task_arr = list(filter(lambda task : (task["name"] == name_id or task["id"] == str(name_id)), tasks))
    selected_task = None
    if(len(selected_task_arr) > 0):
        selected_task = selected_task_arr[0]
    return (selected_task_arr, selected_task)

def isAlive(task):
    return (task["pointer"] != None and task["pointer"].poll() == None)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === WRAPPED FUNCTIONS =======================================================
def _play_task(task_id):
    global tasks
    try:
        print(divisor)
        print("PLAY invoked ", task_id)
        print(divisor)
        (_, task) = _filter_task_by_id_or_name(task_id)
        print("PLAY> ", task)

        if(task != None):
            print(divisor)
            print(app.config['python_cmd'] + " ", os.path.join(app.config['UPLOAD_FOLDER'], task["entry"]))
            print(divisor)
            log = open((task["name"]+'.txt'), 'a')  # so that data written to it will be appended
            #p = sub.Popen(['python3 ', (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"]))], stdout=log)
            p = sub.Popen([(app.config['python_cmd'] + ' '), (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"]))], stdout=log)
            tasks[task_id]["pointer"] = p
            tasks[task_id]["pid"] = p.pid
            tasks[task_id]["status"] = "running"
            print("EXECUTING .. ", (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"])))
            return app.config['SUCCESS']
        else:
            return abort(404)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)

def _stop_task(task_id):
    global tasks
    try:
        print("STOP invoked")
        (_, task) = _filter_task_by_id_or_name(task_id)

        if(task != None):
            tasks[task_id]["pointer"].kill()
            tasks[task_id]["status"] = "not active"
            print("KILLING .. ", task["entry"])
            return app.config['SUCCESS']
        else:
            return abort(404)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)

def _schedule_task(task_id):
    global tasks
    try:
        print("SCHEDULE invoked")
        (_, task) = _filter_task_by_id_or_name(task_id)

        if(task != None):
            print("task is not None")
            p = sub.Popen([(app.config['python_cmd'] + ' '), '.\executor.py', (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"])), "seconds", "90"])
            tasks[task_id]["pointer"] = p
            tasks[task_id]["pid"] = p.pid
            tasks[task_id]["status"] = "running (schdl)"
            print("SCHEDULED .. ", (os.path.join(app.config['UPLOAD_FOLDER'], task["entry"])))
            return app.config['SUCCESS']
        else:
            return abort(404)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === API routes ==============================================================
# --- API/TASKS routes --------------------------------------------------------
@app.route('/api/tasks/', methods=["GET","POST"])
def running():
    global tasks
    try:
        if(request.method == "POST"):
            print("POST")
            print(request.form)

            tasks.append({
                    "id" : str(len(tasks)),
                    "pid" : None,
                    "name" : request.form['taskName'],
                    "entry" : request.form['taskEntry'],
                    "cron" : "{} {} {} {} {}".format(
                        '/s' if request.form['datetimepicker1_input'] else '-',
                        request.form['taskCronValueHours'],
                        request.form['taskCronValueMins'],
                        request.form['taskCronValueSecs'],
                        '/e' if request.form['datetimepicker2_input'] else '-',
                    ),
                    "pointer" : None,
                    "status" : "not running",
                    "started_at" : datetime.now().strftime("%Y-%d-%m %H:%M:%S")
                })
            return redirect('/') #render_template('running.html', tasks=tasks)
        elif(request.method == "GET"):
            print("GET")
            for idx, task in enumerate(tasks):
                tasks[idx]["status"] = "running" if(isAlive(task)) else "not running"
            return jsonify(list(map(lambda task : {
                'id': task['id'], 'pid': task['pid'], 'name': task['name'], 'entry': task['entry'],
                'cron': task['cron'], 'status': task['status'], 'started_at': task['started_at']}, list(filter(lambda task :
                task['status'] != 'deleted' ,tasks)))))
        return abort(404)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)


@app.route('/api/task/<int:task_id>', methods=["DELETE", "GET"])
def task(task_id):
    global tasks
    try:
        print("TASK -> ", request.method, " --> ", task_id)
        if(request.method == "DELETE"):
            (_, task) = _filter_task_by_id_or_name(task_id)
            if(task != None):
                if(tasks[task_id]["pointer"]):
                    tasks[task_id]["pointer"].kill()
                tasks[task_id]["status"] = "deleted"
                return app.config['SUCCESS']
            else:
                return abort(404)
        elif(request.method == "GET"):
            (_, task) = _filter_task_by_id_or_name(task_id)
            if(task != None):
                return jsonify({
                    'id': task['id'], 'pid': task['pid'], 'name': task['name'], 'entry': task['entry'],
                    'cron': task['cron'], 'status': task['status'], 'started_at': task['started_at']})
            else:
                return abort(404)
        return abort(405)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)

@app.route('/api/task/info/<int:task_id>')
def info_task(task_id):
    global tasks
    try:
        print("INFO invoked")
        (_, task) = _filter_task_by_id_or_name(task_id)
        data = ""
        if(task != None):
            print("task is not None")
            with open((task["name"]+'.txt'), 'r') as task_file:
                data = task_file.read()
            return jsonify(data)
        else:
            return abort(404)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)

@app.route('/api/task/play/<int:task_id>')
def api_play_task(task_id):
    ans = _play_task(task_id)
    if(ans == app.config['SUCCESS']):
        jsonify(success=True)
    else:
        return ans

@app.route('/api/task/stop/<int:task_id>')
def api_stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans == app.config['SUCCESS']):
        jsonify(success=True)
    else:
        return ans

@app.route('/api/task/schedule/<int:task_id>')
def api_schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans == app.config['SUCCESS']):
        jsonify(success=True)
    else:
        return ans


# --- API/FS routes -----------------------------------------------------------
@app.route('/api/fs', defaults={'req_path': ''})
@app.route('/api/fs/<path:req_path>', methods=['GET', 'DELETE'])
def dir_listing_api(req_path):
    trace('dir_listing_api')
    try:
        abs_path = _get_req_absolute_path(req_path)
        (files_info, locations, isRoot) = _dir_listing(req_path)
        if(request.method == "DELETE"):
            assert req_path.count('/') == 0, "Selected path '{}' is not a root directory. Delete are allowed only in roots directories".format(req_path)
            shutil.rmtree(abs_path)
            abs_path = app.config['UPLOAD_FOLDER']
        # elif(request.method == "DELETE"):
        return jsonify ({'files_info' : files_info, 'locations' : locations})
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

# === Application routes ======================================================
# -----------------------------------------------------------------------------
@app.route('/')
def home():
    global tasks
    error = ''
    try:
        if(request.method == "POST"):
            print("POST")
            print(request.form)

            tasks.append({
                    "id" : str(len(tasks)),
                    "pid" : None,
                    "name" : request.form['taskName'],
                    "entry" : request.form['taskEntry'],
                    "cron" : None,
                    "pointer" : None,
                    "status" : "not running",
                    "no_runs" : 0,
                    "started_at" : datetime.now().strftime("%Y-%d-%m %H:%M:%S")
                })
            print(tasks)

        elif(request.method == "GET"):
            for idx, task in enumerate(tasks):
                tasks[idx]["status"] = "running" if(isAlive(task)) else "not running"
            print("GET")
        return render_template('running.html', tasks=tasks)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)

@app.route('/task/play/<int:task_id>')
def play_task(task_id):
    ans = _play_task(task_id)
    if(ans == app.config['SUCCESS']):
        redirect('/')
    else:
        return ans

@app.route('/task/stop/<int:task_id>')
def stop_task(task_id):
    ans = _stop_task(task_id)
    if(ans == app.config['SUCCESS']):
        redirect('/')
    else:
        return ans

@app.route('/task/schedule/<int:task_id>')
def schedule_task(task_id):
    ans = _schedule_task(task_id)
    if(ans == app.config['SUCCESS']):
        redirect('/')
    else:
        return ans

# -----------------------------------------------------------------------------
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if(request.method == 'POST'):
        # check if the post request has the file part
        if('file' not in request.files):
            #flash('No file part')
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if(file.filename == ''):
            #flash('No selected file')
            print('No selected file')
            return redirect(request.url)
        if(file):# and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_filename)
            
            print('extracting', full_filename)
            
            #foldername = filename.split('.')[0]
            foldername = os.path.join(request.form['venvName'], filename.split('.')[0])
            full_foldername = os.path.join(app.config['UPLOAD_FOLDER'], foldername)

            os.mkdir(full_foldername)
            
            with ZipFile(full_filename, 'r') as zipObj:
                # Extract all the contents of zip file in current directory
                zipObj.extractall(full_foldername)
            print('Finished')
            os.remove(full_filename)

            (files_info, locations, isRoot) = _dir_listing('')
            return render_template('files.html', files_info=files_info, locations=locations, isRoot=isRoot)
    elif(request.method == 'GET'):
        (files_info, locations, isRoot) = _dir_listing('')
        return render_template('files.html', files_info=files_info, locations=locations, isRoot=isRoot)
    return abort(405)

# -----------------------------------------------------------------------------

# HELPERS
def _get_root_archives_folders():
    BASE_DIR = "./{}/".format(app.config['UPLOAD_FOLDER'])
    root_folders = []
    #for f in os.

def _get_req_absolute_path(requested_path):
    """
        Given a :requested_path return the complete path for that resource.
        e.g.: venv_a/etl_archive_a/subdir_1/etl_script.py => 
        windmill/uploads/venv_a/etl_archive_a/subdir_1/etl_script.py
    """
    trace('_get_req_absolute_path')
    BASE_DIR = app.config['UPLOAD_FOLDER'] #"./{}/".format(app.config['UPLOAD_FOLDER'])
    return os.path.join(BASE_DIR, requested_path)

def trace(function_name):
    if(TRACE):
        print(function_name)

def _get_resource_tree(req_path):
    """
        Given a :requested_path split this path into array that represents the
        tree to that resource in server's uploaded-resources-folder (uploads).
        e.g.: venv_a/etl_archive_a/subdir_1/etl_script.py =>
        [venv_a, etl_archive_a, subdir_1, etl_script.py]
    """
    #path_parts = abs_path.split('/')[2:]
    #path_parts = abs_path.split('/')[1:]
    return req_path.split('/')

def _dir_listing(req_path=''):
    trace('_dir_listing')
    abs_path = _get_req_absolute_path(req_path)
    print(divisor)
    print("name", __name__, "app.root_path", app.root_path, "req_path", req_path, "abs_path", abs_path)
    print(divisor)
    # Return 404 if path doesn't exist
    if(not os.path.exists(abs_path)):
        return abort(404)

    # Show directory contents
    files = os.listdir(abs_path)
    files_info = []
    for i, file_ in enumerate(files):
        path = os.path.join(req_path, file_)
        full_path = os.path.join(abs_path, file_)
        files_info.append({'path' : path, 'name' : file_, 'file_folder_flag' : os.path.isdir(full_path)})
        #print(file_, " X ", files[i])

    locations = [{'name' : '/', 'path' : '/fs'}]
    resource_tree = _get_resource_tree(req_path)

    print("resource_tree", resource_tree)
    for i, resource_tree_element in enumerate(resource_tree):
        print("resource_tree_element", resource_tree_element)
        locations.append({'name' : resource_tree_element, 'path' : ('/fs/' + '/'.join(resource_tree[:i+1]))})

    isRoot = len(resource_tree) == 1

    return (files_info, locations, isRoot)

@app.route('/fs', defaults={'req_path': ''})
@app.route('/fs/<path:req_path>')
def dir_listing(req_path):
    print(divisor)
    trace('dir_listing')
    abs_path = _get_req_absolute_path(req_path)
    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)
    (files_info, locations, isRoot) = _dir_listing(req_path)
    return render_template('files.html', files_info=files_info, locations=locations, isRoot=isRoot)

# -----------------------------------------------------------------------------
@app.route('/packages/add')
def packages_add():
    return render_template('venv_mng.html')

@app.route('/packages', methods=["GET","POST"])
def packages():
    trace('packages')
    try:
        if(request.method == "POST"):
            print("POST")
            print(request.form)
            venvName = request.form['venvName']
            foldername = secure_filename(venvName)
            full_foldername = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
            os.mkdir(full_foldername)

            i = 0
            full_filename = os.path.join(full_foldername, 'requirements.txt')
            with open(full_filename, 'w') as file:
                while True:
                    if(('pkgName'+str(i)) in request.form):
                        pkg_name = ('pkgName'+str(i))
                        pkg_specifier = ('pkgSpecifier'+str(i))
                        pkg_version = ('pkgVersion'+str(i))
                        if(request.form[pkg_name] != "" and request.form[pkg_version] != ""):
                            requirement = "{}{}{}\n".format(
                                request.form[pkg_name],
                                request.form[pkg_specifier],
                                request.form[pkg_version],
                            )
                            #print("\n\n>",request.form[pkg_name], "<->",request.form[pkg_version], "<-[", str(i) ,"]\n\n")
                            file.write(requirement)
                    else:
                        break
                    i += 1
            p = sub.Popen(["pipenv", "install", "-r", full_filename], cwd=full_foldername)
            return redirect('/') #render_template('running.html', tasks=tasks)
        elif(request.method == "GET"):
            print("GET")
            BASE_DIR = app.config['UPLOAD_FOLDER']
            folders = os.listdir(BASE_DIR)
            venvs = [{
                'name' : folder,
                'pkgs' : get_packages(os.path.join(BASE_DIR, folder)),
                'associated_archives' : list(
                    filter(
                        lambda resource : os.path.isdir(os.path.join(BASE_DIR, folder, resource)) ,
                        os.listdir(os.path.join(BASE_DIR, folder))
                    ))
                } for folder in folders]
            print("ARCHIVES", venvs)
            return render_template('venvs.html', venvs=venvs)#jsonify(venvs)

        return abort(404)
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(500)

def get_packages(foldername):
    pkgs = []
    try:
        print("TRYING ACCESS", foldername)
        pipfile = os.path.join(foldername, 'Pipfile.lock')
        pkgs_data = {}
        with open(pipfile) as json_file:
            pkgs_data = json.load(json_file)

        pkg_list = list(pkgs_data['default'].keys())

        print(divisor)
        print("foldername", foldername, "pkgs_data", pkgs_data, "pkg_list", pkg_list)
        print(divisor)

        if(len(pkg_list) > 0):
            pkgs = [{'name' : pkg, 'version' : pkgs_data['default'][pkg]['version']} for pkg in pkg_list]
    except Exception as e:
        flash(e)
        print("INTERNAL ERROR", e)
        return abort(404)
    return pkgs

@app.route('/packages/venv')
def packages_venv():
    pkgs = get_packages('test')
    
    return jsonify(pkgs)

# @deprecated - but could be usefull
@app.route('/packages/system')
def packages_system():
    sub.Popen(["pip", "freeze"], stdout=sub.PIPE, shell=True)
    (out, err) = proc.communicate()
    pkgs = out.decode("utf-8").split('\n')
    pkgs = [p.strip() for p in pkgs]
    return jsonify(pkgs)

# @deprecated - but could be usefull
@app.route('/packages/script')
def packages_script():
    from modulefinder import ModuleFinder
    scr = 'uploads\clientes\clientes_etl.py' # should be a parameter
    finder = ModuleFinder()
    finder.run_script(scr)
    m = finder.modules.items()
    pkgs = {}
    for k, v in m:
        pkgs[k] = ','.join(list(v.globalnames.keys())[:3])
    return jsonify(pkgs)

# @deprecated - but could be usefull
@app.route('/packages/dis')
def packages_dis():
    import dis
    from pprint import pprint
    from collections import defaultdict
    scr = 'uploads\clientes\clientes_etl.py' # should be a parameter
    lines = ""
    with open(scr) as file:
        lines = file.readlines()

    file_content = ''.join(lines)
    #print(file_content)

    instructions = dis.get_instructions(file_content)
    imports = [__ for __ in instructions if 'IMPORT' in __.opname]

    grouped = defaultdict(list)
    for instr in imports:
        grouped[instr.opname].append(instr.argval)

    pprint(grouped)
    return jsonify(grouped)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')