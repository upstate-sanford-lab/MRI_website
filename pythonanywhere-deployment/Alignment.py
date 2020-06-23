
import SimpleITK as sitk
import numpy as np
import time
import os
import sys

if len(sys.argv)!=5:
    print("Usage: python alignment.py <path_to_t2> <path_to_adc> <path_to_highb> <path_to_save_dir>")
    sys.exit(1)

class Align:

    def __init__(self):
        '''for development only'''
        self.t2='path to t2'
        self.adc='path to adc'
        self.highb='path to highb'
        self.outdir='path to save directory'

    def align(self):
        '''aligned'''
        names=['','t2','adc','highb']
        for i in range(len(sys.argv)-1):
            if i==1:
                ref_obj=self.load_scan(sys.argv[1])
                ref_image=ref_obj[0]
                series_reader=ref_obj[1]
            if i>=1:
                itk_image=self.load_scan(sys.argv[i])[0]
                resampled_img=self.resample_image(itk_image, ref_image)
                self.write_dicoms(resampled_img,series_reader,names[i])


    def load_scan(self,data_dir):
        '''load images and returns a 3D data object'''

        #load images
        series_IDs = sitk.ImageSeriesReader.GetGDCMSeriesIDs(data_dir)
        series_file_names = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(data_dir, series_IDs[0])

        # define the sitk reader
        series_reader = sitk.ImageSeriesReader()
        series_reader.SetFileNames(series_file_names)

        #read images
        series_reader.MetaDataDictionaryArrayUpdateOn()
        series_reader.LoadPrivateTagsOn()
        image3D = series_reader.Execute()

        return (image3D, series_reader)



    def resample_image(self, itk_image, ref_imge, is_label=False):

        # setting up resample
        original_spacing = itk_image.GetSpacing()
        original_size = itk_image.GetSize()
        out_spacing = ref_imge.GetSpacing()
        out_size = ref_imge.GetSize()
        resample = sitk.ResampleImageFilter()
        resample.SetOutputSpacing(out_spacing)
        resample.SetSize(out_size)
        resample.SetOutputDirection(itk_image.GetDirection())
        resample.SetOutputOrigin(ref_imge.GetOrigin())
        resample.SetTransform(sitk.Transform())
        resample.SetDefaultPixelValue(itk_image.GetPixelIDValue())

        #resample
        resample.SetInterpolator(sitk.sitkLinear)  # sitkBSpline)

        return resample.Execute(itk_image)

    def write_dicoms(self,image,series_reader,name):
        '''
        :return:
        '''

        #make output directory
        if not os.path.exists(os.path.join(sys.argv[4],name)):
            os.mkdir(os.path.join(sys.argv[4],name))

        writer = sitk.ImageFileWriter()
        writer.KeepOriginalImageUIDOn()
        tags_to_copy = ["0010|0010",  # Patient Name
                        "0010|0020",  # Patient ID
                        "0010|0030",  # Patient Birth Date
                        "0020|000D",  # Study Instance UID, for machine consumption
                        "0020|0010",  # Study ID, for human consumption
                        "0008|0020",  # Study Date
                        "0008|0030",  # Study Time
                        "0008|0050",  # Accession Number
                        "0008|0060"  # Modality
                        ]
        modification_time = time.strftime("%H%M%S")
        modification_date = time.strftime("%Y%m%d")

        # Copy some of the tags and add the relevant tags indicating the change.
        # For the series instance UID (0020|000e), each of the components is a number, cannot start
        # with zero, and separated by a '.' We create a unique series ID using the date and time.
        # tags of interest:
        direction = image.GetDirection()
        series_tag_values = [(k, series_reader.GetMetaData(0, k)) for k in tags_to_copy if
                             series_reader.HasMetaDataKey(0, k)] + \
                            [("0008|0031", modification_time),  # Series Time
                             ("0008|0021", modification_date),  # Series Date
                             ("0008|0008", "DERIVED\\SECONDARY"),  # Image Type
                             (
                             "0020|000e", "1.2.826.0.1.3680043.2.1125." + modification_date + ".1" + modification_time),
                             # Series Instance UID
                             ("0020|0037", '\\'.join(
                                 map(str, (direction[0], direction[3], direction[6],  # Image Orientation (Patient)
                                           direction[1], direction[4], direction[7])))),
                             ("0008|103e",
                              series_reader.GetMetaData(0, "0008|103e") + " Processed-SimpleITK")]  # Series Description

        for i in range(image.GetDepth()):
            image_slice = image[:, :, i]
            # Tags shared by the series.
            for tag, value in series_tag_values:
                image_slice.SetMetaData(tag, value)
            # Slice specific tags.
            image_slice.SetMetaData("0008|0012", time.strftime("%Y%m%d"))  # Instance Creation Date
            image_slice.SetMetaData("0008|0013", time.strftime("%H%M%S"))  # Instance Creation Time
            image_slice.SetMetaData("0020|0032", '\\'.join(
                map(str, image.TransformIndexToPhysicalPoint((0, 0, i)))))  # Image Position (Patient)
            image_slice.SetMetaData("0020|0013", str(i))  # Instance Number

            # Write to the output directory and add the extension dcm, to force writing in DICOM format.
            writer.SetFileName(os.path.join(sys.argv[4],name, str(i) + '.dcm'))
            writer.Execute(image_slice)

if __name__== '__main__':
    c=Align()
    c.align()
