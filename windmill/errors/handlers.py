








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
import os
import subprocess as sub
from datetime import datetime

from windmill.main.utils import trace, divisor, __resolve_path, MsgTypes
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

errors = Blueprint('errors', __name__)

# === HELPERS functions =======================================================
@errors.route('/apl-wm-crm/test_err')
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

# === Application routes ======================================================
@errors.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@errors.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
