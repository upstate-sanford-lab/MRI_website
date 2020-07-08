
import torch
from fastai.vision import *
from predict import Predict
import json

map_location = 'cpu'
path = sys.argv[1]
dict = json.loads(sys.argv[2])
user = sys.argv[3]

c = Predict()
c.user = user
c.path = path
c.dict = dict
c.learn = load_learner(os.path.join(path, 'model'))
score = c.calculate_PIRADS()
