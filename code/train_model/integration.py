import pandas as pd
import argparse

# 按照样本名称拼接, 缺失值赋0

# 表型文件单独处理（单独一个文件框，文件命名为jobID_pheno.txt）
# 其他组学文件有多少读取多少（一个文件框可上传多个文件，文件命名为jobID_omics_1.txt、jobID_omics_2.txt等）
# 算了弄个简单的，读取基因、转录和蛋白组的文件，然后拼接。不做可选文件数量了

# 参数
parser = argparse.ArgumentParser()
parser.add_argument("--jobID", default="20240808232043_OtJF37SH", type=str)
parser.add_argument("--pheno_file", default="D:/wamp/www/multi_omics_own/example/train_example/jobID_pheno.txt", type=str)
parser.add_argument("--file_1", default="D:/wamp/www/multi_omics_own/example/train_example/jobID_omics_1.txt", type=str)
parser.add_argument("--file_2", default="D:/wamp/www/multi_omics_own/example/train_example/jobID_omics_2.txt", type=str)    
parser.add_argument("--file_3", default="D:/wamp/www/multi_omics_own/example/train_example/jobID_omics_3.txt", type=str)
parser.add_argument("--output_file", default="D:/wamp/www/multi_omics_own/example/train_example/merge.txt", type=str)



args = parser.parse_args()
jobID = args.jobID
pheno_file = args.pheno_file
file_1 = args.file_1
file_2 = args.file_2
file_3 = args.file_3
output_file = args.output_file

print('jobID =',jobID)
print('pheno_file =', pheno_file)
print('file_1 =', file_1)
print('file_2 =', file_2)
print('file_3 =', file_3)
print('output_file =', output_file)



file_1_df = pd.read_csv(file_1, sep='\t')
file_1_df = file_1_df.rename(columns={file_1_df.columns[0]: 'Sample'})

file_2_df = pd.read_csv(file_2, sep='\t')
file_2_df = file_2_df.rename(columns={file_2_df.columns[0]: 'Sample'})
# 拼接
merged_df = pd.merge(file_1_df, file_2_df, on='Sample', how='outer')
del file_2_df, file_1_df

file_3_df = pd.read_csv(file_3, sep='\t')
file_3_df = file_3_df.rename(columns={file_3_df.columns[0]: 'Sample'})
merged_df = pd.merge(merged_df, file_3_df, on='Sample', how='outer')
del file_3_df


pheno_df = pd.read_csv(pheno_file, sep='\t')
pheno_df = pheno_df.rename(columns={pheno_df.columns[0]: 'Sample'})  # 修改列名，第一列修改为Sample
merged_df = pd.merge(merged_df, pheno_df, on='Sample', how='outer')
del pheno_df

# 缺失值赋0
merged_df.fillna('0')

# 保存文件
merged_df.to_csv(output_file, sep='\t', index=False)

