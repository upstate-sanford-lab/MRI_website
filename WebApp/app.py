
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import pydicom as dicom
import numpy as np
import os
import cv2
import natsort
import subprocess

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
                    List.append(os.path.join(dirName,filename))
    return List

def makeJPGs(DCM_location, JPG_location):
    '''Takes a folder DCM_location, converts dcm into jpg, and saves files in JPG_location'''
    saved_file_list = []
    for s in os.listdir(DCM_location):
        'Loop through the directory to create an ordered list of dicome files'
        try:
            if ".dcm" in s.lower():  # check whether the file is DICOM
                ds = dicom.dcmread(os.path.join(DCM_location, s))
                ps = ds.pixel_array.astype(float)
                pixels = (np.maximum(ps, 0) / ps.max()) * 255.0 #problem : divide by zero when ps.max() = 0
                pixels = np.uint8(pixels)
                s = s.replace('.dcm', '.jpg')

                if hasattr(ds, "SliceLocation"):
                    s = str(round(ds.SliceLocation, 2)) + ", " + s
                else:
                    'Slice was either aligned already or it was a scout view'

                cv2.imwrite(os.path.join(JPG_location, s), pixels)
                saved_file_list.append(os.path.join("static\JPG_converts", s))
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
    if series == "adc":
        file.save(os.path.join(app.config['adc_uploads'], filename))
    elif series == "highb":
        file.save(os.path.join(app.config['highb_uploads'], filename))
    elif series == "t2":
        file.save(os.path.join(app.config['t2_uploads'], filename))
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
        elif 'static' in images[count]:
            images[count] = append + image.split('static')[1]
        else:
            print("unable to locate 'static' in file path")
        count = count + 1
    return [images,count]

app = Flask(__name__)
'''Usage: update basepath with the location of the WebApp folder'''
basePath = r'C:\Users\MSStore'

for dir in ["uploads", "JPG_converts", "Aligned_DICOM", "jpg_tumor"]:
    app.config[dir] = os.path.join(basePath, "WebApp", "static", dir)
    for series in ["t2", "adc", "highb"]:
        app.config[series + "_" + dir] = os.path.join(basePath, "WebApp", "static", dir, series)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'dcm'}

@app.route('/')
@app.route('/Homepage', methods = ["GET", "POST"])
def index ():
    '''This is the function for the Homepage of the website.
    "Post" requests occur when a request is sent to upload dicoms to the server'''
    clearFiles(app.config["Aligned_DICOM"])
    clearFiles(app.config["JPG_converts"])
    clearFiles(app.config["uploads"])
    clearFiles(app.config["jpg_tumor"])

    uploaded = 0
    FileTypes = ["adc", "highb", "t2"]
    if request.method == 'POST':
        print(request.files)
        for filetype in FileTypes:
            for file in request.files.getlist(filetype):
                successfulSave = False
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    successfulSave = SaveSeries(file,filename, filetype)
                elif not allowed_file(file.filename):
                    print(file.filename)
                    print("Not allowed file type")
                else:
                    print(file.filename)
                    print("No file part")
                if successfulSave == True:
                    uploaded = uploaded + 1
        if uploaded >0:
            subprocess.call(["Python", "Alignment.py", app.config["t2_uploads"], app.config["adc_uploads"], app.config["highb_uploads"], app.config["Aligned_DICOM"]])
            image_list = makeJPGs(app.config["adc_Aligned_DICOM"], app.config["adc_JPG_converts"])
            image_list.append(makeJPGs(app.config["highb_Aligned_DICOM"], app.config["highb_JPG_converts"]))
            image_list.append(makeJPGs(app.config["t2_Aligned_DICOM"], app.config["t2_JPG_converts"]))
            print("the following images have been saved as jpgs")
            print(image_list)
        else:
            print("no files were uploaded")

    return render_template("PIRADS_webAI.html")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    '''When the webpage needs '''
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/Viewer')
def Viewer ():
    return render_template('PIRADS_webAI.html')

@app.route('/api/images')
def api_get_images():
    '''Sends list of uploaded files to webpage'''
    adc = cleanup(gather_files(app.config["adc_JPG_converts"], ".jpg", False),'static', False)[0]
    highb = cleanup(gather_files(app.config["highb_JPG_converts"], ".jpg", False),'static', False)[0]
    t2 = cleanup(gather_files(app.config["t2_JPG_converts"], ".jpg", False),'static', False)[0]
    return jsonify(adc = natsort.natsorted(adc), highb = natsort.natsorted(highb), t2 = natsort.natsorted(t2))

@app.route('/api/imagelist')
def api_get_imagelist():
    adc = cleanup(gather_files(app.config["adc_uploads"], ".dcm", False),"", True)
    highb = cleanup(gather_files(app.config["highb_uploads"], ".dcm", False),"", True)
    t2 = cleanup(gather_files(app.config["t2_uploads"], ".dcm", False),"", True)
    return jsonify(adc = adc, highb = highb, t2 = t2)

@app.route('/api/receiveMarkup', methods = ['POST'])
def api_receiveMarkup():
    if request.method == 'POST':
        data = request.form.to_dict(flat=True)
        print(data)
        markup = {'primarySlice': int(data['primarySlice'])}
        i = 0
        for slice in data['slices'].split(", "):
            if slice in markup.keys():
                markup[slice]['x'].append(int(data['x'].split(", ")[i]))
                markup[slice]['y'].append(int(data['y'].split(", ")[i]))
            else:
                markup[slice] = { 'x': [], 'y': []}
                markup[slice]['x'].append(int(data['x'].split(", ")[i]))
                markup[slice]['y'].append(int(data['y'].split(", ")[i]))
            i = i+1
        print(markup)
        subprocess.call(["Python", "predict.py", markup])
    return "this is your PIRAD score! - message from server def api_receiveMarkup()"

if __name__ == "__main__":
    app.run(debug = True)
    
