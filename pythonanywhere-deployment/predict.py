#!/usr/bin/python3.8


# python imports - python version is 3.7.3
# tested with os Ubuntu 18.04 + NVIDIA RTX 1070 and TITAN RTX
#import os
#from collections import Counter
#import numpy as np #1.17.0
#import pandas as pd #0.25.0
#import pydicom #1.3.0#!/usr/bin/python2.7
#from matplotlib import pyplot as plt #matplotlib 3.1.1
import PIL.Image #Pillow 6.1.0
#from functools import reduce
import cv2 #opencv-python 4.1.0.25
#import sklearn #0.2.1
from sklearn.preprocessing import MinMaxScaler
#import imageio #2.5.0
#import scipy #1.3.0
#import random

#fastai v1.0.59
from fastai.vision import *
#from fastai.basic_train import *

class Predict:

    print("predict has been called!")
    random.seed(0)

    def __init__(self):
        self.path = None
        self.dict = None
        self.learn = None

    def calculate_PIRADS(self,idict=None):

        self.segment_slices(idict=self.dict)
        return (self.apply_model())

    def apply_model(self):

        # import model
        learn = self.learn

        #iterate over tumors and calculate
        sum_pred = 0
        img_num = 0
        for image in sorted(os.listdir(os.path.join(os.path.join(self.path, 'protected','jpg_tumor'), 'tumor'))):
            img = open_image(os.path.join(os.path.join(self.path,'protected' ,'jpg_tumor'), 'tumor', image))
            pred_class, pred_idx, outputs = learn.predict(img)
            sum_pred += int(str(pred_class).split('_')[1])
            img_num += 1
            print("for image {} the predicted class is {}".format(image.split('.')[0],pred_class))

        # metrics
        average = sum_pred / img_num
        print("Overall PIRADS Score is {}ish".format(average))
        return (average)


    def segment_slices(self,idict=None):
        '''
        perform segmentation
        :param idict: dictionary from program
        (i.e. example format -s_dicts={'9': {'x': [154, 154, 168, 169, 180, 173, 163],'y': [191, 206, 204, 202, 183, 178, 183]},'10': {'x': [156, 158, 169, 170, 181, 174, 162], 'y': [190, 207, 203, 201, 182, 177, 189]}}
        :return:
        '''

        p_t_i=os.path.join(self.path,'protected','JPG_converts')
        s_dict=self.make_seg_dict(idict) #need

        index=0
        for slice in s_dict.keys():

            # get name for later use
            vals = s_dict[slice]  # select values for each bounding box
            img_num=int(slice)

            # for each bounding box, select the appropriate slice and segment
            seg_i_dict = {}
            for series in os.listdir(p_t_i):
                path=os.path.join(p_t_i,series)
                segmented_image = self.segment_image(path, img_num, vals)
                seg_i_dict[series] = segmented_image

            # extract each sequance array and combine into numpy array
            stacked_image = np.dstack((seg_i_dict['t2'], seg_i_dict['adc'], seg_i_dict['highb']))

            # normalize
            for i in range(0,3):
                stacked_image[:,:,i]=self.rescale_array(stacked_image[:, :, i])

            # make a directory if one doesn't already exist for images, conver to Image and save .jpg

            if not os.path.exists(os.path.join(os.path.dirname(p_t_i), 'jpg_tumor')):
                os.mkdir(os.path.join(os.path.dirname(p_t_i), 'jpg_tumor'))

            if not os.path.exists(os.path.join(os.path.dirname(p_t_i), 'jpg_tumor', 'tumor')):
                os.mkdir(os.path.join(os.path.dirname(p_t_i), 'jpg_tumor', 'tumor'))
            os.chdir(os.path.join(os.path.dirname(p_t_i), 'jpg_tumor', 'tumor'))

            # opencv solution
            cv2.imwrite(os.path.join(os.path.dirname(p_t_i), 'jpg_tumor', 'tumor', slice+'.jpg'),
                        stacked_image)
            index+=1


    def make_seg_dict(self, s_dicts=None, id='None'):
        '''
        makes a dictionary with format {'slice#':['name','xmin','xmax','ymin','ymax']}
        :param s_dicts: the dictionary of values from program.
        (i.e. example format -s_dicts={'9': {'x': [154, 154, 168, 169, 180, 173, 163],'y': [191, 206, 204, 202, 183, 178, 183]},'10': {'x': [156, 158, 169, 170, 181, 174, 162], 'y': [190, 207, 203, 201, 182, 177, 189]}}
        :param id: nothing for now, may add in the future
        :return:
        '''
        o_d={}
        for slice in s_dicts.keys():
            l=s_dicts[slice]
            o_d[slice]=['ID_future',min(l['x']),max(l['x']),min(l['y']),max(l['y'])]
        return(o_d)


    def segment_image(self,p_img, img_num, vals, pad=10):
        '''
        helper function that takes in path to image, values and performs the segmentation
        :param p_img: path to image
        :param img_num: image number
        :param vals: list with following values ['name','xmin','xmax','ymin','ymax']
        :param pad: number of voxels to padd
        :return:
        '''
        img = PIL.Image.open(os.path.join(p_img,str(img_num)+'.jpg')) #Removed PIL and now it works
        data = self.rescale_array(img)  # normalize by slice
        data_downsampled = data[vals[2] - pad:vals[4] + pad, vals[1] - pad:vals[3] + pad]
        return data_downsampled


    def rescale_array(self,array):
        '''rescales array to have imaging-type values'''
        scaler = MinMaxScaler(feature_range=(0, 255))
        scaler = scaler.fit(array)
        X_scaled = scaler.transform(array)
        return (X_scaled)


if __name__=="__main__":
    c=Predict()
    c.calculate_PIRADS()
