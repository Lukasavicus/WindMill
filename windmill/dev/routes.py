




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

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++