import pandas as pd
from os.path import join


class DatasetAnalysis:

    def __init__(self):
        self.dsPATH='/Users/sanforth/OneDrive - SUNY Upstate Medical University/Upstate/research/corona/final_ds/'

    def split_num(self,center='SUNY1'): #centers are ['China','Italy','Japan','LIDC-IDRI','SUNY1'],
        '''evaluate splits'''

        file=pd.read_csv(join(self.dsPATH,'final_ds_splits_train.csv'))
        c_file = file.loc[file['center'] == center, :]
        print("number of scans in this dataset is {}".format(c_file.shape[0]))
        for split in ['train','val']:
            sc_file = c_file.loc[c_file['split'] == split, :]
            unique_files=[file.split('_')[0] for file in sc_file['scan_id'].tolist()]
            print("------")
            print(split)
            print("number of scans for {} is {}".format(split,sc_file.shape[0]))
            print("number of unique patients for {} is {}:".format(split,len(set(unique_files))))






if __name__=='__main__':
    c=DatasetAnalysis()
    c.split_num()