
import torch
from fastai.vision import *
from PIL import Image
import os

print("setting variables")
map_location = 'cpu'
path = os.path.dirname(os.path.abspath(__file__))
learn = load_learner(os.path.join(path,'..','mysite', 'model'))
tumor_val_db=pd.read_csv(os.path.join(path,'PIRADS_only.csv'))


for series in os.listdir(os.path.join(path,'val_test_pt')):
    print(series)
    sum_pred_class = 0
    sum_pred_output = 0
    img_num = 0
    for image in sorted(os.listdir(os.path.join(path,'val_test_pt',series))):
        img = open_image(os.path.join(path,'val_test_pt', series, image))
        pred_class, pred_idx, outputs = learn.predict(img)
        sum_pred_class += int(str(pred_class).split('_')[1])
        sum_pred_output += outputs.numpy()
        img_num += 1
        ave_pred_class = sum_pred_class / img_num
        ave_pred_output = np.argmax(sum_pred_output/img_num)
        rowIndex = tumor_val_db.index[tumor_val_db.loc[:,'tumor_name']==series]
        tumor_val_db.loc[rowIndex, 'web_class'] = str(ave_pred_class)
        tumor_val_db.loc[rowIndex, 'web_output'] = str(ave_pred_output+2) #+2 is for 1) 0 indexing and 2) PIRADS starts at 2 (<- I don'tunderstand this -Andrew)

tumor_val_db.to_csv(os.path.join(path,'tumor_val_db.csv'))
print("done")
