








# === imports =================================================================
from flask import current_app as app
from flask import Blueprint, flash, render_template, redirect, abort, jsonify, request, url_for
from flask import send_file
import os
from werkzeug.utils import secure_filename
from zipfile import ZipFile
import shutil

from windmill.main.utils import trace, divisor, __resolve_path, uri_sep, MsgTypes
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


archives = Blueprint('archives', __name__)


# -----------------------------------------------------------------------------
#def allowed_file(filename):
#    return '.' in filename and \
#           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# -----------------------------------------------------------------------------


# === HELPERS =================================================================
def _get_req_absolute_path(requested_path):
    """
        Given a :requested_path: return the complete path for that resource.
        e.g.: venv_a/etl_archive_a/subdir_1/etl_script.py => 
        windmill/uploads/venv_a/etl_archive_a/subdir_1/etl_script.py
    """
    trace('_get_req_absolute_path')
    BASE_DIR = app.config['UPLOAD_FOLDER'] #"./{}/".format(app.config['UPLOAD_FOLDER'])
    return os.path.join(BASE_DIR, requested_path)

def _get_resource_tree(req_path):
    """
        Given a :requested_path: split this path into array that represents the
        tree to that resource in server's uploaded-resources-folder (uploads).
        e.g.: venv_a/etl_archive_a/subdir_1/etl_script.py =>
        [venv_a, etl_archive_a, subdir_1, etl_script.py]
    """
    #path_parts = abs_path.split('/')[2:]
    #path_parts = abs_path.split('/')[1:]
    #return req_path.split('/')
    return req_path.split(os.path.sep)

def _dir_listing(req_path=''):
    """
        Function that given a :requested_path returns the triplet:
        files_info: ?
        locations: ?
        isRoot: flag to determine if a archive folder is either a root or not
    """
    trace('_dir_listing')
    abs_path = _get_req_absolute_path(req_path)
    #print("archives", divisor)
    #print("archives", "name", __name__, "archives.root_path", archives.root_path, "req_path", req_path, "abs_path", abs_path)
    # Return 404 if path doesn't exist
    if(not os.path.exists(abs_path)):
        flash({'title' : "ERROR", 'msg' : 'Path not found', 'type' : MsgTypes['ERROR']})
        return abort(404)

    # Show directory contents
    files = os.listdir(abs_path)
    files_info = []
    for i, file_ in enumerate(files):
        path = os.path.join(req_path, file_)
        full_path = os.path.join(abs_path, file_)
        files_info.append({'path' : path, 'name' : file_, 'file_folder_flag' : os.path.isdir(full_path)})
        #print(file_, " X ", files[i])

    locations = [{'name' : os.path.sep, 'path' : os.path.join(os.path.sep, 'fs')}]
    #locations = [{'name' : os.path.sep, 'path' : '/fs'}]
    resource_tree = _get_resource_tree(req_path)

    #print("archives", "resource_tree", resource_tree, " or ", req_path.split('/'), "  -- >", os.path.sep)
    for i, resource_tree_element in enumerate(resource_tree):
        #print("archives", "resource_tree_element", resource_tree_element)
        locations.append({
                'name' : resource_tree_element,
                'path' : (uri_sep + 'fs' + uri_sep + uri_sep.join(resource_tree[:i+1]))
            })

    isRoot = len(resource_tree) == 1 and resource_tree[0] != ''
    folderEnv = len(resource_tree) == 1 and resource_tree[0] == ''

    return (files_info, locations, isRoot, folderEnv)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


# === Application routes ======================================================
@archives.route('/upload', methods=['GET', 'POST'])
def upload_file():
    """
        Route to handles with:
        :GET: renders the page with all resources (folders (venvs), project
        folders and files)
        :POST: create a new resource (file or unzipped project folder) by putting
        it in the venv folder selected
    """
    if(request.method == 'POST'):
        # check if the post request has the file part
        if('file' not in request.files):
            flash({'title' : "Tasks", 'msg' : "No file part", 'type' : MsgTypes['ERROR']})
            print("archives", 'No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also submit an empty part without filename
        if(file.filename == ''):
            flash({'title' : "Tasks", 'msg' : "No selected file", 'type' : MsgTypes['ERROR']})
            print("archives", 'No selected file')
            return redirect(request.url)
        if(file):# and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(full_filename)
            
            #print("archives", 'extracting', full_filename)
            
            #foldername = filename.split('.')[0]
            foldername = os.path.join(request.form['venvName'], filename.split('.')[0])
            full_foldername = os.path.join(app.config['UPLOAD_FOLDER'], foldername)

            os.mkdir(full_foldername)
            
            with ZipFile(full_filename, 'r') as zipObj:
                # Extract all the contents of zip file in current directory
                zipObj.extractall(full_foldername)
            #print("archives", 'Finished')
            os.remove(full_filename)

            flash({'title' : "Archive", 'msg' : f"Archive {full_filename} created successfully.", 'type' : MsgTypes['SUCCESS']})
            (files_info, locations, isRoot, folderEnv) = _dir_listing('')
            return render_template('archives_view.html', files_info=files_info, locations=locations, isRoot=isRoot, folderEnv=folderEnv)
    elif(request.method == 'GET'):
        (files_info, locations, isRoot, folderEnv) = _dir_listing('')
        return render_template('archives_view.html', files_info=files_info, locations=locations, isRoot=isRoot, folderEnv=folderEnv)
    flash({'title' : "Tasks", 'msg' : "/upload does not accept this HTTP verb", 'type' : MsgTypes['ERROR']})
    return abort(405)
# -----------------------------------------------------------------------------
@archives.route('/fs', defaults={'req_path': ''})
@archives.route('/fs/<path:req_path>')
def dir_listing(req_path):
    req_path = __resolve_path(req_path)
    #print("archives", divisor)
    #trace('dir_listing')
    abs_path = _get_req_absolute_path(req_path)
    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        return send_file(abs_path)
    (files_info, locations, isRoot, folderEnv) = _dir_listing(req_path)
    return render_template('archives_view.html', files_info=files_info, locations=locations, isRoot=isRoot, folderEnv=folderEnv)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++



# === API routes ==============================================================
@archives.route('/api/fs', defaults={'req_path': ''})
@archives.route('/api/fs/<path:req_path>', methods=['GET', 'DELETE'])
def dir_listing_api(req_path):
    req_path = __resolve_path(req_path)
    #trace('dir_listing_api')
    try:
        abs_path = _get_req_absolute_path(req_path)
        (files_info, locations, isRoot, folderEnv) = _dir_listing(req_path)
        if(request.method == "DELETE"):
            # PATH SEP SYSTEM DEPENDANCY
            #req_path.count('/')
            assert req_path.count(os.path.sep) == 0, "Selected path '{}' is not a root directory. Delete are allowed only in roots directories".format(req_path)
            shutil.rmtree(abs_path)
            abs_path = app.config['UPLOAD_FOLDER']
            flash({'title' : "Archive", 'msg' : "Archive {} deleted.".format(req_path), 'type' : MsgTypes['SUCCESS']})
        # elif(request.method == "DELETE"):
        return jsonify ({'files_info' : files_info, 'locations' : locations})
    except Exception as e:
        flash({'title' : "ERROR", 'msg' : e, 'type' : MsgTypes['ERROR']})
        print("archives", "INTERNAL ERROR", e)
        return abort(500)
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++