import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))


from train_model.ladder import load_model, predict, set_random_seed, ModelEvaluator, visualize_results, print_evaluation_report
import torch
import numpy as np
import argparse
import os
import warnings
warnings.filterwarnings('ignore')

def load_and_predict(model_path, scaler_path, new_data, device, args=None):
    """
    Load model and predict new data
    """
    print("Loading model and preprocessor...")
    
    # Load model
    model, scaler = load_model(model_path, scaler_path, device)
    
    print(f"Model loaded, input dimension: {model.input_dim}")
    print(f"Number of classes: {model.num_classes}")
    print(f"New data shape: {new_data.shape}")
    
    # Check data dimension
    if new_data.shape[1] != model.input_dim:
        raise ValueError(f"Data dimension mismatch! Model expects {model.input_dim} dimensions, but input data has {new_data.shape[1]} dimensions")
    
    # Predict
    print("Predicting...")
    predictions, probabilities, reconstructed, encoded_features = predict(model, scaler, new_data, device)
    
    # Create class names (based on number of classes)
    class_names = [f'{i}' for i in range(model.num_classes)]
    predicted_labels = [class_names[pred] for pred in predictions]
    
    print("Prediction completed!")
    
    return {
        'original_data': new_data,
        'predictions': predictions,
        'predicted_labels': predicted_labels,
        'probabilities': probabilities,
        'reconstructed_data': reconstructed,
        'encoded_features': encoded_features,
        'model': model,
        'scaler': scaler,
        'class_names': class_names
    }

def evaluate_predictions(prediction_results, save_path=None):
    """
    Evaluate prediction results
    """
    print("\n" + "="*60)
    print("Prediction results evaluation")
    print("="*60)
    
    original = prediction_results['original_data']
    reconstructed = prediction_results['reconstructed_data']
    probabilities = prediction_results['probabilities']
    predictions = prediction_results['predictions']
    
    # Calculate reconstruction metrics
    mse = np.mean((original - reconstructed) ** 2)
    mae = np.mean(np.abs(original - reconstructed))
    correlation = np.corrcoef(original.flatten(), reconstructed.flatten())[0, 1]
    
    # Calculate prediction confidence
    max_probabilities = np.max(probabilities, axis=1)
    avg_confidence = np.mean(max_probabilities)
    min_confidence = np.min(max_probabilities)
    max_confidence = np.max(max_probabilities)
    
    # Calculate prediction distribution
    unique_predictions, prediction_counts = np.unique(predictions, return_counts=True)
    prediction_distribution = dict(zip(unique_predictions, prediction_counts))
    
    # Print evaluation results
    print("\n Reconstruction quality evaluation:")
    print("-" * 30)
    print(f"Mean squared error (MSE): {mse:.6f}")
    print(f"Mean absolute error (MAE): {mae:.6f}")
    print(f"Correlation: {correlation:.6f}")
    
    print("\n Prediction quality evaluation:")
    print("-" * 30)
    print(f"Average confidence: {avg_confidence:.4f}")
    print(f"Minimum confidence: {min_confidence:.4f}")
    print(f"Maximum confidence: {max_confidence:.4f}")
    
    print("\n Prediction distribution:")
    print("-" * 30)
    for pred, count in prediction_distribution.items():
        percentage = (count / len(predictions)) * 100
        print(f"Class {pred}: {count} samples ({percentage:.1f}%)")
    
    # Save evaluation results
    if save_path:
        evaluation_data = {
            'reconstruction_metrics': {
                'mse': float(mse),
                'mae': float(mae),
                'correlation': float(correlation)
            },
            'prediction_metrics': {
                'avg_confidence': float(avg_confidence),
                'min_confidence': float(min_confidence),
                'max_confidence': float(max_confidence),
                'prediction_distribution': {str(k): int(v) for k, v in prediction_distribution.items()}
            }
        }
        
        json_path = save_path.replace('.png', '.json') if save_path.endswith('.png') else save_path + '.json'
        with open(json_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
    
    return {
        'reconstruction_metrics': {
            'mse': mse,
            'mae': mae,
            'correlation': correlation
        },
        'prediction_metrics': {
            'avg_confidence': avg_confidence,
            'min_confidence': min_confidence,
            'max_confidence': max_confidence,
            'prediction_distribution': prediction_distribution
        }
    }

def visualize_predictions(prediction_results, save_path=None):
    """
    Visualize prediction results
    """
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.manifold import TSNE
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle('Ladder network prediction results visualization', fontsize=16, fontweight='bold')
    
    original = prediction_results['original_data']
    reconstructed = prediction_results['reconstructed_data']
    predictions = prediction_results['predictions']
    probabilities = prediction_results['probabilities']
    encoded_features = prediction_results['encoded_features']
    
    # 1. Reconstruction quality scatter plot
    ax1 = axes[0, 0]
    original_flat = original.flatten()
    reconstructed_flat = reconstructed.flatten()

    if len(original_flat) > 1000:
        indices = np.random.choice(len(original_flat), 1000, replace=False)
        original_sample = original_flat[indices]
        reconstructed_sample = reconstructed_flat[indices]
    else:
        original_sample = original_flat
        reconstructed_sample = reconstructed_flat
    
    ax1.scatter(original_sample, reconstructed_sample, alpha=0.5, s=1)
    ax1.plot([original_sample.min(), original_sample.max()], 
             [original_sample.min(), original_sample.max()], 'r--', lw=2)
    ax1.set_xlabel('Original data')
    ax1.set_ylabel('Reconstructed data')
    ax1.set_title('Reconstruction quality scatter plot')
    ax1.grid(True, alpha=0.3)
    
    # 2. Prediction distribution
    ax2 = axes[0, 1]
    unique_predictions, prediction_counts = np.unique(predictions, return_counts=True)
    bars = ax2.bar(unique_predictions, prediction_counts, color='skyblue', alpha=0.7)
    ax2.set_xlabel('Predicted class')
    ax2.set_ylabel('Sample number')
    ax2.set_title('Prediction distribution')
    ax2.grid(True, alpha=0.3)
    
    # Add numerical labels
    for bar, count in zip(bars, prediction_counts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                f'{count}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Prediction confidence distribution
    ax3 = axes[1, 0]
    max_probabilities = np.max(probabilities, axis=1)
    ax3.hist(max_probabilities, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
    ax3.set_xlabel('Prediction confidence')
    ax3.set_ylabel('Frequency')
    ax3.set_title(f'Prediction confidence distribution (average: {np.mean(max_probabilities):.3f})')
    ax3.grid(True, alpha=0.3)
    
    # # 4. Feature space visualization (t-SNE)
    # ax4 = axes[1, 0]
    # if len(encoded_features) > 0:
    #     # Use the last layer encoded features
    #     features = encoded_features[-1]
    #     if features.shape[1] > 2:
    #         tsne = TSNE(n_components=2, random_state=42)
    #         features_2d = tsne.fit_transform(features[:1000])  # 只使用前1000个样本
    #     else:
    #         features_2d = features[:1000]
        
    #     scatter = ax4.scatter(features_2d[:, 0], features_2d[:, 1], 
    #                         c=predictions[:1000], cmap='tab10', alpha=0.6)
    #     ax4.set_xlabel('t-SNE 1')
    #     ax4.set_ylabel('t-SNE 2')
    #     ax4.set_title('特征空间可视化')
    #     plt.colorbar(scatter, ax=ax4, label='预测类别')
    
    # # 5. 重构误差分布
    # ax5 = axes[1, 1]
    # reconstruction_error = np.abs(original - reconstructed)
    # ax5.hist(reconstruction_error.flatten(), bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    # ax5.set_xlabel('重构误差')
    # ax5.set_ylabel('频次')
    # ax5.set_title('重构误差分布')
    # ax5.grid(True, alpha=0.3)
    
    # 6. 各类别置信度箱线图
    ax6 = axes[1, 1]
    if len(unique_predictions) > 1:
        confidence_by_class = []
        class_labels = []
        for pred_class in unique_predictions:
            class_mask = predictions == pred_class
            class_confidences = max_probabilities[class_mask]
            confidence_by_class.append(class_confidences)
            class_labels.append(f'Class {pred_class}')
        
        ax6.boxplot(confidence_by_class, labels=class_labels)
        ax6.set_ylabel('Prediction confidence')
        ax6.set_title('Prediction confidence distribution by class')
        ax6.tick_params(axis='x', rotation=45)
        ax6.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    # plt.show()
    plt.close()

def save_predictions_to_txt(sample_names, prediction_results, output_path):
    """
    Save prediction results to txt file
    """
    predictions = prediction_results['predictions']
    predicted_labels = prediction_results['predicted_labels']
    probabilities = prediction_results['probabilities']
    
    # Get class names
    class_names = prediction_results['class_names']
    
    # Create result DataFrame
    results_df = pd.DataFrame({
        'Sample': sample_names,
        'Predicted_Label': predicted_labels
        # 'Predicted_Class_Index': predictions
    })
    
    # # 添加每个类别的概率
    # for i, class_name in enumerate(class_names):
    #     results_df[f'Probability_{class_name}'] = probabilities[:, i]
    
    # 添加最大概率和置信度
    results_df['Probability'] = np.max(probabilities, axis=1)  # 最大概率
    # results_df['Confidence_Level'] = results_df['Max_Probability'].apply(
    #     lambda x: 'High' if x > 0.8 else 'Medium' if x > 0.6 else 'Low'
    # )
    
    # 保存到txt文件
    results_df.to_csv(output_path, sep='\t', index=False)
    
    # # print(f"预测结果已保存到: {output_path}")
    # print(f"包含 {len(sample_names)} 个样本的预测结果")
    # print(f"预测类别分布:")
    class_counts = results_df['Predicted_Label'].value_counts()
    for class_name, count in class_counts.items():
        print(f"  {class_name}: {count} samples")

if __name__ == "__main__":
    """
    预测主函数
    cmd:  D:/Anaconda3/envs/pt37/python.exe f:/breeding/code/my_code/multi-omics/predict_ladder.py
    输出：ladder_prediction_results_*.npy、ladder_prediction_results.png (visualize参数=1)、ladder_prediction_results.json

    """
    parser = argparse.ArgumentParser(description='梯形网络半监督学习模型预测脚本')
    
    # 模型路径
    parser.add_argument('--model_path', type=str, default='ladder_model.pth', help='模型文件路径')
    parser.add_argument('--scaler_path', type=str, default='ladder_scaler.pkl', help='预处理器文件路径')
    
    # 数据路径
    parser.add_argument('--data_path', type=str, default='../../data/train_example_semi/train_example_semi_test.txt', help='新数据文件路径 (txt格式)')
    
    # 评估选项
    parser.add_argument('--evaluate', action='store_true', default=1, help='是否进行预测评估')
    parser.add_argument('--visualize', action='store_true', default=0, help='是否可视化预测结果')
    parser.add_argument('--save_results', action='store_true', default=1, help='是否保存预测结果')
    parser.add_argument('--output_path', type=str, default='ladder_prediction_results', help='输出文件路径前缀')
    
    # 其他参数
    parser.add_argument('--random_seed', type=int, default=42, help='随机种子')
    
    args = parser.parse_args()
    
    # 设置随机种子
    set_random_seed(args.random_seed)
    
    # 检查CUDA可用性
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    # 准备数据
    if args.data_path:
        # 从文件加载数据
        import pandas as pd
        data_df = pd.read_csv(args.data_path, sep="\t")
        data_df = data_df.dropna()
        sample_names = data_df.iloc[:, 0].values  # 第一列是样本名称
        data = data_df.iloc[:, 1:-1].values.astype(float)  # 中间列是特征
        labels = data_df.iloc[:, -1].values  # 最后一列是标签（可能为空）
    print(f"data shape: {data.shape}")
    print(f"sample number: {len(sample_names)}")
    print(f"feature dimension: {data.shape[1]}")
    
    # 加载模型并预测
    try:
        prediction_results = load_and_predict(
            args.model_path, args.scaler_path, data, device, args
        )
    except Exception as e:
        print(f"Prediction failed: {e}")
        exit(0)
    
    # 评估预测结果
    if args.evaluate:
        metrics = evaluate_predictions(
            prediction_results, 
            args.output_path if args.save_results else None
        )
    
    # 可视化结果
    if args.visualize:
        visualize_predictions(
            prediction_results,
            args.output_path + '.png' if args.save_results else None
        )
    
    # 保存预测结果
    if args.save_results:
        # 保存预测结果
        # np.save(args.output_path + '_predictions.npy', prediction_results['predictions'])
        # np.save(args.output_path + '_predicted_labels.npy', prediction_results['predicted_labels'])
        # np.save(args.output_path + '_probabilities.npy', prediction_results['probabilities'])
        # np.save(args.output_path + '_reconstructed.npy', prediction_results['reconstructed_data'])
        
        # 保存编码特征
        for i, features in enumerate(prediction_results['encoded_features']):
            np.save(args.output_path + f'_encoded_features_{i}.npy', features)
        
        # 保存预测结果到txt文件
        save_predictions_to_txt(sample_names, prediction_results, args.output_path + '.txt')
        
        # print(f"预测结果已保存到: {args.output_path}_*.npy")
        # print(f"预测结果已保存到: {args.output_path}_predictions.txt")

