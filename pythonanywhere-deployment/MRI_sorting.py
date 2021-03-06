import os
import shutil
import pydicom
import pandas as pd
import xml.etree.ElementTree as ET


class ParseMRI:

    def __init__(self):
        self.basePATH=None
        self.savePATH = None


    def sort_dm_all(self,dir):
        ''' recursively searches for dicoms and sorts them '''
        for file in os.listdir(dir):
            print('sorting files for patient {}'.format(file))
            if not file.startswith('.'):
                if os.path.isdir(os.path.join(dir,file)):
                    os.chdir(os.path.join(dir,file))
                    self.sort_dm_all(os.path.join(dir,file))
                elif file.endswith('.dcm'):
                    self.sort_dcm(filepath=os.path.join(dir,file))


    def sort_dcm(self,filepath):
        '''
        makes new directories if not already present and copies the dicom files to the new directory
        :return:
        '''
        #filepath=os.path.join(self.basePATH,'Labarge_Kevin_J_19550613_3648187','8188128_20161116','series','IM-0002-0001.dcm')

        filename = os.path.basename(filepath)
        #try:
        file_l = pydicom.dcmread(filepath)
        ID = file_l[0x010, 0x020].value
        series = file_l[0x008, 0x103e].value
        series_n = self.remove_chars(series)  # removes strange characters
        study_date=file_l[0x008, 0x020].value
        if ID not in os.listdir(self.savePATH):
            os.mkdir(os.path.join(self.savePATH,ID))
        if study_date not in os.listdir(os.path.join(self.savePATH,ID)):
            os.mkdir(os.path.join(self.savePATH, ID,study_date))
        if series_n not in os.listdir(os.path.join(self.savePATH, ID,study_date)):
            os.mkdir(os.path.join(self.savePATH, ID,study_date,series_n))
        if not os.path.exists(os.path.join(self.savePATH,ID, study_date, series_n,filename)):
            shutil.copy2(filepath, os.path.join(self.savePATH,ID, study_date, series_n,filename))
        #except:
        #    print("series {} failure".format(filepath))


    def remove_chars(self,subj):
        '''remvoe specific characters to prevent issues with saving'''
        sc = set([':', '-', '_', '--','&','=','@','/','\\','+','(',')'])
        return ''.join([c for c in subj if c not in sc])
