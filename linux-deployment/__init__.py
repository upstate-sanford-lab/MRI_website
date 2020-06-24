from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pydicom as dicom
import numpy as np
import os
import PIL.Image
from functools import wraps
import natsort
import subprocess
from predict import Predict
from fastai.vision import *

def gather_files(path, type, wholeDIR):
    '''Return a list of directories containing files of a
     certain type. For example: .jpg, .dcm, or others
     if the type is .dcm, the directory name is returned
     otherwise, the file name is returned'''
    List = []  # create an empty list
    for dirName, subdirList, fileList in os.walk(path):
        for filename in fileList:
            if type in filename.lower():  # check whether the file's DICOM
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
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def SaveSeries(file, filename, series):
    '''This function saves a "file" under a specific "filename" in one of three folders specified by "series" (adc, highb, t2)'''
    if series in ["adc", "highb", "t2"]:
        file.save(os.path.join(app.config[series + '_uploads'], filename))
    else:
        return False
    return True


def clearFiles(dir):
    deletedFiles = []
    for dirName, subdirList, fileList in os.walk(dir):
        for filename in fileList:
            if ".dcm" or ".jpg" in filename.lower():  # check whether the file's DICOM of JPG
                os.remove(os.path.join(dirName, filename))
                deletedFiles.append(filename)
    print("the following files were deleted")
    print(deletedFiles)


def cleanup(images, append, isolateFile):
    '''This function is used to edit file names so that they can be called
    directly by javascript, or so that the file name can be isolated completely
    from a long directory. I am sure there is a better way to do this but so far this has been working for me. '''
    count = 0
    for image in images:
        if isolateFile == True:
            images[count] = os.path.split(image)[1]
        elif 'protected' in images[count]:
            images[count] = append + image.split('protected')[1]
        else:
            print("unable locate 'protected' in file path")
        count = count + 1
    return [images, count]


def checkLogin(name, password):
    users = {"Tom": "prostate", "Andrew": "webdev"}
    if name in users:
        if users[name] == password:
            return True
    return False


basePath = os.getcwd()
app = Flask(__name__, instance_path=os.path.join(basePath, 'protected'))
app.config['SECRET_KEY'] = "supersecretkey34237439273874298"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'dcm'}


for dir in ["uploads", "JPG_converts", "Aligned_DICOM", "jpg_tumor"]:
    path = os.path.join(basePath, "protected", dir)
    app.config[dir] = path
    if not os.path.exists(path):
        os.mkdir(path)
        print("made directory: " + path)
    for series in ["t2", "adc", "highb"]:
        path = os.path.join(basePath, "protected", dir, series)
        app.config[series + "_" + dir] = path
        if not os.path.exists(path):
            os.mkdir(path)
            print("made directory: " + path)


def personal_files(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if session["user"] == "Andrew":
            return f(*args, **kwargs)
        else:
            print("user not Andrew, redirected to index")
            return redirect(url_for('index'))

    return wrap


def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if all(key in session for key in ('loggedIn', 'user')):
            if session["loggedIn"] == True:
                return f(*args, **kwargs)
        else:
            print("need to login first")
            return redirect(url_for('login'))

    return wrap


@app.route('/', methods=["GET", "POST"])
@app.route('/Homepage', methods=["GET", "POST"])
@login_required
def index():
    uploaded = 0
    if request.method == 'POST':
        for folder in ["Aligned_DICOM", "JPG_converts", "uploads", "jpg_tumor"]:
            clearFiles(app.config[folder])
        for filetype in ["adc", "highb", "t2"]:
            for file in request.files.getlist(filetype):
                successfulSave = False
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    successfulSave = SaveSeries(file, filename, filetype)
                elif not allowed_file(file.filename):
                    print(file.filename)
                    print("Not allowed file type")
                else:
                    print(file.filename)
                    print("No file part")
                if successfulSave == True:
                    uploaded = uploaded + 1
        if uploaded > 0:
            imagelist = [];
            for series in ["adc", "highb", "t2"]:
                subprocess.call(["python", "anonymize.py", app.config[series + "_uploads"]])
            subprocess.call(["python", "Alignment.py", app.config["t2_uploads"], app.config["adc_uploads"],
                             app.config["highb_uploads"], app.config["Aligned_DICOM"]])
            for series in ["adc", "highb", "t2"]:
                imagelist.append(
                    makeJPGs(app.config[series + "_Aligned_DICOM"], app.config[series + "_JPG_converts"], series))
            print("the following images have been anonymized, aligned, and saved as JPGs")
            print(imagelist)
        else:
            print("no files were uploaded")
    user = session["user"]
    return render_template("PIRADS_webAI.html", username=user)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        print("attempt for login")
        username = request.form["username"]
        password = request.form["password"]
        if checkLogin(username, password):
            session["user"] = request.form["username"]
            session["loggedIn"] = True
            print("logged in")
            return redirect(url_for("index"))
    if all(key in session for key in ('loggedIn', 'user')):
        if session["loggedIn"] == True:
            print("already logged in")
            return redirect(url_for("index"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    for folder in ["Aligned_DICOM", "JPG_converts", "uploads", "jpg_tumor"]:
        clearFiles(app.config[folder])
    session.pop("user")
    session.pop("loggedIn")
    return redirect(url_for("login"))


@app.route('/api/images')
@login_required
def api_get_images():
    '''Sends list of uploaded files to webpage'''
    adc = cleanup(gather_files(app.config["adc_JPG_converts"], ".jpg", False), 'protected', False)[0]
    highb = cleanup(gather_files(app.config["highb_JPG_converts"], ".jpg", False), 'protected', False)[0]
    t2 = cleanup(gather_files(app.config["t2_JPG_converts"], ".jpg", False), 'protected', False)[0]
    return jsonify(adc=natsort.natsorted(adc), highb=natsort.natsorted(highb), t2=natsort.natsorted(t2))


@app.route('/api/receiveMarkup', methods=['POST'])
@login_required
def api_receiveMarkup():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        print(data)
        markup = {}
        #markup = {'primarySlice': int(data['primarySlice'])}
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
        c = Predict()
        c.path = basePath
        c.dict = markup
        c.learn = load_learner(os.path.join(basePath, 'static', 'model'))
        score = c.calculate_PIRADS()
        return ("Overall PIRADS Score is {}ish".format(score))
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

if __name__ == "__main__":
    app.run(debug=True)