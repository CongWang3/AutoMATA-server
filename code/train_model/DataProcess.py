import shutup  # 控制台输出 忽略 warning
shutup.please()

from sklearn.utils import shuffle
from sklearn.preprocessing import LabelEncoder
import torch.optim
import warnings
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

# import os
# os.environ['CUDA_VISIBLE_DEVICES'] ='0'  # 参数待改



warnings.simplefilter(action='ignore', category=RuntimeWarning)
# torch.manual_seed(2022)


def load_data(state="train", jobID="20240808232043_OtJF37SH"):  # train, val, test

    if state == "train":
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")  #  train 改为 data，为了train+analysis流程
    elif state == "test":
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t")
    else:  
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_val.txt", sep="\t")

    # print(data.shape)
    # 删掉第一列数据: GeneID
    data = data.iloc[:, 1:]
    # 打乱数据
    # data = shuffle(data, random_state=2024)
    data = data.dropna()  # 一审
    # print(data.iloc[:,-1].head())
    # 获取数据和label
    feature = data.iloc[:,:-1].values.astype(float) 
    label = data.iloc[:,-1].values.astype(int)

    encoder = LabelEncoder()
    label = encoder.fit_transform(label.ravel())

    feature, label = torch.FloatTensor(feature), torch.LongTensor(label)
    return feature, label


def process(jobID="20240808232043_OtJF37SH", ratio="8:1:1"):

    data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")

    ratio_str = ratio.split(":")
    ratio_num = list(map(int, ratio_str))  # [8, 1, 1]
    train_ratio = ratio_num[0] / sum(ratio_num)
    test_ratio = ratio_num[2] / sum(ratio_num[1:])

    # train_data, res_data = train_test_split(data, test_size=1-train_ratio, random_state=42, stratify=data[["Label"]])
    # val_data, test_data = train_test_split(res_data, test_size=test_ratio, random_state=42, stratify=res_data[["Label"]])
    # 一审
    train_data, res_data = train_test_split(data, test_size=1-train_ratio, stratify=data[["Label"]], shuffle=False)
    val_data, test_data = train_test_split(res_data, test_size=test_ratio, stratify=res_data[["Label"]], shuffle=False)


    # save
    train_data.to_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t", index=False)
    test_data.to_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t", index=False)
    val_data.to_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_val.txt", sep="\t", index=False)

