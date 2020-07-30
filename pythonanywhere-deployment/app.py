from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash
from werkzeug.utils import secure_filename
import pydicom as dicom
import numpy as np
import os
import PIL.Image
from functools import wraps
import natsort
import subprocess
from MRI_sorting import ParseMRI
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import logging
import json
from zipfile import ZipFile
import shutil
from lesionID import lesionsID

def gather_files(path, type, wholeDIR):
    '''Return a list of directories containing files of a
     certain type. For example: .jpg, .dcm, or others
     if the type is .dcm, the directory name is returned
     otherwise, the file name is returned'''
    List = []  # create an empty list
    for dirName, subdirList, fileList in os.walk(path):
        for filename in fileList:
            if type in filename.lower():  # check whether the file is of designated type
                if wholeDIR == True:
                    List.append(dirName)
                else:
                    List.append(os.path.join(dirName, filename))
    return List


def makeJPGs(DCM_location, JPG_location, series):
    '''Takes a folder DCM_location, converts dcm into jpg, and saves files in JPG_location'''
    saved_file_list = []
    for s in os.listdir(DCM_location):
        'Loop through the directory to create an ordered list of dicome files'
        try:
            if ".dcm" in s.lower():  # check whether the file is DICOM
                ds = dicom.dcmread(os.path.join(DCM_location, s))
                ps = ds.pixel_array.astype(float)
                # if series == "highb":
                pixels = ((ps - ps.min()) / (ps.max() - ps.min())) * 255.0
                # elif series == "t2" or series == "adc":
                #     if ps.max() == 0:
                #         pixels = (np.maximum(ps, 0)) * 255.0
                #     else:
                #         pixels = (np.maximum(ps, 0) / ps.max()) * 255.0
                pixels = np.uint8(pixels)
                im = PIL.Image.fromarray(pixels)
                im = im.convert("L")

                s = s.replace('.dcm', '.jpg')
                if hasattr(ds, "SliceLocation"):
                    s = str(round(ds.SliceLocation, 2)) + ", " + s
                else:
                    '''Slice was either aligned already or it was a scout view'''

                im.save(os.path.join(JPG_location, s))
                saved_file_list.append(os.path.join("static", "JPG_converts", s))
        except:
            print("Could not convert: " + s)
    return saved_file_list


def allowed_file(filename):
    '''This function isolates the file extension and checks to see if it is an Allowed extension.
    This helps prevent users from uploading malicious files to the server'''
    return '.' in filename and \
           filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS and \
           len(filename.split(".")) == 2


def SaveSeries(file, filename, series):
    '''This function saves a "file" under a specific "filename" in one of three folders specified by "series" (adc, highb, t2)'''
    if series in ["adc", "highb", "t2"]:
        file.save(os.path.join(session["fileConfig"][series + '_uploads'], filename))
    else:
        return False
    return True


def clearFiles(dir):
    deletedFiles = []
    count = 0
    for dirName, subdirList, fileList in os.walk(dir):
        for filename in fileList:
            if ".dcm" or ".jpg" in filename.lower():  # check whether the file's DICOM of JPG
                os.remove(os.path.join(dirName, filename))
                count = count+1
                deletedFiles.append(filename)
    return count


def cleanup(imagePaths, append, isolateFile):
    '''This function is used to edit file names so that they can be called
    directly by javascript, or so that the file name can be isolated completely
    from a long directory. I am sure there is a better way to do this but so far this has been working for me. '''
    count = 0
    for imagePath in imagePaths:
        if isolateFile == True:
            imagePaths[count] = os.path.split(imagePath)[1]
        elif 'protected' in imagePath:
            imagePaths[count] = append + imagePath.split('protected')[1]
        else:
            print("unable locate 'protected' in file path")
        count = count + 1
    return [imagePaths, count]


def configureUserFiles():
    userPath = os.path.join(basePath, "protected", session["user"])
    flash("Configuring user directories","info")
    if not os.path.exists(userPath):
        os.mkdir(userPath)
        print("made directory: " + userPath)
    for dir in ["uploads", "JPG_converts", "Aligned_DICOM"]:
        dirPath = os.path.join(userPath, dir)
        session["fileConfig"][dir] = dirPath
        if not os.path.exists(dirPath):
            os.mkdir(dirPath)
            print("made directory: " + dirPath)
        for series in ["t2", "adc", "highb"]:
            seriesPath = os.path.join(userPath, dir, series)
            session["fileConfig"][series + "_" + dir] = seriesPath
            if not os.path.exists(seriesPath):
                os.mkdir(seriesPath)
                print("made directory: " + seriesPath)

    session["fileConfig"]["jpg_tumor"] = os.path.join(userPath,"jpg_tumor")
    if not os.path.exists(session["fileConfig"]["jpg_tumor"]):
        os.mkdir(session["fileConfig"]["jpg_tumor"])

    session["fileConfig"]["sortingDir"] = os.path.join(userPath,"sortingDir")
    if not os.path.exists(session["fileConfig"]["sortingDir"]):
        os.mkdir(session["fileConfig"]["sortingDir"])

    session["fileConfig"]["lesionID"] = os.path.join(userPath,"lesionID")
    if not os.path.exists(session["fileConfig"]["lesionID"]):
        os.mkdir(session["fileConfig"]["lesionID"])

    session["fileConfig"]["lesionID_save"] = os.path.join(userPath,"lesionID","save")
    if not os.path.exists(session["fileConfig"]["lesionID_save"]):
        os.mkdir(session["fileConfig"]["lesionID_save"])

    session["fileConfig"]["lesionID_save_voi"] = os.path.join(userPath,"lesionID","save","voi")
    if not os.path.exists(session["fileConfig"]["lesionID_save_voi"]):
        os.mkdir(session["fileConfig"]["lesionID_save_voi"])

def get_all_file_paths(directory):
    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for dirName, subdirList, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(dirName, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths

def create_zip():
    directory = os.path.join(basePath, "protected", session["user"], "Aligned_DICOM")
    file_paths = get_all_file_paths(directory)
    print(file_paths)
    zip_path = os.path.join(basePath, "protected", session["user"],'files.zip')

    if os.path.exists(zip_path):
        os.remove(zip_path)

    with ZipFile(zip_path,'w') as zip:
        # writing each file one by one
        for file in file_paths:
            normPath = os.path.normpath(file)
            print(normPath)
            split_file = normPath.split(os.sep)
            print(split_file)
            arcFile = os.path.join(split_file[len(split_file)-3],split_file[len(split_file)-2],split_file[len(split_file)-1])
            zip.write(file, arcFile)

basePath = os.path.dirname(os.path.abspath(__file__))
venvPath = "/home/sanfordlab/.virtualenvs/flaskk/bin/python"


app = Flask(__name__, instance_path=os.path.join(basePath, 'protected'))
app.config['SECRET_KEY'] = "supersecretkey34237439273874298"
app.permanent_session_lifetime = timedelta(minutes = 30)

# SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
#     username="AndrewGoldmann",
#     password="flaskPass",
#     hostname="AndrewGoldmann$webApp",
#     databasename="AndrewGoldmann.mysql.pythonanywhere-services.com"
# )
# app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
# app.config["SQLALCHEMY_POOL_RECYCLE"] = 299
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ALLOWED_EXTENSIONS = {'dcm'}

class users(db.Model):
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password


def personal_files(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if all(arg.split("/")[0] == session["user"] for arg in kwargs.values()):
            return f(*args, **kwargs)
        else:
            flash("These are not your files",'error')
            return redirect(url_for('index'))
    return wrap


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if all(key in session for key in ('loggedIn', 'user')):
            if session["loggedIn"] == True:
                return f(*args, **kwargs)
        else:
            flash("You need to login first", 'error')
            return redirect(url_for('login'))
    return wrap

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get("user") == "Andrew" and session.get("loggedIn") == True:
            return f(*args, **kwargs)
        else:
            flash("Need to be logged in as admin to view this page", 'error')
            return redirect(url_for('index'))
    return wrap

@app.route('/', methods=["GET", "POST"])
@app.route('/Homepage', methods=["GET", "POST"])
@login_required
def index():
    uploaded = 0
    if request.method == 'POST':
        for folder in ["Aligned_DICOM", "JPG_converts", "uploads", "jpg_tumor"]:
            clearFiles(session["fileConfig"][folder])
        for filetype in ["adc", "highb", "t2"]:
            NoFilePart = False
            NotAllowedType = False
            for file in request.files.getlist(filetype):
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    successful = SaveSeries(file, filename, filetype)
                    if successful:
                        uploaded = uploaded + 1
                elif not allowed_file(file.filename):
                    print("not Allowed  " + file.filename)
                    NotAllowedType == True
                else:
                    NoFilePart == True
            if NoFilePart == True:
                flash("There was no file in the {series} series".format(series=filetype), "error")
            if NotAllowedType == True:
                flash("A file in {series} was not a dicom".format(series=filetype), "error")

        if uploaded > 0:
            imagelist = [];
            for series in ["adc", "highb", "t2"]:
                subprocess.call([venvPath, os.path.join(basePath,"anonymize.py"), session["fileConfig"][series + "_uploads"]])
            subprocess.call([venvPath, os.path.join(basePath,"Alignment.py"), session["fileConfig"]["t2_uploads"], session["fileConfig"]["adc_uploads"],
                             session["fileConfig"]["highb_uploads"], session["fileConfig"]["Aligned_DICOM"]])
            for series in ["adc", "highb", "t2"]:
                imagelist.append(
                    makeJPGs(session["fileConfig"][series + "_Aligned_DICOM"], session["fileConfig"][series + "_JPG_converts"], series))
            print("the following images have been anonymized, aligned, and saved as JPGs")
            print(imagelist)
            flash(str(uploaded) + " files successfully uploaded, anonymized and aligned", 'info')
            create_zip()
        else:
            flash("No files were uploaded", "error")
    user = session["user"]
    return render_template("PIRADS_webAI.html", username=user)


# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     '''When the webpage needs '''
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        print("attempt for login")
        username = request.form["username"]
        password = request.form["password"]
        if users.query.filter_by(username = username).first():
            if users.query.filter_by(username = username).first().password == password:
                session["user"] = request.form["username"]
                session["loggedIn"] = True
                session["fileConfig"] = {}
                session.permanent = True
                flash("Successfully logged in", 'info')
                configureUserFiles()
                return redirect(url_for("index"))
            else:
                flash("Password incorrect", 'error')
        else:
            flash("Username incorrect", 'error')
    elif all(key in session for key in ('loggedIn', 'user')):
        if session["loggedIn"] == True:
            flash("Already logged in", "info")
            return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    session.pop("user")
    session.pop("loggedIn")
    session.pop("fileConfig")
    flash("Successfully logged out", 'info')
    return redirect(url_for("login"))

@app.route("/register", methods = ["POST", "GET"])
def register():
    if request.method == "POST":
        print("registration attempted")
        username = request.form["username"]
        password = request.form["password"]
        password2 = request.form["password2"]
        if users.query.filter_by(username = username).first():
            flash("Username already taken", 'error')
            return render_template("register.html")
        elif not password == password2:
            flash("Passwords must match", 'error')
            return render_template("register.html")
        else:
            flash("Registration successful", "info")
            usr = users(username, password)
            db.session.add(usr)
            db.session.commit()
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route('/api/images')
@login_required
def api_get_images():
    '''Sends list of uploaded files to webpage'''
    adc = cleanup(gather_files(session["fileConfig"]["adc_JPG_converts"], ".jpg", False), 'protected', False)[0]
    highb = cleanup(gather_files(session["fileConfig"]["highb_JPG_converts"], ".jpg", False), 'protected', False)[0]
    t2 = cleanup(gather_files(session["fileConfig"]["t2_JPG_converts"], ".jpg", False), 'protected', False)[0]
    return jsonify(adc=natsort.natsorted(adc), highb=natsort.natsorted(highb), t2=natsort.natsorted(t2))


@app.route('/api/receiveMarkup', methods=['POST'])
@login_required
def api_receiveMarkup():
    flash("Segmentation received", "info")
    clearFiles(session["fileConfig"]["jpg_tumor"])
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        markup = {}
        # markup = {'primarySlice': int(data['primarySlice'])}
        if 'slices' in data:
            i = 0
            for slice in data['slices'].split(", "):
                if slice in markup.keys():
                    markup[slice]['x'].append(int(data['x'].split(", ")[i]))
                    markup[slice]['y'].append(int(data['y'].split(", ")[i]))
                else:
                    markup[slice] = {'x': [], 'y': []}
                    markup[slice]['x'].append(int(data['x'].split(", ")[i]))
                    markup[slice]['y'].append(int(data['y'].split(", ")[i]))
                i = i + 1
            print(markup)
            # try:
            markup_as_string = json.dumps(markup)
            capture = subprocess.run([venvPath, os.path.join(basePath,'middle_man.py'), basePath, markup_as_string, session["user"]], capture_output = True, text=True)
            print("capture is: ")
            print(capture.stdout)
            print(type(capture.stdout))
            if capture.returncode !=0:
                print(capture.stderr)
                return ("You caused a bug! This will be worked on at our end, please try again with slighly diferent segmentation")
            score = capture.stdout
            return (score)
        #     except:
        #         return ("This version of the website is unable to report a PIRADS score")
        else:
            return ("please segment the region of the prostate that requires analysis")
    else:
        return "Error: submitted GET request. POST request required"


@app.route('/protected/<path:filename>')
@login_required
@personal_files
def protected(filename):
    try:
        return send_from_directory(os.path.join(app.instance_path, ''), filename)
    except Exception as e:
        return redirect(url_for("index"))


@app.route("/deleteAccount")
@login_required
def deleteAccount():
    users.query.filter_by(username = session["user"]).delete()
    db.session.commit()
    for folder in ["Aligned_DICOM", "JPG_converts", "uploads", "jpg_tumor"]:
        clearFiles(session["fileConfig"][folder])
    if os.path.exists(os.path.join(basePath, "protected", session["user"],"files.zip")):
        os.remove(os.path.join(basePath, "protected", session["user"],"files.zip"))
    flash("Account deletion successful", 'info')
    return redirect(url_for("logout"))


@app.route("/deleteFiles")
@login_required
def deleteFiles():
    count = []
    for folder in ["Aligned_DICOM", "JPG_converts", "uploads", "jpg_tumor"]:
        count.append(clearFiles(session["fileConfig"][folder]))
    flash(str(count[0])+" dicom files deleted", "info")
    total = 0
    for num in count:
        total = total+num
    if os.path.exists(os.path.join(basePath, "protected", session["user"],"files.zip")):
        os.remove(os.path.join(basePath, "protected", session["user"],"files.zip"))
        total = total+1
    flash(str(total) + " total files deleted including accessory files", "info")
    return redirect(url_for("index"))

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500

@app.route("/view")
@admin_required
@login_required
def view():
    values=users.query.all()
    if values == None:
        values == "database empty"
    return render_template("view.html", values=values)

@app.route("/downloadFiles")
@login_required
def complete_download():
    zip_path = os.path.join(basePath, "protected", session["user"])
    filename = 'files.zip'
    if os.path.exists(os.path.join(zip_path, filename)):
        flash("Files sent to browser", "info")
        return send_from_directory(zip_path, filename, mimetype='application/zip', as_attachment=True, attachment_filename= filename)
    else:
        flash("Files not ready. Re-upload your dicoms files and try again", 'error')
        return redirect(url_for("index"))


@app.route("/identifyLesions")
@login_required
def identifyLesions():
    lesion = lesionsID()
    lesion.patient = session["user"]
    lesion.t2path = session["fileConfig"]["t2_Aligned_DICOM"]
    lesion.highbpath = session["fileConfig"]["highb_Aligned_DICOM"]
    lesion.adcpath = session["fileConfig"]["adc_Aligned_DICOM"]
    lesion.ann_path= session["fileConfig"]["lesionID_save_voi"]
    lesion.savepath = session["fileConfig"]["lesionID_save"]
    lesion.process()
    flash("identifying lesions","info")
    return redirect(url_for("index"))

@app.route("/sortDicoms",methods=["GET", "POST"])
@login_required
def sortDicoms():
    if request.method == "POST":
        clearFiles(session["fileConfig"]["sortingDir"])

        if not os.path.exists(os.path.join(session["fileConfig"]["sortingDir"], "unsorted")):
            os.mkdir(os.path.join(session["fileConfig"]["sortingDir"], "unsorted"))
        if not os.path.exists(os.path.join(session["fileConfig"]["sortingDir"], "sorted_dicoms")):
            os.mkdir(os.path.join(session["fileConfig"]["sortingDir"], "sorted_dicoms"))

        NoFilePart = False
        NotAllowedType = False

        for file in request.files.getlist('filesToSort'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(session["fileConfig"]["sortingDir"],"unsorted", filename))
            elif not allowed_file(file.filename):
                print("not Allowed  " + file.filename)
                NotAllowedType == True
            else:
                NoFilePart == True

        if NoFilePart == True:
            flash("There was no file in the upload", "error")
        if NotAllowedType == True:
            flash("A file in the series was not a DICOM", "error")

        sorter = ParseMRI()
        sorter.basePATH = os.path.join(session["fileConfig"]["sortingDir"])
        sorter.savePATH = os.path.join(sorter.basePATH, 'sorted_dicoms')
        sorter.sort_dm_all(dir = os.path.join(session["fileConfig"]["sortingDir"],'unsorted'))

        directory = sorter.savePATH
        file_paths = get_all_file_paths(directory)
        zip_path = session["fileConfig"]["sortingDir"]
        filename = 'files.zip'
        if os.path.exists(os.path.join(zip_path,filename)):
            os.remove(os.path.join(zip_path,filename))
        with ZipFile(os.path.join(zip_path,filename),'w') as zip:
            # writing each file one by one
            for file in file_paths:
                normPath = os.path.normpath(file)
                split_file = normPath.split(os.sep)
                arcFile = os.path.join(split_file[len(split_file)-3],split_file[len(split_file)-2],split_file[len(split_file)-1])
                zip.write(file, arcFile)

        flash("Files sent to browser", "info")
        try:
            return send_from_directory(zip_path, filename, mimetype='application/zip', as_attachment=True, attachment_filename= filename)
        finally:
            shutil.rmtree(os.path.join(session["fileConfig"]["sortingDir"],"unsorted"))
            shutil.rmtree(os.path.join(session["fileConfig"]["sortingDir"],"sorted_dicoms"))
            if os.path.exists(os.path.join(zip_path,filename)):
                os.remove(os.path.join(zip_path,filename))
    else:
        flash("Attempted download with 'GET' request", 'error')
        return redirect(url_for("index"))

@app.route("/adcbox")
@login_required
def testThisThing():
    if request.method == "POST":
        for file in request.files:
            print("file found")
            print(file.name)


if __name__ == "__main__":
    db.create_all()
    app.run()
