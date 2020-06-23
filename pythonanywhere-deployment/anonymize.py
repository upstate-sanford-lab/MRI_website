import pydicom
import os
import sys

if len(sys.argv)!=2:
    print("Usage: python anonymize.py <input_dir>")
    sys.exit(1)

class Anonymize:

    def __init__(self):
        self.basePATH= os.getcwd()

    def process_dir(self,dir=''):
        '''anonymize all files in directory'''

        for dcm in os.listdir(sys.argv[1]):
            if dcm.endswith('.dcm'):
                dcm_a=self.anon_dicom(os.path.join(sys.argv[1],dcm))
                dcm_a.save_as(os.path.join(sys.argv[1],dcm))

    def anon_dicom(self,path=''):
        '''anonymizes one dicom'''
        ds=pydicom.dcmread(path)
        ds.remove_private_tags()
        type_dict,val_dict=self.tag_repo()
        notag=[]
        for type in type_dict.keys():
            dict_l=type_dict[type]
            for name in dict_l.keys():
                try:
                    ds[dict_l[name]].value=val_dict[type]
                except:
                    notag+=[name]
        return ds


    def tag_repo(self):
        '''repository of dicom tags for anonymization from PMID: 26037716'''

        date_dict = {'StudyDate':0x00080020, 'SeriesDate': 0x00080021, 'AcquisitionDate': 0x00080022, \
                     'ContentDate':0x00080023,'OverlayDate':0x00080024,'CurveDate':0x00080025,\
                     'PatientsBirthDate':0x00100030,'Date':0x0040A121}
        time_dict= {'AcquisitionDatetime':0x0008002A,'StudyTime':0x00080030,'SeriesTime':0x00080031,\
                    'AcquisitionTime':0x00080032,'ContentTime':0x00080033,'OverlayTime':0x00080034,\
                    'CurveTime':0x00080035,'PatientsBirthTime':0x00100032,'DateTime':0x0040A120,\
                    'Time':0x0040A122}
        num_dict={'AccessionNumber':0x00080050,'ReferringPhysiciansTelephoneNumber':0x00080094,\
                  'ReferringPhysicianIDSequence':0x00080096,'PhysicianOfRecordIDSequence':0x00081049,\
                  'PerformingPhysicianIDSequence':0x00081052,'PhysicianReadingStudyIDSequence':0x00081062,
                  'PatientID':0x00100020,'IssuerOfPatientID':0x00100021,'OtherPatientIDs':0x00101000,\
                  'PatientsTelephoneNumbers':0x00102154,'StudyID':0x00200010}
        name_dict={'ReferringPhysiciansName':0x00080090,'PhysicianOfRecord':0x00081048,\
                   'PerformingPhysiciansName':0x00081050,'NameOfPhysicianReadingStudy':0x00081060,\
                   'OperatorsName':0x00081070,'PatientsName':0x00100010,'OtherPatientNames':0x00101001,\
                   'PatientsBirthName':0x00101005,'PatientsMothersBirthName':0x00101060,\
                   'PersonName':0x0040A123}
        inst_dict={'InstitutionName':0x00080080,'InstitutionalDepartmentName':0x00081040,\
                   'PatientsInstitutionResidence':0x00380400}
        location_dict={'InstitutionAddress':0x0008008,'ReferringPhysiciansAddress':0x00080092,\
                       'CountryOfResidence':0x00102150,'RegionOfResidence':0x00102152,\
                       'CurrentPatientLocation':0x00380300}
        gender_dict={'PatientsSex':0x00100040,'PatientsAddress':0x00101040}

        #save tags as dictionary
        type_dict={'dates':date_dict,'time':time_dict,'name':name_dict,'num':num_dict,'loc':location_dict,\
                   'sex':gender_dict,'inst':inst_dict}
        val_dict={'dates':'460 BC','time':'000:0001','name':'Duck, Donald','num':'00000000',\
                  'loc':'Mars','inst':'Best Place Ever','sex':'!!!'}
        return type_dict,val_dict



if __name__=='__main__':
    c=Anonymize()
    c.process_dir()
