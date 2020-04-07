








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
import json
from werkzeug.utils import secure_filename

from windmill.main.utils import trace, divisor
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

venvironments = Blueprint('venvironments', __name__)

def _get_packages(foldername):
    """
        Function that given a :foldername: representing the venv folder returns
        all packages installed (by getting access to the Pipfile.lock file that
        contains this information organized in json)
    """
    pkgs = []
    try:
        print("venvs", "TRYING ACCESS", foldername)
        pipfile = os.path.join(foldername, 'Pipfile.lock')
        pkgs_data = {}
        with open(pipfile) as json_file:
            pkgs_data = json.load(json_file)

        pkg_list = list(pkgs_data['default'].keys())

        print("venvs", divisor)
        print("venvs", "foldername", foldername, "pkgs_data", pkgs_data, "pkg_list", pkg_list)
        print("venvs", divisor)

        if(len(pkg_list) > 0):
            pkgs = [{'name' : pkg, 'version' : pkgs_data['default'][pkg]['version']} for pkg in pkg_list]
    except Exception as e:
        flash(e)
        print("venvs", "INTERNAL ERROR", e)
        return abort(404)
    return pkgs


# === Application routes ======================================================
@venvironments.route('/packages/add')
def packages_add():
    """
        Route to the view that renders the page to input a new virtual environment
    """
    return render_template('venv_mng.html')

@venvironments.route('/packages', methods=["GET","POST"])
def packages():
    """
        Route to handles with:
        :GET: renders the page with all virtual environments
        :POST: create a new virtual environment (create a new folder that will
        represent a venv and install all python-packages to that venv).
    """
    trace('packages')
    try:
        if(request.method == "POST"):
            print("venvs", "POST")
            print("venvs", request.form)
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
            print("venvs", "GET")
            BASE_DIR = app.config['UPLOAD_FOLDER']
            folders = os.listdir(BASE_DIR)
            venvs = [{
                'name' : folder,
                'pkgs' : _get_packages(os.path.join(BASE_DIR, folder)),
                'associated_archives' : list(
                    filter(
                        lambda resource : os.path.isdir(os.path.join(BASE_DIR, folder, resource)) ,
                        os.listdir(os.path.join(BASE_DIR, folder))
                    ))
                } for folder in folders]
            print("venvs", "ARCHIVES", venvs)
            return render_template('venvs.html', venvs=venvs)#jsonify(venvs)

        return abort(404)
    except Exception as e:
        flash(e)
        print("venvs", "INTERNAL ERROR", e)
        return abort(500)


# -----------------------------------------------------------------------------
# @deprecated - test
@venvironments.route('/packages/venv')
def packages_venv():
    pkgs = _get_packages('test')
    
    return jsonify(pkgs)

# @deprecated - but could be usefull
@venvironments.route('/packages/system')
def packages_system():
    sub.Popen(["pip", "freeze"], stdout=sub.PIPE, shell=True)
    (out, err) = proc.communicate()
    pkgs = out.decode("utf-8").split('\n')
    pkgs = [p.strip() for p in pkgs]
    return jsonify(pkgs)

# @deprecated - but could be usefull
@venvironments.route('/packages/script')
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
@venvironments.route('/packages/dis')
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