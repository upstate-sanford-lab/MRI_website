import os
import pandas as pd

path = os.path.dirname(os.path.abspath(__file__))
data = pd.read_csv(os.path.join(path,'tumor_val_db.csv'))
statsFilled = pd.read_csv(os.path.join(path, "statistics.csv"))
print(statsFilled)

def isNaN(num):
    return num != num

def kappa():
    print("running stats")
    totalAgree=0
    total = 0
    chanceAgreeProbs = {}
    for reader in ["pred_total","gt_total"]:
        for category in range(1,6):
            chanceAgreeProbs[reader+str(category)] = 0

    for i in range(1,6):
        for j in range(1,6):
            row = "gt"+str(i)
            column = "pred"+str(j)
            agreements = data[(data["pred_PIRADS"]==i) & (data["web_output"] == j)].shape[0]
            statsFilled.loc[statsFilled['firstline']==row,column] = agreements

            value = pd.to_numeric(statsFilled.loc[statsFilled['firstline']==row,'gt_total']).to_numpy()[0]
            if isNaN(value):
                statsFilled.loc[statsFilled['firstline']==row,'gt_total'] = 0
            else:
                statsFilled.loc[statsFilled['firstline']==row,'gt_total'] = value + agreements
                chanceAgreeProbs["gt_total"+str(i)]=value +agreements

            value = pd.to_numeric(statsFilled.loc[statsFilled['firstline']=='pred_total',column]).to_numpy()[0]
            if isNaN(value):
                statsFilled.loc[statsFilled['firstline']=='pred_total',column] = 0
            else:
                statsFilled.loc[statsFilled['firstline']=='pred_total',column] = value + agreements
                chanceAgreeProbs["pred_total"+str(j)]=value+agreements

            total = total+agreements
            if i == j:
                totalAgree = totalAgree+agreements

    statsFilled.loc[statsFilled['firstline']=='pred_total','gt_total']=total


    actualAgreeProb = totalAgree / total
    chanceAgreeProb = 0;
    for category in range(1,6):
        chanceAgreeProb = chanceAgreeProb + (chanceAgreeProbs["pred_total"+str(category)] * chanceAgreeProbs["gt_total"+str(category)])
    chanceAgreeProb = chanceAgreeProb/(total * total)
    kappaScore = (actualAgreeProb - chanceAgreeProb) / (1 - chanceAgreeProb)
    print(statsFilled)
    print(chanceAgreeProb)
    print(actualAgreeProb)
    print(kappaScore)
    statsFilled.to_csv(os.path.join(path,'statsFilled.csv'))



kappa()
print("done")
