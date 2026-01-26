import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from train_model.VAE import load_and_predict, evaluate_predictions, visualize_predictions, set_random_seed
import torch
import numpy as np
import argparse
import os
import warnings
warnings.filterwarnings('ignore')

if __name__ == "__main__":
    """
    预测主函数
    cmd:  D:/Anaconda3/envs/pt37/python.exe f:/breeding/code/my_code/multi-omics/predict_vae.py
    输出：prediction_results_*.npy、prediction_results.png、prediction_results.json

    """
    parser = argparse.ArgumentParser(description='VAE模型预测脚本')
    
    # 模型路径
    parser.add_argument('--model_path', type=str, default='vae_model.pth', help='模型文件路径')
    parser.add_argument('--scaler_path', type=str, default='scaler.pkl', help='预处理器文件路径')
    
    # 数据路径
    # parser.add_argument('--jobid', type=str, default='20240808232043_OtJF37SH', help='数据集ID')
    parser.add_argument('--data_path', type=str, default='../../data/train_exmaple_un/train_exmaple_un_test.txt', help='新数据文件路径 (CSV格式)')
    # parser.add_argument('--data_shape', type=str, default='50,100', help='数据形状，格式: "samples,features" (如: "100,50")')
    
    # 评估选项
    parser.add_argument('--evaluate', action='store_true', default=1, help='是否进行预测评估')
    parser.add_argument('--visualize', action='store_true', default=0, help='是否可视化预测结果')
    parser.add_argument('--save_results', action='store_true', default=1, help='是否保存预测结果')
    parser.add_argument('--output_path', type=str, default='prediction_results', help='输出文件路径前缀')
    
    # 其他参数
    parser.add_argument('--random_seed', type=int, default=42, help='随机种子')
    
    args = parser.parse_args()
    
    # 设置随机种子
    set_random_seed(args.random_seed)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # Prepare data
    if args.data_path:
        # Load data from file
        print(f"Load data from file: {args.data_path}")
        import pandas as pd
        data = pd.read_csv(args.data_path, sep="\t")
        data = data.dropna().values
    print(f"Data shape: {data.shape}")
    
    # Load model and predict
    try:
        prediction_results = load_and_predict(
            args.model_path, args.scaler_path, data, device, args
        )
    except Exception as e:
        print(f"Prediction failed: {e}")
        exit(0)
    
    # Evaluate prediction results
    if args.evaluate:
        metrics = evaluate_predictions(
            prediction_results, 
            args.output_path if args.save_results else None
        )
    
    # Visualize results
    if args.visualize:
        visualize_predictions(
            prediction_results,
            args.output_path + '.png' if args.save_results else None
        )
    
    # Save prediction results
    if args.save_results:
        # Save reconstructed data
        np.save(args.output_path + '_reconstructed.npy', prediction_results['reconstructed_data'])
        np.save(args.output_path + '_latent_mu.npy', prediction_results['latent_mu'])
        np.save(args.output_path + '_latent_logvar.npy', prediction_results['latent_logvar'])
    
    

