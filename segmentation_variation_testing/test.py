from PIL import Image
import os
import pydicom
import cv2
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import matplotlib.pyplot as plt
from parsing_VOI import ParseVOI
from natsort import natsorted
import pandas as pd

# Usage:
# Update "ProstateX_dir"
# It is not necessary to update "save", this is an artifact of previous attempts
# Update "model_path"
# Update "pads" as needed


def segment_variation_testing():
    ProstateX_dir = r'C:\Users\MSStore\Desktop\Prostate X'
    save = r'C:\Users\MSStore\Desktop\Test_padded_jpgs'
    model_path = ''
    vois_excluded = ['tz_bt.voi','tz_pseg.voi','urethra_bt.voi','wp_bt.voi','wp_pseg.voi', 'test_point.voi']
    learn = load_learner(model_path)
    
    pads = [-10,-5,-3,-2,-1,0,1,2,3,5,10]
    id = 0
    log = {}


    if not os.path.exists(save):
        os.mkdir(save)
    parser = ParseVOI()
    dataset_dict = {}
    for folder in os.listdir(ProstateX_dir):
        dicoms_dir = {}
        bboxes = []
        dicoms_dir['adc'] = []
        dicoms_dir['highb'] = []
        dicoms_dir['t2'] = []
        for dicom in os.listdir(os.path.join(ProstateX_dir, folder, 'dicoms', 'adc', 'aligned')):
            dicoms_dir['adc'].append(os.path.join(ProstateX_dir, folder, 'dicoms', 'adc', 'aligned', dicom))
        for dicom in os.listdir(os.path.join(ProstateX_dir, folder, 'dicoms', 'highb', 'aligned')):
            dicoms_dir['highb'].append(os.path.join(ProstateX_dir, folder, 'dicoms', 'highb', 'aligned', dicom))
        for dicom in os.listdir(os.path.join(ProstateX_dir, folder, 'dicoms', 't2')):
            dicoms_dir['t2'].append(os.path.join(ProstateX_dir, folder, 'dicoms', 't2', dicom))
        voi_dir = os.path.join(ProstateX_dir, folder, 'voi')
        for voi in os.listdir(voi_dir):
            if voi.endswith('.voi') and voi not in vois_excluded:
                bboxes.append(parser.one_dict(os.path.join(voi_dir, voi)))
        dataset_dict[folder] = {'dicoms_dir': dicoms_dir, 'bboxes': bboxes}
    for patient in dataset_dict:
        print("working on {}".format(patient))
        if not os.path.exists(os.path.join(save, patient)):
            os.mkdir(os.path.join(save, patient))
        for parsed_bbox in dataset_dict[patient]['bboxes']:
            voi_name = parsed_bbox[list(parsed_bbox.keys())[0]][0]
            dicoms = dataset_dict[patient]['dicoms_dir']
            save_path = os.path.join(save, patient, voi_name)
            if not os.path.exists(save_path):
                os.mkdir(save_path)

            for pad in pads:
                log, id = segment_aligned(dicoms, parsed_bbox, save_path, pad, log, id, learn)
                id = id - len(parsed_bbox)
            id = id + len(parsed_bbox)

    refined_log = {}
    for id in log:
        pad_dicts = log[id][2]
        pad_scores = []
        for key in pad_dicts:
            score = pad_dicts[key]
            pad_scores.append(score)
        refined_log[id] = [log[id][0], log[id][1]] + pad_scores
    print("almost done")
    print(refined_log)

    pads_as_strings = []
    for pad in pads:
        pads_as_strings.append(str(pad))

    results = pd.DataFrame.from_dict(refined_log, orient='index',
                       columns=['voi name', 'slice']+pads_as_strings)

    print(results)
    results.to_csv(os.path.join(save,'results.csv'))
    print("done - see results as csv in {}".format(save))


def segment_aligned(dicom_paths, bboxes, save_path, pad, log, id, learn):
    # print(dicom_paths)
    # print(bboxes)
    index = 0
    if not bboxes == None:
        for bbox in bboxes.keys():
            vals = bboxes[bbox]  # select values for each bounding box

            if str(id) in log:
                padded_scores = log[str(id)][2]
            else:
                padded_scores = {}

            print("the id is {}, the padded scores are {}".format(id, padded_scores))

            # print("vals are {}".format(vals))

            # for each bounding box, select the appropriate slice and segment
            segmented_image_dict = {}
            ave_sd_dict = {}
            for series in dicom_paths:
                paths = dicom_paths[series]
                paths = natsorted(paths)
                # path_to_load = paths[int(bbox)]
                path_to_load = paths[int(bbox)-1]
                # print("path to load is {}".format(path_to_load))
                # segmented_image = segment_image(save,path_to_load, vals, dir, index, series)
                ds = pydicom.dcmread(path_to_load)
                data = ds.pixel_array
                ave_sd_dict[series] = average_of_series(paths)  # returns tuple of average,sd
                segmented_image = data[vals[2] - pad:vals[4] + pad, vals[1] - pad:vals[3] + pad]
                segmented_image_dict[series] = segmented_image

                # extract each sequance array and combine into numpy array
            t2 = segmented_image_dict['t2']
            adc = segmented_image_dict['adc']
            highb = segmented_image_dict['highb']
            stacked_image = np.dstack((t2, adc, highb))

            if stacked_image.shape[0] > 0 and stacked_image.shape[1] > 0:
                # normalize --> note, data is normalized on patient level
                stacked_image[:, :, 0] = rescale_array(stacked_image[:, :, 0], ave_sd_dict['t2'][0], ave_sd_dict['t2'][1])
                stacked_image[:, :, 1] = rescale_array(stacked_image[:, :, 1], ave_sd_dict['adc'][0], ave_sd_dict['t2'][1])
                stacked_image[:, :, 2] = rescale_array(stacked_image[:, :, 2], ave_sd_dict['highb'][0],ave_sd_dict['t2'][1])

                # make a directory if one doesn't already exist for images, conver to Image and save .jpg



                # opencv solution
                # save_slice = os.path.join(save_path, bbox)
                # if not os.path.exists(save_slice):
                #     os.mkdir(save_slice)
                # cv2.imwrite(os.path.join(save_slice, 'Padded with ' + str(pad) + ', ' + vals[0] + '.jpg'), stacked_image)

                # direct predict solution
                pred_class, pred_idx, outputs = learn.predict(stacked_image)
                padded_scores[str(pad)] = int(str(pred_class).split('_')[1])
                # padded_scores[str(pad)] = pad
                # log[str(id)] = [vals[0], int(bbox), padded_scores]





            else:
                # print("There was a problem with {} . The shape was originally {} and segmented to {}".format(path_to_load, data.shape,stacked_image.shape))
                # print("the image was segmented in length from {} to {}, an height from {} to {}".format(vals[2] - pad,
                #                                                                                         vals[4] + pad,
                #                                                                                         vals[1] - pad,
                #                                                                                         vals[3] + pad))
                # print("")

                padded_scores[str(pad)] = -1
                log[str(id)] = [vals[0], int(bbox), padded_scores]
            id = id + 1
            index += 1

    return log, id

def segment_image(save,path_to_image,vals,patient_dir,index,series,pad=10):
    '''
    helper function that takes in path to image, values and performs the segmentation
    :param path_to_image: self explanatory
    :param vals: indexes
    :param patient_dir:
    :param index:
    :param series:
    :param pad: number of voxes around the image in question
    :return:
    '''
    # print(path_to_image)
    ds = pydicom.dcmread(path_to_image)
    data = ds.pixel_array
    # plt.imshow(data, cmap=plt.cm.bone)
    # plt.show()


    # print('xmin {}:xmax {} ymin {}:ymax {}'.format(vals[2], vals[4], vals[1], vals[3]))
    # print('The image has {} x {} voxels'.format(data.shape[0],data.shape[1]))
    data_downsampled = data[vals[2] - pad:vals[4] + pad, vals[1] - pad:vals[3] + pad]
    # print('The downsampled image has {} x {} voxels'.format(
    #     data_downsampled.shape[0], data_downsampled.shape[1]))

    ds.PixelData = data_downsampled.tobytes()
    ds.Rows, ds.Columns = data_downsampled.shape

    # if not os.path.exists(os.path.join(save,'T2')):
    #     os.mkdir(os.path.join(save,'T2'))
    # if not os.path.exists(os.path.join(save,'T2', patient_dir)):
    #     os.mkdir(os.path.join(save,'T2', patient_dir))
    # os.chdir(os.path.join(save,'T2',patient_dir))
    #
    # #save image
    # if series == 't2':
    #     ds.save_as(patient_dir + '_' + str(index) + '_T2_' + vals[0] + '.dcm')

    return data_downsampled

def dicom_paths_find(dir):
    '''
    start in patient directory, then find all dicom files listed in that directory -->  note adc and highb
    are aligned to t2
    :param database (path): the base director of all patients
    :param patient_dir (str): the folder name of the files
    :return: list of paths to dicom files within patient directory
    '''

    #set base directory

    #set path to each directory for aligned files
    t2_dir=os.path.join(dir,'t2')
    adc_dir=os.path.join(dir,'adc')
    highb_dir=os.path.join(dir,'highb')

    #setup dict names
    series_dict={'t2':t2_dir,'adc':adc_dir,'highb':highb_dir}

    #loop over series and joint with series dir path to get paths to dicom files for all images in all series
    dicom_dict={}
    for series in series_dict.keys():
        try:
            files=os.listdir(series_dict[series])
            path_list=[]
            for file in files:
                path_list+=[os.path.join(series_dict[series],file)]
            #path_list=order_dicom(path_list)
            dicom_dict[series]=path_list
        except:
            print("series {} not able to be loaded".format(series_dict[series]))
    return dicom_dict

def order_dicom(dicom_file_list):
    '''
    As input, this method takes a list of paths to dicom directories (from find_dicom_paths), loads dicom, then orders them
    :param dicom_file_list
    :return list of files in correct order
    '''
    dicoms={}
    for path in dicom_file_list:
        file=path
        ds=pydicom.read_file(path)
        dicoms[str(file)] = float(ds.SliceLocation)
    updated_imagelist=[key for (key, value) in sorted(dicoms.items(), key=lambda x: x[1])]
    return(updated_imagelist)

def rescale_array(array,series_ave,series_sd):
    '''normalize array on series level
    :param array (numpy array) - raw array matrix
    :param series_ave: average across entire series
    :param series_sd: standard deviation of entire array

    '''
    #normalize by series average and sd average (across entire image)
    series_ave=np.float(series_ave)
    normalized_array=(array-series_ave)/series_sd # using broadcasting

    # minmax scaling --> for viewing
    scaler=MinMaxScaler(feature_range=(0,255))
    scaler=scaler.fit(normalized_array)
    normalized_array=scaler.transform(normalized_array)

    return (normalized_array)

def average_of_series(paths):
    '''helper function that calculates all the average across all elements in a series'''
    slice_num=0
    array_1 = pydicom.dcmread(paths[0]).pixel_array #gets the shape of the first array in the series
    array=np.zeros(shape=(array_1.shape[0],array_1.shape[1],len(paths)))

    #start by contructing multidimensional array from individual dicom slices
    for path in paths:
        pixel_data=pydicom.dcmread(path).pixel_array
        array[:,:,slice_num]=pixel_data
        slice_num = slice_num + 1
    mean_slices=(np.mean(array), np.std(array))
    return mean_slices


segment_variation_testing()

# segment_aligned(r'C:\Users\MSStore\Desktop\Test data aligned\Aligned_DICOM')

# created_JPGs = r'C:\Users\MSStore\Desktop\created JPG'
# established_JPGs = r'C:\Users\MSStore\Desktop\established JPG'
# im1 = Image.open(os.path.join(created_JPGs,'8.jpg'))
# im2 = Image.open(os.path.join(created_JPGs,'9.jpg'))
# im3 = Image.open(os.path.join(created_JPGs,'10.jpg'))
#
#
# im4 = Image.open(os.path.join(established_JPGs,'1_R_mid+anterior_TZ_PIRADS_5_5_5_bt0.jpg'))
# im5 = Image.open(os.path.join(established_JPGs,'1_R_mid+anterior_TZ_PIRADS_5_5_5_bt1.jpg'))
# im6 = Image.open(os.path.join(established_JPGs,'1_R_mid+anterior_TZ_PIRADS_5_5_5_bt2.jpg'))
#
#
# pixels = list(im1.getdata())
# print(im1.size)
# print(pixels)
