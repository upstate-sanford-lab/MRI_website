from flask import Flask, flash, render_template, request, redirect, jsonify
from werkzeug.utils import secure_filename
import json
import pydicom as dicom
import numpy as np
import os
import matplotlib.pyplot as plt
from skimage import measure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import cv2
import natsort
import subprocess

import scipy.ndimage
from matplotlib import pyplot
import scipy.ndimage as ndi
from pydicom.data import get_testdata_files
import pandas as pd


def plot_slice(slice):
    '''NOT CURRENLTY USED. Create a plot for a given slice'''
    plt.imshow(slice.pixel_array, cmap=plt.cm.bone)
    plt.show()

def sample_stack(stack, rows=3, cols=3):
    'NOT CURRENTLY USED. Plots a stack of dicoms in a grid format'
    fig, ax = plt.subplots(rows, cols, figsize=[12, 12])
    sqrt(stack.shape[3])
    for ind in range(rows * cols):
        ax[int(i / rows), int(i % rows)].set_title('slice %d' % ind)
        ax[int(i / rows), int(i % rows)].imshow(stack[ind], cmap='gray')
        ax[int(i / rows), int(i % rows)].axis('off')
    plt.show()

def plot_3d(image, threshold=-300):
    '''NOT CURRENTLY USED. Provides a 3D rendering of a stack of images'''

    verts, faces = measure.marching_cubes(image, threshold)

    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Fancy indexing: `verts[faces]` to generate a collection of triangles
    mesh = Poly3DCollection(verts[faces], alpha=0.70)
    face_color = [0.45, 0.45, 0.75]
    mesh.set_facecolor(face_color)
    ax.add_collection3d(mesh)

    ax.set_xlim(0, p.shape[0])
    ax.set_ylim(0, p.shape[1])
    ax.set_zlim(0, p.shape[2])

    plt.show()

def load_scan(path):
    '''NOT CURRENTLY USED. Return a list of parsed dcm files from a designated folder "path"'''
    slices = []
    for s in os.listdir(path):
        if ".dcm" in s.lower():  # check whether the file is DICOM
            ds = dicom.dcmread(os.path.join(path,s))
        slices.append(ds)
        slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))

    try:
        slice_thickness = np.abs(slices[0].ImagePositionPatient[2] - slices[1].ImagePositionPatient[2])
    except:
        slice_thickness = np.abs(slices[0].SliceLocation - slices[1].SliceLocation)

    for s in slices:
        s.SliceThickness = slice_thickness

    return slices

def get_pixels(slices):
    '''Convert a list of parsed dicom images into a stack of pixel arrays'''
    pixStack = []
    for slice in slices:
        ps = slice.pixel_array.astype(float)
        pixels = (np.maximum(ps, 0) / ps.max()) * 255.0
        pixels = np.uint8(pixels)
        pixStack.append(pixels)
    return np.array(pixStack)

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
                if hasattr(ds, "SliceLocation"):
                    ps = ds.pixel_array.astype(float)
                    pixels = (np.maximum(ps, 0) / ps.max()) * 255.0 #problem : divide by zero when ps.max() = 0
                    pixels = np.uint8(pixels)
                    s = s.replace('.dcm', '.jpg')
                    s = str(round(ds.SliceLocation, 2)) + ", " + s
                    cv2.imwrite(os.path.join(JPG_location, s), pixels)
                    saved_file_list.append(os.path.join("static\JPG_converts", s))
                else:
                    print("slice " + s + " was a likely a scout view")
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
        file.save(os.path.join(app.config['adc_UPLOADS'], filename))
        print(filename + " dicom saved")
    elif series == "highb":
        file.save(os.path.join(app.config['highb_UPLOADS'], filename))
        print(filename + " dicom saved")
    elif series == "t2":
        file.save(os.path.join(app.config['t2_UPLOADS'], filename))
        print(filename + " dicom saved")
    else:
        return False
    return True

def cleanup(images, append, isolateFile):
    '''This function is used to edit file names so that they can be called
    directly by javascript, or so that the file name can be isolated completely
    from a long directory. I am sure there is a better way to do this but so far this has been working for me. '''
    count = 0
    for image in images:
        if isolateFile == True:
            images[count] = image.split('\\')[7]
        else:
            images[count] = append + image.split('static')[1]
        count = count + 1
    return [images,count]



app = Flask(__name__)

app.config["adc_UPLOADS"] = r'C:\Users\MSStore\WebApp\static\uploads\adc'
app.config["highb_UPLOADS"] = r'C:\Users\MSStore\WebApp\static\uploads\highb'
app.config["t2_UPLOADS"] = r'C:\Users\MSStore\WebApp\static\uploads\t2'

app.config["adc_JPG"] = r'C:\Users\MSStore\WebApp\static\JPG_converts\adc'
app.config["highb_JPG"] = r'C:\Users\MSStore\WebApp\static\JPG_converts\highb'
app.config["t2_JPG"] = r'C:\Users\MSStore\WebApp\static\JPG_converts\t2'
app.config["Aligner"] = r'C:\Users\MSStore\WebApp\Alignment.py'
app.config["Aligned"] = r'C:\Users\MSStore\WebApp\static\Aligned_DICOM'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'dcm'}

@app.route('/')
@app.route('/Homepage', methods = ["GET", "POST"])
def index ():
    '''This is the function for the "Homepage of the website.
    "Post" requests occur when a request is sent to upload dicoms to the server'''
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
            subprocess.call(["Alignment.py", app.config["t2_JPG"], app.config["adc_JPG"], app.config["highb_JPG"], app.config["Aligned"]])
            image_list = makeJPGs(app.config["adc_UPLOADS"], app.config["adc_JPG"])
            image_list.append(makeJPGs(app.config["highb_UPLOADS"], app.config["highb_JPG"]))
            image_list.append(makeJPGs(app.config["t2_UPLOADS"], app.config["t2_JPG"]))
            print("the following images have been saved as jpgs")
            print(image_list)
        else:
            print("no files were uploaded")

    return render_template("Homepage.html")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    '''When the webpage needs '''
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/Viewer')
def Viewer ():
    return render_template('Viewer.html')


@app.route('/api/images')
def api_get_images():
    '''Sends list of uploaded files to webpage'''
    adc = cleanup(gather_files(app.config["adc_JPG"], ".jpg", False),'static', False)[0]
    highb = cleanup(gather_files(app.config["highb_JPG"], ".jpg", False),'static', False)[0]
    t2 = cleanup(gather_files(app.config["t2_JPG"], ".jpg", False),'static', False)[0]
    return jsonify(adc = natsort.natsorted(adc), highb = natsort.natsorted(highb), t2 = natsort.natsorted(t2))

@app.route('/api/imagelist')
def api_get_imagelist():
    adc = cleanup(gather_files(app.config["adc_UPLOADS"], ".dcm", False),"", True)
    highb = cleanup(gather_files(app.config["highb_UPLOADS"], ".dcm", False),"", True)
    t2 = cleanup(gather_files(app.config["t2_UPLOADS"], ".dcm", False),"", True)
    print(adc)
    return jsonify(adc = adc, highb = highb, t2 = t2)

# @app.route('/api/pixels')
# def api_get_pixels():
#     adc = []
#     highb = []
#     t2 = []
#     for file in natsort.natsorted(cleanup(gather_files(app.config["adc_UPLOADS"], ".dcm", False))[0]):
#         adc.append(dicom.dcmread(file))
#     for file in natsort.natsorted(cleanup(gather_files(app.config["highb_UPLOADS"], ".dcm", False))[0]):
#         highb.append(dicom.dcmread(file))
#     for file in natsort.natsorted(cleanup(gather_files(app.config["t2_UPLOADS"], ".dcm", False))[0]):
#         t2.append(dicom.dcmread(file))
#     return jsonify(adc = get_pixels(adc).tolist(), highb = get_pixels(highb).tolist(), t2 = get_pixels(t2).tolist())


if __name__ == "__main__":
    app.run(debug = True)
    
