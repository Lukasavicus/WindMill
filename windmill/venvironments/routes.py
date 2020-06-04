








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
import json
from werkzeug.utils import secure_filename

from windmill.main.utils import trace, divisor, MsgTypes

from windmill.models import VEnvironment, VEnvironmentDAO, Package
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

venvironments = Blueprint('venvironments', __name__)
context = "apl-wm-crm"

import threading
import subprocess

def popen_and_call(on_exit, cmd, cwd, venv_name):
    """
        Runs the given args in a subprocess.Popen, and then calls the function
        on_exit when the subprocess completes.
        on_exit is a callable object, and popen_args is a list/tuple of args that 
        would give to subprocess.Popen.
    """
    def run_in_thread(on_exit, cmd, cwd, venv_name): #, venv_name
        print("I WILL WAIT - cmd - "+cwd+"")
        proc = sub.Popen(cmd, cwd=cwd)
        proc.wait()
        print("WAIT IS OVER")
        on_exit(cwd, venv_name) #, venv_name
    thread = threading.Thread(target=run_in_thread, args=(on_exit, cmd, cwd, venv_name)) # , venv_name
    thread.start()
    # returns immediately after the thread starts
    return thread

def _add_packages_installed(folder, venv_name):
    print("_add_packages_installed")
    print("="*100, "\n\nupdating...\n\n", "="*100)
    pkgs = _get_packages(folder)
    venv = VEnvironment(venv_name, packages=pkgs)
    print("VEnv is now with all packages", venv)
    return VEnvironmentDAO.insert(venv)

def _get_packages(foldername):
    """
        Function that given a :foldername: representing the venv folder returns
        all packages installed (by getting access to the Pipfile.lock file that
        contains this information organized in json)
    """
    print("_get_packages")
    pkgs = []
    try:
        #print("venvs", "TRYING ACCESS", foldername)
        pipfile = os.path.join(foldername, 'Pipfile.lock')
        pkgs_data = {}
        with open(pipfile) as json_file:
            pkgs_data = json.load(json_file)

        pkg_list = list(pkgs_data['default'].keys())

        #print("venvs", divisor)
        #print("venvs", "foldername", foldername, "pkgs_data", pkgs_data, "pkg_list", pkg_list)
        #print("venvs", divisor)

        if(len(pkg_list) > 0):
            pkgs = [{
                    'name' : pkg,
                    'version_specifier' : pkgs_data['default'][pkg]['version'][:2],
                    'version' : pkgs_data['default'][pkg]['version'][2:] } for pkg in pkg_list]
    except Exception as e:
        #flash({'title' : "Virtual Env", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("venvs", "INTERNAL ERROR", e)
        return []#abort(404)
    return pkgs

def _get_venvs():
    """
        Function that based on a directory :BASE_DIR: recover all virtual
        environments
    """
    print("_get_venvs()")
    BASE_DIR = app.config['UPLOAD_FOLDER']
    folders = os.listdir(BASE_DIR)
    venvs = VEnvironmentDAO.recover()

    # venvs = [{
    #     'id' : venvs[0]._id,
    #     'name' : folder,
    #     'pkgs' : _get_packages(os.path.join(BASE_DIR, folder)),
    #     'associated_archives' : list(
    #         filter(
    #             lambda resource : os.path.isdir(os.path.join(BASE_DIR, folder, resource)),
    #             os.listdir(os.path.join(BASE_DIR, folder))
    #         ))
    #     } for folder in folders]

    # associated = list(map(lambda venv: {'associated_archives' : list(
    #         filter(
    #             lambda resource : os.path.isdir(os.path.join(BASE_DIR, venv.name, resource)),
    #             os.listdir(os.path.join(BASE_DIR, venv.name))
    #         ))}, venvs))
    # print(associated)
    print([(venv.name, len(venv.packages)) for venv in venvs])
    return venvs

def _new_virtual_environment(req_form):
    """
        Function that make a new virtual environment object based on data sent
        in the request form.
    """
    venv = VEnvironment(req_form['venvName'])
    i = 0
    while True:
        if(('pkgName'+str(i)) in req_form):
            pkg_name = ('pkgName'+str(i))
            pkg_specifier = ('pkgSpecifier'+str(i))
            pkg_version = ('pkgVersion'+str(i))
            if(req_form[pkg_name] != ""):
                venv.add_package(Package(
                    req_form[pkg_name],
                    req_form[pkg_specifier],
                    req_form[pkg_version],
                ))
        else:
            break
        i += 1
    return venv

def _make_requirements(foldername, virtual_env_obj):
    """
        Function that build the 'requirements.txt' file used to create a
        virtual environment by the PIPENV, based on :virtual_env_obj: object.
    """
    requirements_filename = os.path.join(foldername, 'requirements.txt')
    with open(requirements_filename, 'w') as requirement_file:
        for pkg in virtual_env_obj.packages:
            requirement = "{}{}{}\n".format(
                pkg.name, pkg.version_specifier, pkg.version,
            )
            #print("\n\n>",pkg.name], "<->",pkg.version], "<-[", str(i) ,"]\n\n")
            requirement_file.write(requirement)
    return requirements_filename
    

# === Application routes ======================================================
@venvironments.route('/'+context+'/environments/add')
def environments_add():
    """
        Route to the view that renders the page to input a new virtual
        environment
    """
    return render_template('venv_mng.html')

@venvironments.route('/'+context+'/environments', methods=["GET","POST"])
def environments():
    """
        Route to handles with:
        :GET: renders the page with all virtual environments
        :POST: create a new virtual environment (create a new folder that will
        represent a venv and install all python-packages to that venv).
    """
    #trace('packages')
    try:
        if(request.method == "POST"):
            print("venvs", "POST")
            venvName = request.form['venvName']
            foldername = secure_filename(venvName)
            full_foldername = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
            os.mkdir(full_foldername)
            print("So far so good - 1")
            venv = _new_virtual_environment(request.form)
            print("So far so good - 2")
            requirements_filename = _make_requirements(full_foldername, venv)
            print("So far so good - 3")
            #p = sub.Popen(["pipenv", "install", "-r", requirements_filename], cwd=full_foldername)

            #val = popen_and_call(_add_packages_installed, ["pipenv", "install", "-r", requirements_filename], full_foldername, venv.name)
            popen_and_call(_add_packages_installed, ["pipenv", "install", "-r", requirements_filename], full_foldername, venvName)

            flash({'title' : "Virtual Env", 'msg' : "Virtual Env {} will be created asynchronously successfully".format(full_foldername), 'type' : MsgTypes['SUCCESS']})
            
            return redirect(url_for('tasks.home')) #redirect('/') #render_template('running.html', tasks=tasks)

        elif(request.method == "GET"):
            print("venvs", "GET")
            venvs = _get_venvs()
            assert venvs != None, "Could not query 'venvs' collection. This happened because either the collection don't exist or the database refused connection"
            return render_template('venvs.html', venvs=venvs)

        flash({'title' : "Virtual Env", 'msg' : "/packages  does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
        return abort(404)
    except Exception as e:
        flash({'title' : "Virtual Env", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("venvs", "INTERNAL ERROR", e)
        return abort(500)

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@venvironments.route('/'+context+'/api/environment/<venv_id>', methods=["DELETE", "GET", "PUT"])
def api_venv(venv_id):
    try:
        print("venvs", "VENV -> ", request.method, " --> ", venv_id)
        venv = VEnvironmentDAO.recover_by_id(venv_id)
        print("\n\n", venv, "\n\n")
        if(venv != None):
            if(request.method == "DELETE"):
                print("VENV DELETE: "+venv_id+"")
                #VenvDAO.delete(venv)
                return app.config['SUCCESS']

            elif(request.method == "PUT"):
                # _new_virtual_environment()
                flash({'title' : "Venv Action", 'msg' : "Venv '"+venv.name+"' was updated", 'type' : MsgTypes['SUCCESS']})
                return app.config['SUCCESS']

            if(request.method in ["GET", "PUT"]): # "DELETE"
                return jsonify(venv.jsonify())

        else:
            flash({'title' : "Venv Action", 'msg' : "Venv id:"+venv_id+" could not be found", 'type' : MsgTypes['ERROR']})
            return abort(404)
        flash({'title' : "Venvs", 'msg' : "/api/venv does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
        return abort(405)
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("tasks", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++