import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import argparse
import os
import json
from sklearn.model_selection import train_test_split, KFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns
# from scipy import stats
import pandas as pd
import sys
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)

import warnings
warnings.filterwarnings('ignore')

class LadderNetwork(nn.Module):
    """
    Multi-classification tasks for semi-supervised learning
    """
    def __init__(self, input_dim, hidden_dims, num_classes, dropout_rate=0.1):
        super(LadderNetwork, self).__init__()
        
        self.input_dim = input_dim
        self.num_classes = num_classes
        
        # encoder
        encoder_layers = []
        prev_dim = input_dim
        for hidden_dim in hidden_dims:
            encoder_layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim
        
        self.encoder = nn.Sequential(*encoder_layers)
        
        # decoder
        decoder_layers = []
        decoder_dims = list(reversed(hidden_dims))
        
        for i, hidden_dim in enumerate(decoder_dims):
            decoder_layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            ])
            prev_dim = hidden_dim
        
        # final output layer
        decoder_layers.append(nn.Linear(prev_dim, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)
        
        # classifier
        self.classifier = nn.Linear(hidden_dims[-1], num_classes)
        
        # noise layer (for semi-supervised learning)
        self.noise_layers = nn.ModuleList([
            nn.Linear(hidden_dims[i], hidden_dims[i]) for i in range(len(hidden_dims))
        ])
    
    def forward(self, x, add_noise=False):
        """forward propagation"""
        # encoder
        encoded = self.encoder(x)
        
        # add noise (if enabled)
        if add_noise:
            noise = torch.randn_like(encoded) * 0.1
            encoded = encoded + noise
        
        # classifier
        logits = self.classifier(encoded)
        
        # decoder
        decoded = self.decoder(encoded)
        
        return logits, decoded, [encoded]
    
    def decode(self, h, encoded_features):
        return self.decoder(h)

class SemiSupervisedLoss(nn.Module):
    """
    Semi-supervised learning loss function
    Combine supervised loss and reconstruction loss
    """
    def __init__(self, alpha=1.0, beta=1.0, gamma=0.1, reduction='mean'):
        super(SemiSupervisedLoss, self).__init__()
        self.alpha = alpha  # supervised loss weight
        self.beta = beta    # reconstruction loss weight
        self.gamma = gamma  # regularization loss weight
        self.reduction = reduction
    
    def forward(self, logits, targets, reconstructed, original, encoded_features):
        # supervised loss (cross entropy)
        if targets is not None:
            # supervised_loss = F.cross_entropy(logits, targets, reduction=self.reduction)
            # Separate labeled and unlabeled data
            labeled_mask = targets != -1  # -1 means unlabeled
            if labeled_mask.sum() > 0:  # there are labeled data
                labeled_logits = logits[labeled_mask]
                labeled_targets = targets[labeled_mask]
                supervised_loss = F.cross_entropy(labeled_logits, labeled_targets, reduction=self.reduction)
            else:
                supervised_loss = torch.tensor(0.0, device=logits.device)
        else:
            supervised_loss = torch.tensor(0.0, device=logits.device)
        
        # reconstruction loss (MSE)
        reconstruction_loss = F.mse_loss(reconstructed, original, reduction=self.reduction)
        
        # regularization loss (L2)
        l2_reg = 0
        for features in encoded_features:
            l2_reg += torch.norm(features, p=2)
        regularization_loss = l2_reg / len(encoded_features)
        
        total_loss = (self.alpha * supervised_loss + 
                     self.beta * reconstruction_loss + 
                     self.gamma * regularization_loss)
        
        return total_loss, supervised_loss, reconstruction_loss, regularization_loss

class FocalLoss(nn.Module):
    """
    Focal Loss for multi-class classification
    """
    def __init__(self, alpha=1.0, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # ce_loss = F.cross_entropy(inputs, targets, reduction='none')
        # pt = torch.exp(-ce_loss)
        # focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
        
        # if self.reduction == 'mean':
        #     return focal_loss.mean()
        # elif self.reduction == 'sum':
        #     return focal_loss.sum()
        # else:
        #     return focal_loss

        # Separate labeled and unlabeled data
        # 修改 一做kfold就报错 所以修改这里
        labeled_mask = targets != -1  # -1 means unlabeled
        if labeled_mask.sum() > 0:  # there are labeled data
            labeled_inputs = inputs[labeled_mask]
            labeled_targets = targets[labeled_mask]
            ce_loss = F.cross_entropy(labeled_inputs, labeled_targets, reduction='none')
            pt = torch.exp(-ce_loss)
            focal_loss = self.alpha * (1 - pt) ** self.gamma * ce_loss
            
            if self.reduction == 'mean':
                return focal_loss.mean()
            elif self.reduction == 'sum':
                return focal_loss.sum()
            else:
                return focal_loss
        else:
            return torch.tensor(0.0, device=inputs.device)

class LabelSmoothingLoss(nn.Module):
    """
    Label Smoothing Loss
    """
    def __init__(self, num_classes, smoothing=0.1, reduction='mean'):
        super(LabelSmoothingLoss, self).__init__()
        self.num_classes = num_classes
        self.smoothing = smoothing
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # log_preds = F.log_softmax(inputs, dim=1)
        # true_dist = torch.zeros_like(log_preds)
        # true_dist.fill_(self.smoothing / (self.num_classes - 1))
        # true_dist.scatter_(1, targets.unsqueeze(1), 1 - self.smoothing)
        
        # loss = -torch.sum(true_dist * log_preds, dim=1)
        
        # if self.reduction == 'mean':
        #     return loss.mean()
        # elif self.reduction == 'sum':
        #     return loss.sum()
        # else:
        #     return loss
        # Separate labeled and unlabeled data
        # 修改
        labeled_mask = targets != -1  # -1 means unlabeled
        if labeled_mask.sum() > 0:  # there are labeled data
            labeled_inputs = inputs[labeled_mask]
            labeled_targets = targets[labeled_mask]
            
            log_preds = F.log_softmax(labeled_inputs, dim=1)
            true_dist = torch.zeros_like(log_preds)
            true_dist.fill_(self.smoothing / (self.num_classes - 1))
            true_dist.scatter_(1, labeled_targets.unsqueeze(1), 1 - self.smoothing)
            
            loss = -torch.sum(true_dist * log_preds, dim=1)
            
            if self.reduction == 'mean':
                return loss.mean()
            elif self.reduction == 'sum':
                return loss.sum()
            else:
                return loss
        else:
            return torch.tensor(0.0, device=inputs.device)

class ContrastiveLoss(nn.Module):
    """
    Contrastive Loss for semi-supervised learning
    """
    def __init__(self, margin=1.0, temperature=0.1, reduction='mean'):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
        self.temperature = temperature
        self.reduction = reduction
    
    def forward(self, features, labels):
        # # calculate similarity matrix
        # features_norm = F.normalize(features, p=2, dim=1)
        # similarity_matrix = torch.mm(features_norm, features_norm.t()) / self.temperature
        
        # # create positive sample mask
        # labels_equal = labels.unsqueeze(0) == labels.unsqueeze(1)
        
        # # calculate contrastive loss
        # exp_sim = torch.exp(similarity_matrix)
        # pos_sim = exp_sim * labels_equal.float()
        # neg_sim = exp_sim * (1 - labels_equal.float())
        
        # pos_sum = pos_sim.sum(dim=1, keepdim=True)
        # neg_sum = neg_sim.sum(dim=1, keepdim=True)
        
        # loss = -torch.log(pos_sum / (pos_sum + neg_sum + 1e-8))
        
        # if self.reduction == 'mean':
        #     return loss.mean()
        # elif self.reduction == 'sum':
        #     return loss.sum()
        # else:
        #     return loss
        # Separate labeled and unlabeled data
        # 修改
        labeled_mask = labels != -1  # -1 means unlabeled
        if labeled_mask.sum() > 0:  # there are labeled data
            labeled_features = features[labeled_mask]
            labeled_labels = labels[labeled_mask]
            
            # calculate similarity matrix
            features_norm = F.normalize(labeled_features, p=2, dim=1)
            similarity_matrix = torch.mm(features_norm, features_norm.t()) / self.temperature
            
            # create positive sample mask
            labels_equal = labeled_labels.unsqueeze(0) == labeled_labels.unsqueeze(1)
            
            # calculate contrastive loss
            exp_sim = torch.exp(similarity_matrix)
            pos_sim = exp_sim * labels_equal.float()
            neg_sim = exp_sim * (1 - labels_equal.float())
            
            pos_sum = pos_sim.sum(dim=1, keepdim=True)
            neg_sum = neg_sim.sum(dim=1, keepdim=True)
            
            loss = -torch.log(pos_sum / (pos_sum + neg_sum + 1e-8))
            
            if self.reduction == 'mean':
                return loss.mean()
            elif self.reduction == 'sum':
                return loss.sum()
            else:
                return loss
        else:
            return torch.tensor(0.0, device=features.device)

class ModelEvaluator:
    """
    Semi-supervised learning model evaluator
    """
    def __init__(self, device):
        self.device = device
        self.metrics = {}
    
    def evaluate_classification(self, model, data_loader, scaler):
        """
        Evaluate classification performance
        """
        model.eval()
        all_predictions = []
        all_targets = []
        all_probabilities = []
        
        with torch.no_grad():
            for data, targets in data_loader:
                data = data.to(self.device)
                targets = targets.to(self.device)
                
                logits, _, _ = model(data)
                probabilities = F.softmax(logits, dim=1)
                predictions = torch.argmax(logits, dim=1)
                
                all_predictions.extend(predictions.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())
        
        all_predictions = np.array(all_predictions)
        all_targets = np.array(all_targets)
        all_probabilities = np.array(all_probabilities)
        
        # calculate classification metrics
        accuracy = accuracy_score(all_targets, all_predictions)
        precision = precision_score(all_targets, all_predictions, average='weighted')
        recall = recall_score(all_targets, all_predictions, average='weighted')
        f1 = f1_score(all_targets, all_predictions, average='weighted')
        
        # calculate each class metrics
        precision_per_class = precision_score(all_targets, all_predictions, average=None)
        recall_per_class = recall_score(all_targets, all_predictions, average=None)
        f1_per_class = f1_score(all_targets, all_predictions, average=None)
        
        # calculate confusion matrix
        cm = confusion_matrix(all_targets, all_predictions)
        
        classification_metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'precision_per_class': precision_per_class,
            'recall_per_class': recall_per_class,
            'f1_per_class': f1_per_class,
            'confusion_matrix': cm,
            'predictions': all_predictions,
            'targets': all_targets,
            'probabilities': all_probabilities
        }
        
        return classification_metrics
    
    def evaluate_reconstruction(self, model, data_loader, scaler):
        """
        Evaluate reconstruction performance
        """
        model.eval()
        all_original = []
        all_reconstructed = []
        
        with torch.no_grad():
            for data, _ in data_loader:
                data = data.to(self.device)
                _, reconstructed, _ = model(data)
                
                all_original.append(data.cpu().numpy())
                all_reconstructed.append(reconstructed.cpu().numpy())
        
        original = np.vstack(all_original)
        reconstructed = np.vstack(all_reconstructed)
        
        # unstandardize
        original_unscaled = scaler.inverse_transform(original)
        reconstructed_unscaled = scaler.inverse_transform(reconstructed)
        
        # calculate reconstruction metrics
        mse = np.mean((original_unscaled - reconstructed_unscaled) ** 2)
        mae = np.mean(np.abs(original_unscaled - reconstructed_unscaled))
        
        # calculate correlation coefficient
        correlation = np.corrcoef(original_unscaled.flatten(), reconstructed_unscaled.flatten())[0, 1]
        
        reconstruction_metrics = {
            'mse': mse,
            'mae': mae,
            'correlation': correlation,
            'original_data': original_unscaled,
            'reconstructed_data': reconstructed_unscaled
        }
        
        return reconstruction_metrics
    
    def compute_comprehensive_metrics(self, model, data_loader, scaler):
        """
        Calculate comprehensive evaluation metrics
        """
        print("Start comprehensive model evaluation...")
        
        # evaluate classification performance
        print("Evaluate classification performance...")
        classification_metrics = self.evaluate_classification(model, data_loader, scaler)
        
        # evaluate reconstruction performance
        print("Evaluate reconstruction performance...")
        reconstruction_metrics = self.evaluate_reconstruction(model, data_loader, scaler)
                
        comprehensive_metrics = {
            'classification': classification_metrics,
            'reconstruction': reconstruction_metrics
        }
        
        return comprehensive_metrics
 
def visualize_results(metrics, save_path=None):
    """
    Visualize evaluation results
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle('Ladder network semi-supervised learning evaluation results', fontsize=16, fontweight='bold')
    
    # 1. confusion matrix
    ax1 = axes[0, 0]
    cm = metrics['classification']['confusion_matrix']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1)
    ax1.set_title(f'Confusion matrix (accuracy: {metrics["classification"]["accuracy"]:.3f})')
    ax1.set_xlabel('Predicted labels')
    ax1.set_ylabel('True labels')
    
    # 2. classification performance metrics
    ax2 = axes[0, 1]
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1 score']
    metrics_values = [
        metrics['classification']['accuracy'],
        metrics['classification']['precision'],
        metrics['classification']['recall'],
        metrics['classification']['f1_score']
    ]
    bars = ax2.bar(metrics_names, metrics_values, color=['skyblue', 'lightcoral', 'lightgreen', 'gold'])
    ax2.set_ylabel('Scores')
    ax2.set_title('Classification performance metrics')
    ax2.set_ylim(0, 1)
    
    # add numerical labels
    for bar, value in zip(bars, metrics_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. reconstruction quality scatter plot
    ax3 = axes[1, 0]
    original = metrics['reconstruction']['original_data'].flatten()
    reconstructed = metrics['reconstruction']['reconstructed_data'].flatten()
    
    # random sampling 1000 points for visualization
    if len(original) > 1000:
        indices = np.random.choice(len(original), 1000, replace=False)
        original_sample = original[indices]
        reconstructed_sample = reconstructed[indices]
    else:
        original_sample = original
        reconstructed_sample = reconstructed
    
    ax3.scatter(original_sample, reconstructed_sample, alpha=0.5, s=1)
    ax3.plot([original_sample.min(), original_sample.max()], 
             [original_sample.min(), original_sample.max()], 'r--', lw=2)
    ax3.set_xlabel('Original data')
    ax3.set_ylabel('Reconstructed data')
    ax3.set_title(f'Reconstruction quality (correlation: {metrics["reconstruction"]["correlation"]:.3f})')
    ax3.grid(True, alpha=0.3)
    
    # # 4. 各类别F1分数
    # ax4 = axes[1, 0]
    # f1_per_class = metrics['classification']['f1_per_class']
    # class_names = [f'类别{i}' for i in range(len(f1_per_class))]
    # bars = ax4.bar(class_names, f1_per_class, color='lightblue')
    # ax4.set_ylabel('F1分数')
    # ax4.set_title('各类别F1分数')
    # ax4.set_ylim(0, 1)
    # ax4.tick_params(axis='x', rotation=45)
    
    # # 添加数值标签
    # for bar, value in zip(bars, f1_per_class):
    #     height = bar.get_height()
    #     ax4.text(bar.get_x() + bar.get_width()/2., height + 0.01,
    #             f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 5. 重构误差分布
    ax5 = axes[1, 1]
    reconstruction_error = np.abs(original - reconstructed)
    ax5.hist(reconstruction_error, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    ax5.set_xlabel('Reconstruction error')
    ax5.set_ylabel('Frequency')
    ax5.set_title(f'Reconstruction error distribution (MSE: {metrics["reconstruction"]["mse"]:.3f})')
    ax5.grid(True, alpha=0.3)
    
    # # 6. 综合评分
    # ax6 = axes[1, 2]
    # scores = [
    #     metrics['overall_score']['classification_score'],
    #     metrics['overall_score']['reconstruction_score']
    # ]
    # labels = ['分类质量', '重构质量']
    # colors = ['skyblue', 'lightcoral']
    
    # bars = ax6.bar(labels, scores, color=colors, alpha=0.7, edgecolor='black')
    # ax6.set_ylabel('评分')
    # ax6.set_title(f'综合评分: {metrics["overall_score"]["total_score"]}/100')
    # ax6.set_ylim(0, 80)
    
    # # 添加数值标签
    # for bar, score in zip(bars, scores):
    #     height = bar.get_height()
    #     ax6.text(bar.get_x() + bar.get_width()/2., height + 1,
    #             f'{score}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    # plt.show()
    plt.close()

def print_evaluation_report(metrics):
    print("\n" + "="*60)
    print("Ladder network semi-supervised learning evaluation report")
    print("="*60)
    
    # classification performance
    print("\n Classification performance evaluation:")
    print("-" * 30)
    print(f"Accuracy: {metrics['classification']['accuracy']:.6f}")
    print(f"Precision: {metrics['classification']['precision']:.6f}")
    print(f"Recall: {metrics['classification']['recall']:.6f}")
    print(f"F1 Score: {metrics['classification']['f1_score']:.6f}")
    
    print("\n Detailed metrics for each class:")
    print("-" * 30)
    for i, (precision, recall, f1) in enumerate(zip(
        metrics['classification']['precision_per_class'],
        metrics['classification']['recall_per_class'],
        metrics['classification']['f1_per_class']
    )):
        print(f"Class {i}: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
    
    # reconstruction performance
    print("\n Reconstruction performance evaluation:")
    print("-" * 30)
    print(f"MSE: {metrics['reconstruction']['mse']:.6f}")
    print(f"MAE: {metrics['reconstruction']['mae']:.6f}")
    print(f"Correlation: {metrics['reconstruction']['correlation']:.6f}")
    
    # # 综合评分
    # print("\n Comprehensive score:")
    # print("-" * 30)
    # print(f"Classification score: {metrics['overall_score']['classification_score']}/70")
    # print(f"Reconstruction score: {metrics['overall_score']['reconstruction_score']}/30")
    # print(f"Total score: {metrics['overall_score']['total_score']}/100")
    # print(f"评分百分比: {metrics['overall_score']['score_percentage']:.1f}%")
    
    # # 模型等级评定
    # score_pct = metrics['overall_score']['score_percentage']
    # if score_pct >= 90:
    #     grade = "优秀 (A+)"
    # elif score_pct >= 80:
    #     grade = "良好 (A)"
    # elif score_pct >= 70:
    #     grade = "中等 (B)"
    # elif score_pct >= 60:
    #     grade = "及格 (C)"
    # else:
    #     grade = "需要改进 (D)"
    
    # print(f"模型等级: {grade}")
    # print("="*60)

class EarlyStopping:
    def __init__(self, patience=7, min_delta=0, restore_best_weights=True):
        self.patience = patience
        self.min_delta = min_delta
        self.restore_best_weights = restore_best_weights
        self.best_loss = None
        self.counter = 0
        self.best_weights = None
        
    def __call__(self, val_loss, model):
        if self.best_loss is None:
            self.best_loss = val_loss
            self.save_checkpoint(model)
        elif val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            self.save_checkpoint(model)
        else:
            self.counter += 1
            
        if self.counter >= self.patience:
            if self.restore_best_weights:
                model.load_state_dict(self.best_weights)
            return True
        return False
    
    def save_checkpoint(self, model):
        """Save best model weights"""
        self.best_weights = model.state_dict().copy()

def set_random_seed(seed):
    """Set random seed to ensure reproducibility"""
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.Generator().manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def prepare_data(seed, batch_size, ratio="8:1:1", jobID="20240808232043_OtJF37SH", use_unlabeled=True, kfold=0):
    """
    准备训练、验证和测试数据
    第一列是样本名称，最后一列是标签
    支持半监督学习：使用无标签数据
    训练集有无标签样本（无标签标为Unknown），验证集和测试集必须有标签
    """
    if ratio == "0" and kfold == 0:
        scaler = StandardScaler()
        label_encoder = LabelEncoder()
        
        # 直接加载训练-验证-测试集文件
        train_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")   # the path of training dataset

        train_data = train_data.dropna()
        train_features = train_data.iloc[:, 1:-1].values.astype(float)  # 中间列是特征
        train_labels = train_data.iloc[:, -1].values  # 最后一列是标签
        
        # 分离有标签和无标签数据
        labeled_mask = train_labels != 'Unknown'
        unlabeled_mask = train_labels == 'Unknown'
        
        labeled_features = train_features[labeled_mask]
        labeled_labels = train_labels[labeled_mask]
        unlabeled_features = train_features[unlabeled_mask]
        
        # 编码标签
        labeled_labels_encoded = label_encoder.fit_transform(labeled_labels)
        
        # 标准化特征
        scaler.fit(labeled_features)  # 只使用有标签数据拟合scaler
        labeled_features_scaled = scaler.transform(labeled_features)
        unlabeled_features_scaled = scaler.transform(unlabeled_features)
        
        # 创建有标签数据加载器
        labeled_data_tensor = torch.FloatTensor(labeled_features_scaled)
        labeled_labels_tensor = torch.LongTensor(labeled_labels_encoded)
        labeled_loader = DataLoader(TensorDataset(labeled_data_tensor, labeled_labels_tensor), 
                                  batch_size=batch_size, shuffle=True)
        
        # 创建无标签数据加载器（用于重构任务）
        unlabeled_data_tensor = torch.FloatTensor(unlabeled_features_scaled)
        unlabeled_loader = DataLoader(TensorDataset(unlabeled_data_tensor), 
                                    batch_size=batch_size, shuffle=True)
        
        # 合并有标签和无标签数据用于训练
        if use_unlabeled and len(unlabeled_features) > 0:
            # 创建半监督训练数据加载器
            all_features = np.vstack([labeled_features_scaled, unlabeled_features_scaled])
            all_labels = np.concatenate([labeled_labels_encoded, 
                                       np.full(len(unlabeled_features), -1)])  # -1表示无标签
            
            all_data_tensor = torch.FloatTensor(all_features)
            all_labels_tensor = torch.LongTensor(all_labels)
            train_loader = DataLoader(TensorDataset(all_data_tensor, all_labels_tensor), 
                                    batch_size=batch_size, shuffle=True)
        else:
            train_loader = labeled_loader
        
        # 验证和测试数据
        # val_data = pd.read_csv(f"./train_example/{jobid}_val.txt", sep="\t")
        val_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_val.txt", sep="\t")
        val_data = val_data.dropna()
        val_features = val_data.iloc[:, 1:-1].values.astype(float)
        val_labels = val_data.iloc[:, -1].values
        
        # 处理验证集标签 - 确保标签格式一致
        try:
            # 尝试使用label_encoder转换
            val_labels_str = val_labels.astype(str)  # test
            val_labels_encoded = label_encoder.transform(val_labels_str)
            # val_labels_encoded = label_encoder.transform(val_labels)
        except ValueError as e:
            # 如果转换失败，说明标签格式不匹配
            # print(f"警告：验证集标签格式不匹配，尝试直接转换: {e}")
            # 将数字标签转换为字符串，然后重新拟合label_encoder
            # val_labels_str = val_labels.astype(str) # test
            # 重新拟合label_encoder以包含所有标签
            all_labels = np.concatenate([labeled_labels, val_labels_str])
            label_encoder.fit(all_labels)
            val_labels_encoded = label_encoder.transform(val_labels_str)
        
        val_features_scaled = scaler.transform(val_features)
        val_data_tensor = torch.FloatTensor(val_features_scaled)
        val_labels_tensor = torch.LongTensor(val_labels_encoded)
        val_loader = DataLoader(TensorDataset(val_data_tensor, val_labels_tensor), 
                              batch_size=batch_size, shuffle=False)

        # test_data = pd.read_csv(f"./train_example/{jobid}_test.txt", sep="\t")
        test_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t")
        test_data = test_data.dropna()
        test_features = test_data.iloc[:, 1:-1].values.astype(float)
        test_labels = test_data.iloc[:, -1].values
        
        # 处理测试集标签 - 确保标签格式一致
        try:
            # 尝试使用label_encoder转换
            test_labels_str = test_labels.astype(str)
            test_labels_encoded = label_encoder.transform(test_labels_str)
            # test_labels_encoded = label_encoder.transform(test_labels) # test
        except ValueError as e:
            # 如果转换失败，说明标签格式不匹配
            # print(f"警告：测试集标签格式不匹配，尝试直接转换: {e}")
            # 将数字标签转换为字符串，然后重新拟合label_encoder
            # test_labels_str = test_labels.astype(str)   # test
            # 重新拟合label_encoder以包含所有标签
            all_labels = np.concatenate([labeled_labels, test_labels_str])
            label_encoder.fit(all_labels)
            test_labels_encoded = label_encoder.transform(test_labels_str)
        
        test_features_scaled = scaler.transform(test_features)
        test_data_tensor = torch.FloatTensor(test_features_scaled)
        test_labels_tensor = torch.LongTensor(test_labels_encoded)
        test_loader = DataLoader(TensorDataset(test_data_tensor, test_labels_tensor), 
                               batch_size=batch_size, shuffle=False)
        
        input_dim = train_features.shape[1]
    elif ratio != "0" and kfold == 0:
        # 分割训练-验证-测试集
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")
        data = data.dropna()
        # sample_names = data.iloc[:, 0].values  # 第一列是样本名称
        features = data.iloc[:, 1:-1].values.astype(float)  # 中间列是特征
        labels = data.iloc[:, -1].values  # 最后一列是标签
        
        scaler = StandardScaler()
        label_encoder = LabelEncoder()
        
        # 分离有标签和无标签数据
        labeled_mask = labels != 'Unknown'
        unlabeled_mask = labels == 'Unknown'
        
        labeled_features = features[labeled_mask]
        labeled_labels = labels[labeled_mask]
        unlabeled_features = features[unlabeled_mask]
        
        # 编码标签
        labeled_labels_encoded = label_encoder.fit_transform(labeled_labels)
        
        # 标准化特征
        scaler.fit(labeled_features)  # 只使用有标签数据拟合scaler
        labeled_features_scaled = scaler.transform(labeled_features)
        unlabeled_features_scaled = scaler.transform(unlabeled_features)
        
        # 分割有标签数据
        ratio_str = ratio.split(":")
        ratio_num = list(map(int, ratio_str))
        train_ratio = ratio_num[0] / sum(ratio_num)
        test_ratio = ratio_num[2] / sum(ratio_num[1:])

        # train_features, res_features, train_labels, res_labels = train_test_split(
        #     labeled_features_scaled, labeled_labels_encoded, test_size=1-train_ratio, 
        #     random_state=seed, stratify=labeled_labels_encoded
        # )
        # val_features, test_features, val_labels, test_labels = train_test_split(
        #     res_features, res_labels, test_size=test_ratio, random_state=seed, stratify=res_labels
        # )
        
        # 检查数据量是否足够进行分层抽样
        unique_labels, label_counts = np.unique(labeled_labels_encoded, return_counts=True)
        min_class_count = np.min(label_counts)
        
        if min_class_count < 2:
            # print(f"警告：某些类别样本数量过少（最少{min_class_count}个），将使用随机分割而非分层抽样")  
            print(f"Warning: If the sample size of certain categories is too small (at least {min_class_count}), random segmentation will be used instead of stratified sampling")  
            stratify_train = None
            stratify_val = None
        else:
            stratify_train = labeled_labels_encoded
            stratify_val = None
        
        train_features, res_features, train_labels, res_labels = train_test_split(
            labeled_features_scaled, labeled_labels_encoded, test_size=1-train_ratio, 
            random_state=seed, stratify=stratify_train
        )
        
        # 检查验证集分割时是否需要分层抽样
        if len(res_labels) > 0:
            unique_res_labels, res_label_counts = np.unique(res_labels, return_counts=True)
            min_res_class_count = np.min(res_label_counts)
            
            if min_res_class_count < 2:
                # print(f"警告：验证集分割时某些类别样本数量过少（最少{min_res_class_count}个），将使用随机分割")
                print(f"Warning: If the sample size of certain categories is too small (at least {min_res_class_count}) during validation set segmentation, random segmentation will be used")
                stratify_val = None
            else:
                stratify_val = res_labels
        else:
            stratify_val = None
        
        val_features, test_features, val_labels, test_labels = train_test_split(
            res_features, res_labels, test_size=test_ratio, random_state=seed, stratify=stratify_val
        )

        
        
        # 创建训练数据加载器（包含无标签数据）
        if use_unlabeled and len(unlabeled_features) > 0:
            # 将无标签数据添加到训练集中
            all_train_features = np.vstack([train_features, unlabeled_features_scaled])
            all_train_labels = np.concatenate([train_labels, np.full(len(unlabeled_features), -1)])
            
            train_data_tensor = torch.FloatTensor(all_train_features)
            train_labels_tensor = torch.LongTensor(all_train_labels)
        else:
            train_data_tensor = torch.FloatTensor(train_features)
            train_labels_tensor = torch.LongTensor(train_labels)
        
        train_loader = DataLoader(TensorDataset(train_data_tensor, train_labels_tensor), 
                                batch_size=batch_size, shuffle=True)
        
        val_data_tensor = torch.FloatTensor(val_features)
        val_labels_tensor = torch.LongTensor(val_labels)
        val_loader = DataLoader(TensorDataset(val_data_tensor, val_labels_tensor), 
                              batch_size=batch_size, shuffle=False)
        
        test_data_tensor = torch.FloatTensor(test_features)
        test_labels_tensor = torch.LongTensor(test_labels)
        test_loader = DataLoader(TensorDataset(test_data_tensor, test_labels_tensor), 
                               batch_size=batch_size, shuffle=False)
        
        input_dim = features.shape[1]
        
    else:  # 修改
        # kfold training
        scaler = StandardScaler()
        label_encoder = LabelEncoder()
        
        # Directly load training-validation-test set file
        train_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")
        train_data = train_data.dropna()
        train_features = train_data.iloc[:, 1:-1].values.astype(float)  # the middle columns are features
        train_labels = train_data.iloc[:, -1].values  # the last column is label
        
        # Separate labeled and unlabeled data
        labeled_mask = train_labels != 'Unknown'
        unlabeled_mask = train_labels == 'Unknown'
        
        labeled_features = train_features[labeled_mask]
        labeled_labels = train_labels[labeled_mask]
        unlabeled_features = train_features[unlabeled_mask]
        
        # Encode labels
        labeled_labels_encoded = label_encoder.fit_transform(labeled_labels)
        
        # Standardize features
        scaler.fit(labeled_features)  # Only use labeled data to fit scaler
        labeled_features_scaled = scaler.transform(labeled_features)
        unlabeled_features_scaled = scaler.transform(unlabeled_features)
        
        # Create labeled data loader
        labeled_data_tensor = torch.FloatTensor(labeled_features_scaled)
        labeled_labels_tensor = torch.LongTensor(labeled_labels_encoded)
        labeled_loader = DataLoader(TensorDataset(labeled_data_tensor, labeled_labels_tensor), 
                                  batch_size=batch_size, shuffle=True)
        
        # Create unlabeled data loader (for reconstruction task)
        unlabeled_data_tensor = torch.FloatTensor(unlabeled_features_scaled)
        unlabeled_loader = DataLoader(TensorDataset(unlabeled_data_tensor), 
                                    batch_size=batch_size, shuffle=True)
        
        # Merge labeled and unlabeled data for training
        if use_unlabeled and len(unlabeled_features) > 0:
            # Create semi-supervised training data loader
            all_features = np.vstack([labeled_features_scaled, unlabeled_features_scaled])
            all_labels = np.concatenate([labeled_labels_encoded, 
                                       np.full(len(unlabeled_features), -1)])
            
            all_data_tensor = torch.FloatTensor(all_features)
            all_labels_tensor = torch.LongTensor(all_labels)
            train_loader = DataLoader(TensorDataset(all_data_tensor, all_labels_tensor), 
                                    batch_size=batch_size, shuffle=True)
        else:
            train_loader = labeled_loader
        val_loader = 0
        # test_data = pd.read_csv(f"./train_example/{jobid}_test.txt", sep="\t")
        test_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t")
        test_data = test_data.dropna()
        test_features = test_data.iloc[:, 1:-1].values.astype(float)
        test_labels = test_data.iloc[:, -1].values
        
        # Process test set labels - ensure label format consistency
        try:
            # Try using label_encoder to convert
            test_labels_str = test_labels.astype(str)  # test
            test_labels_encoded = label_encoder.transform(test_labels_str)
            # test_labels_encoded = label_encoder.transform(test_labels)  # test
        except ValueError as e:
            # If conversion fails, it means the label format does not match
            # Convert numeric labels to strings, then refit label_encoder
            # test_labels_str = test_labels.astype(str)  # test
            # Refit label_encoder to include all labels
            all_labels = np.concatenate([labeled_labels, test_labels_str])
            label_encoder.fit(all_labels)
            test_labels_encoded = label_encoder.transform(test_labels_str)
        
        test_features_scaled = scaler.transform(test_features)
        test_data_tensor = torch.FloatTensor(test_features_scaled)
        test_labels_tensor = torch.LongTensor(test_labels_encoded)
        test_loader = DataLoader(TensorDataset(test_data_tensor, test_labels_tensor), 
                               batch_size=batch_size, shuffle=False)
        
        input_dim = train_features.shape[1]


    num_classes = len(np.unique(labeled_labels_encoded))
    
    return input_dim, num_classes, train_loader, val_loader, test_loader, scaler

def train_epoch(model, train_loader, optimizer, device, loss_function='semi_supervised', 
                alpha=1.0, beta=1.0, gamma=0.1, add_noise=False):
    """训练一个epoch - 支持半监督学习"""
    model.train()
    total_loss = 0
    total_supervised_loss = 0
    total_reconstruction_loss = 0
    total_regularization_loss = 0
    
    for batch_idx, (data, targets) in enumerate(train_loader):
        data = data.to(device)
        targets = targets.to(device)
        optimizer.zero_grad()
        
        logits, reconstructed, encoded_features = model(data, add_noise=add_noise)
        
        # 分离有标签和无标签数据
        labeled_mask = targets != -1  # -1表示无标签
        unlabeled_mask = targets == -1
        
        if labeled_mask.sum() > 0:  # 有有标签数据
            labeled_data = data[labeled_mask]
            labeled_targets = targets[labeled_mask]
            labeled_logits = logits[labeled_mask]
            labeled_reconstructed = reconstructed[labeled_mask]
            labeled_encoded_features = [feat[labeled_mask] for feat in encoded_features]
        else:
            labeled_data = None
            labeled_targets = None
            labeled_logits = None
            labeled_reconstructed = None
            labeled_encoded_features = None
        
        if unlabeled_mask.sum() > 0:  # 有无标签数据
            unlabeled_data = data[unlabeled_mask]
            unlabeled_reconstructed = reconstructed[unlabeled_mask]
            unlabeled_encoded_features = [feat[unlabeled_mask] for feat in encoded_features]
        else:
            unlabeled_data = None
            unlabeled_reconstructed = None
            unlabeled_encoded_features = None
        
        # 计算损失
        if loss_function.lower() == 'semi_supervised':
            # 半监督损失：有标签数据计算监督损失，所有数据计算重构损失
            supervised_loss = torch.tensor(0.0, device=device)
            if labeled_data is not None:
                supervised_loss = F.cross_entropy(labeled_logits, labeled_targets)
            
            reconstruction_loss = F.mse_loss(reconstructed, data)
            
            regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
            
            loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            
        elif loss_function.lower() == 'focal':
            supervised_loss = torch.tensor(0.0, device=device)
            if labeled_data is not None:
                focal_loss_fn = FocalLoss(alpha=1.0, gamma=2.0)
                supervised_loss = focal_loss_fn(labeled_logits, labeled_targets)
            
            reconstruction_loss = F.mse_loss(reconstructed, data)
            regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
            loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            
        elif loss_function.lower() == 'label_smoothing':
            supervised_loss = torch.tensor(0.0, device=device)
            if labeled_data is not None:
                label_smooth_loss_fn = LabelSmoothingLoss(num_classes=model.num_classes, smoothing=0.1)
                supervised_loss = label_smooth_loss_fn(labeled_logits, labeled_targets)
            
            reconstruction_loss = F.mse_loss(reconstructed, data)
            regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
            loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            
        elif loss_function.lower() == 'contrastive':
            supervised_loss = torch.tensor(0.0, device=device)
            if labeled_data is not None:
                supervised_loss = F.cross_entropy(labeled_logits, labeled_targets)
                contrastive_loss_fn = ContrastiveLoss()
                contrastive_loss = contrastive_loss_fn(labeled_encoded_features[-1], labeled_targets)
            else:
                contrastive_loss = torch.tensor(0.0, device=device)
            
            reconstruction_loss = F.mse_loss(reconstructed, data)
            regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
            loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * contrastive_loss + 0.1 * regularization_loss
            
        else:
            # 默认使用半监督损失
            supervised_loss = torch.tensor(0.0, device=device)
            if labeled_data is not None:
                supervised_loss = F.cross_entropy(labeled_logits, labeled_targets)
            
            reconstruction_loss = F.mse_loss(reconstructed, data)
            regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
            loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        total_supervised_loss += supervised_loss.item()
        total_reconstruction_loss += reconstruction_loss.item()
        total_regularization_loss += regularization_loss.item()
    
    return (total_loss / len(train_loader), 
            total_supervised_loss / len(train_loader), 
            total_reconstruction_loss / len(train_loader), 
            total_regularization_loss / len(train_loader))

def validate_epoch(model, val_loader, device, loss_function='semi_supervised', 
                  alpha=1.0, beta=1.0, gamma=0.1):
    """验证一个epoch"""
    model.eval()
    total_loss = 0
    total_supervised_loss = 0
    total_reconstruction_loss = 0
    total_regularization_loss = 0
    
    with torch.no_grad():
        for data, targets in val_loader:
            data = data.to(device)
            targets = targets.to(device)
            
            logits, reconstructed, encoded_features = model(data)
            
            # 根据损失函数类型计算损失
            if loss_function.lower() == 'semi_supervised':
                loss_fn = SemiSupervisedLoss(alpha=alpha, beta=beta, gamma=gamma)
                loss, supervised_loss, reconstruction_loss, regularization_loss = loss_fn(
                    logits, targets, reconstructed, data, encoded_features
                )
            elif loss_function.lower() == 'focal':
                focal_loss_fn = FocalLoss(alpha=1.0, gamma=2.0)
                supervised_loss = focal_loss_fn(logits, targets)
                reconstruction_loss = F.mse_loss(reconstructed, data)
                regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
                loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            elif loss_function.lower() == 'label_smoothing':
                label_smooth_loss_fn = LabelSmoothingLoss(num_classes=model.num_classes, smoothing=0.1)
                supervised_loss = label_smooth_loss_fn(logits, targets)
                reconstruction_loss = F.mse_loss(reconstructed, data)
                regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
                loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            elif loss_function.lower() == 'contrastive':
                contrastive_loss_fn = ContrastiveLoss()
                supervised_loss = F.cross_entropy(logits, targets)
                reconstruction_loss = F.mse_loss(reconstructed, data)
                contrastive_loss = contrastive_loss_fn(encoded_features[-1], targets)
                regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
                loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * contrastive_loss + 0.1 * regularization_loss
            else:
                loss_fn = SemiSupervisedLoss(alpha=alpha, beta=beta, gamma=gamma)
                loss, supervised_loss, reconstruction_loss, regularization_loss = loss_fn(
                    logits, targets, reconstructed, data, encoded_features
                )
            
            total_loss += loss.item()
            total_supervised_loss += supervised_loss.item()
            total_reconstruction_loss += reconstruction_loss.item()
            total_regularization_loss += regularization_loss.item()
    
    return (total_loss / len(val_loader), 
            total_supervised_loss / len(val_loader), 
            total_reconstruction_loss / len(val_loader), 
            total_regularization_loss / len(val_loader))

def train_model(model, train_loader, val_loader, optimizer, device, epochs, patience, model_name, 
                loss_function='semi_supervised', alpha=1.0, beta=1.0, gamma=0.1, add_noise=False):
    """训练模型"""
    early_stopping = EarlyStopping(patience=patience)
    train_losses = []
    val_losses = []
    
    print(f"Start training model: {model_name}")
    print(f"Use loss function: {loss_function}")
    print(f"Supervised loss weight: {alpha}, Reconstruction loss weight: {beta}, Regularization weight: {gamma}")
    print("-" * 50)
    
    for epoch in range(epochs):
        train_loss, train_sup, train_recon, train_reg = train_epoch(
            model, train_loader, optimizer, device, loss_function, alpha, beta, gamma, add_noise
        )
        val_loss, val_sup, val_recon, val_reg = validate_epoch(
            model, val_loader, device, loss_function, alpha, beta, gamma
        )
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        print(f'Epoch {epoch+1}/{epochs}:')
        print(f'  train loss: {train_loss:.4f} (supervised: {train_sup:.4f}, reconstruction: {train_recon:.4f}, regularization: {train_reg:.4f})')
        print(f'  validation loss: {val_loss:.4f} (supervised: {val_sup:.4f}, reconstruction: {val_recon:.4f}, regularization: {val_reg:.4f})')
        
        if early_stopping(val_loss, model):
            print(f'Early stopping triggered, stopping training at epoch {epoch+1}')
            break
    
    return train_losses, val_losses

def test_model(model, test_loader, device, loss_function='semi_supervised', 
               alpha=1.0, beta=1.0, gamma=0.1):
    """测试模型"""
    model.eval()
    total_loss = 0
    total_supervised_loss = 0
    total_reconstruction_loss = 0
    total_regularization_loss = 0
    
    with torch.no_grad():
        for data, targets in test_loader:
            data = data.to(device)
            targets = targets.to(device)
            
            logits, reconstructed, encoded_features = model(data)
            
            # 根据损失函数类型计算损失
            if loss_function.lower() == 'semi_supervised':
                loss_fn = SemiSupervisedLoss(alpha=alpha, beta=beta, gamma=gamma)
                loss, supervised_loss, reconstruction_loss, regularization_loss = loss_fn(
                    logits, targets, reconstructed, data, encoded_features
                )
            elif loss_function.lower() == 'focal':
                focal_loss_fn = FocalLoss(alpha=1.0, gamma=2.0)
                supervised_loss = focal_loss_fn(logits, targets)
                reconstruction_loss = F.mse_loss(reconstructed, data)
                regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
                loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            elif loss_function.lower() == 'label_smoothing':
                label_smooth_loss_fn = LabelSmoothingLoss(num_classes=model.num_classes, smoothing=0.1)
                supervised_loss = label_smooth_loss_fn(logits, targets)
                reconstruction_loss = F.mse_loss(reconstructed, data)
                regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
                loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * regularization_loss
            elif loss_function.lower() == 'contrastive':
                contrastive_loss_fn = ContrastiveLoss()
                supervised_loss = F.cross_entropy(logits, targets)
                reconstruction_loss = F.mse_loss(reconstructed, data)
                contrastive_loss = contrastive_loss_fn(encoded_features[-1], targets)
                regularization_loss = sum(torch.norm(feat, p=2) for feat in encoded_features) / len(encoded_features)
                loss = alpha * supervised_loss + beta * reconstruction_loss + gamma * contrastive_loss + 0.1 * regularization_loss
            else:
                loss_fn = SemiSupervisedLoss(alpha=alpha, beta=beta, gamma=gamma)
                loss, supervised_loss, reconstruction_loss, regularization_loss = loss_fn(
                    logits, targets, reconstructed, data, encoded_features
                )
            
            total_loss += loss.item()
            total_supervised_loss += supervised_loss.item()
            total_reconstruction_loss += reconstruction_loss.item()
            total_regularization_loss += regularization_loss.item()
    
    avg_loss = total_loss / len(test_loader)
    avg_supervised_loss = total_supervised_loss / len(test_loader)
    avg_reconstruction_loss = total_reconstruction_loss / len(test_loader)
    avg_regularization_loss = total_regularization_loss / len(test_loader)
    
    print(f"Test results:")
    print(f"  Total loss: {avg_loss:.4f}")
    print(f"  Supervised loss: {avg_supervised_loss:.4f}")
    print(f"  Reconstruction loss: {avg_reconstruction_loss:.4f}")
    print(f"  Regularization loss: {avg_regularization_loss:.4f}")
    
    return avg_loss, avg_supervised_loss, avg_reconstruction_loss, avg_regularization_loss

def kfold_cross_validation(args, k_folds=5):
    """k-fold cross-validation"""
    print(f"\nStart {k_folds}-fold cross-validation")
    print("=" * 60)
    
    # 首先分割训练-测试集
    # print("First split training-test set...")
    input_dim, num_classes, train_loader, val_loader, test_loader, scaler = prepare_data(
        args.random_seed, args.batch_size, args.ratio, args.jobid, args.use_unlabeled, args.k_folds
    )
    
    # 获取训练数据用于k-fold
    train_data_list = []
    train_labels_list = []
    for data, labels in train_loader:
        train_data_list.append(data.numpy())
        train_labels_list.append(labels.numpy())
    train_data_scaled = np.vstack(train_data_list)
    train_labels_scaled = np.concatenate(train_labels_list)
    
    # 在训练数据上进行k-fold交叉验证
    kfold = KFold(n_splits=k_folds, shuffle=True, random_state=args.random_seed)
    fold_results = []
    
    for fold, (train_idx, val_idx) in enumerate(kfold.split(train_data_scaled)):
        print(f"\nFold {fold + 1}/{k_folds}")
        print("-" * 30)
        
        # 划分数据
        fold_train_data = torch.FloatTensor(train_data_scaled[train_idx])
        fold_train_labels = torch.LongTensor(train_labels_scaled[train_idx])
        fold_val_data = torch.FloatTensor(train_data_scaled[val_idx])
        fold_val_labels = torch.LongTensor(train_labels_scaled[val_idx])
        
        fold_train_loader = DataLoader(TensorDataset(fold_train_data, fold_train_labels), 
                                     batch_size=args.batch_size, shuffle=True)
        fold_val_loader = DataLoader(TensorDataset(fold_val_data, fold_val_labels), 
                                   batch_size=args.batch_size, shuffle=False)
        
        # 创建模型
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = LadderNetwork(
            input_dim=input_dim,
            hidden_dims=[512, 256, 128],
            num_classes=num_classes,
            dropout_rate=args.dropout
        ).to(device)
        
        # 创建优化器
        if args.optimizer_function.lower() == 'adam':
            optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
        elif args.optimizer_function.lower() == 'sgd':
            optimizer = optim.SGD(model.parameters(), lr=args.learning_rate, momentum=0.9)
        elif args.optimizer_function.lower() == 'adamw':
            optimizer = optim.AdamW(model.parameters(), lr=args.learning_rate)
        elif args.optimizer_function.lower() == 'rmsprop':
            optimizer = optim.RMSprop(model.parameters(), lr=args.learning_rate)
        else:
            optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
        
        # 训练模型
        train_losses, val_losses = train_model(
            model, fold_train_loader, fold_val_loader, optimizer, device, 
            args.epochs, args.early_stopping_patience, f"Fold_{fold+1}", 
            args.loss_function, args.alpha, args.beta, args.gamma, args.add_noise
        )
        
        # 在验证集上测试模型
        test_loss, test_sup, test_recon, test_reg = test_model(
            model, fold_val_loader, device, args.loss_function, args.alpha, args.beta, args.gamma
        )
        fold_results.append({
            'fold': fold + 1,
            'test_loss': test_loss,
            'test_supervised_loss': test_sup,
            'test_reconstruction_loss': test_recon,
            'test_regularization_loss': test_reg,
            'train_losses': train_losses,
            'val_losses': val_losses
        })
    
    # 计算平均结果
    avg_test_loss = np.mean([r['test_loss'] for r in fold_results])
    avg_test_sup = np.mean([r['test_supervised_loss'] for r in fold_results])
    avg_test_recon = np.mean([r['test_reconstruction_loss'] for r in fold_results])
    avg_test_reg = np.mean([r['test_regularization_loss'] for r in fold_results])
    
    print(f"\n{k_folds}-fold cross-validation results:")
    print("=" * 40)
    print(f"Validation loss: {avg_test_loss:.4f} ± {np.std([r['test_loss'] for r in fold_results]):.4f}")
    print(f"Supervised loss: {avg_test_sup:.4f} ± {np.std([r['test_supervised_loss'] for r in fold_results]):.4f}")
    print(f"Reconstruction loss: {avg_test_recon:.4f} ± {np.std([r['test_reconstruction_loss'] for r in fold_results]):.4f}")
    print(f"Regularization loss: {avg_test_reg:.4f} ± {np.std([r['test_regularization_loss'] for r in fold_results]):.4f}")
    
    return fold_results, model, scaler, test_loader, input_dim, num_classes

def save_model(model, scaler, args, model_path, scaler_path, input_dim, num_classes):
    """Save model and preprocessor"""
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_config': {
            'input_dim': input_dim,
            'hidden_dims': [512, 256, 128],
            'num_classes': num_classes,
            'dropout_rate': args.dropout
        },
        'args': vars(args)
    }, model_path)
    
    # Save scaler and label_encoder
    import pickle
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    
    # with open(label_encoder_path, 'wb') as f:
    #     pickle.dump(label_encoder, f)
    
    # print(f"模型已保存到: {model_path}")
    # print(f"预处理器已保存到: {scaler_path}")
    # print(f"标签编码器已保存到: {label_encoder_path}")

def load_model(model_path, scaler_path, device):
    """加载模型和预处理器"""
    # 加载模型
    checkpoint = torch.load(model_path, map_location=device)
    model_config = checkpoint['model_config']
    
    model = LadderNetwork(
        input_dim=model_config['input_dim'],
        hidden_dims=model_config['hidden_dims'],
        num_classes=model_config['num_classes'],
        dropout_rate=model_config['dropout_rate']
    ).to(device)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # 加载scaler和label_encoder
    import pickle
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    
    # with open(label_encoder_path, 'rb') as f:
    #     label_encoder = pickle.load(f)
    
    # print(f"模型已从 {model_path} 加载")
    # print(f"预处理器已从 {scaler_path} 加载")
    # print(f"标签编码器已从 {label_encoder_path} 加载")
    
    return model, scaler

def predict(model, scaler, data, device):
    """使用训练好的模型进行预测"""
    model.eval()
    
    # 数据预处理
    data_scaled = scaler.transform(data)
    data_tensor = torch.FloatTensor(data_scaled).to(device)
    
    with torch.no_grad():
        logits, reconstructed, encoded_features = model(data_tensor)
        probabilities = F.softmax(logits, dim=1)
        predictions = torch.argmax(logits, dim=1)
    
    return (predictions.cpu().numpy(), 
            probabilities.cpu().numpy(), 
            reconstructed.cpu().numpy(), 
            [feat.cpu().numpy() for feat in encoded_features])

def main():
    parser = argparse.ArgumentParser(description='梯形网络半监督学习训练脚本')

    # 数据路径
    parser.add_argument('--ratio', type=str, default='0', help='数据分割比例')
    parser.add_argument('--jobid', type=str, default='example_semi_supervised', help='数据集ID')
    
    # 模型参数
    parser.add_argument('--dropout', type=float, default=0.1, help='Dropout率')
    
    # 训练参数
    parser.add_argument('--epochs', type=int, default=10, help='训练轮数')
    parser.add_argument('--batch_size', type=int, default=32, help='批次大小')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='学习率')
    parser.add_argument('--early_stopping_patience', type=int, default=10, help='早停耐心值')
    
    # 损失函数参数
    parser.add_argument('--loss_function', type=str, default='semi_supervised', 
                       choices=['semi_supervised', 'focal', 'label_smoothing', 'contrastive'], 
                       help='损失函数类型:\n'
                            'semi_supervised: 半监督学习损失\n'
                            'focal: Focal损失\n'
                            'label_smoothing: 标签平滑损失\n'
                            'contrastive: 对比损失')
    parser.add_argument('--alpha', type=float, default=1.0, help='监督损失权重')
    parser.add_argument('--beta', type=float, default=1.0, help='重构损失权重')
    parser.add_argument('--gamma', type=float, default=0.1, help='正则化损失权重')
    parser.add_argument('--add_noise', action='store_true', default=0, help='是否添加噪声')  # 训练模型
    
    # 优化器
    parser.add_argument('--optimizer_function', type=str, default='adam', 
                       choices=['adam', 'sgd', 'adamw', 'rmsprop'], help='优化器类型')
    
    # 半监督学习参数
    parser.add_argument('--use_unlabeled', action='store_true', default=1, help='是否使用无标签数据进行半监督学习')
    # parser.add_argument('--unlabeled_ratio', type=float, default=0.5, help='无标签数据比例（0-1）')
    
    # 其他参数
    parser.add_argument('--random_seed', type=int, default=42, help='随机种子')
    parser.add_argument('--k_folds', type=int, default=0, help='k-fold折数')
    parser.add_argument('--save_model', action='store_true', default=1, help='是否保存模型')
    parser.add_argument('--model_path', type=str, default='ladder_model.pth', help='模型保存路径')
    parser.add_argument('--scaler_path', type=str, default='ladder_scaler.pkl', help='预处理器保存路径')
    # parser.add_argument('--label_encoder_path', type=str, default='ladder_label_encoder.pkl', help='标签编码器保存路径')
    
    # 评估相关参数
    parser.add_argument('--evaluate_model', action='store_true', default=1, help='是否进行模型评估')
    parser.add_argument('--save_evaluation', action='store_true', default=1, help='是否保存评估结果')
    parser.add_argument('--evaluation_path', type=str, default='results.png', help='评估结果保存路径')
    parser.add_argument('--show_plots', action='store_true', default=1, help='是否显示可视化图表')
    
    args = parser.parse_args()

    print("Ladder model")
    print('ratio =', args.ratio)
    print('k_folds =', args.k_folds)
    print('epochs =', args.epochs)
    print('batch_size =', args.batch_size)
    print('learning_rate =', args.learning_rate)
    print('early_stopping_patience =', args.early_stopping_patience)
    print('optimizer_function =', args.optimizer_function)
    print('loss_function =', args.loss_function)
    print('random_seed =', args.random_seed)
    print('alpha =', args.alpha)
    print('beta =', args.beta)
    print('gamma =', args.gamma)
    
    # 设置随机种子
    set_random_seed(args.random_seed)
    
    # 检查CUDA可用性
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if args.k_folds:
        # k-fold交叉验证
        fold_results, model, scaler, test_loader, input_dim, num_classes = kfold_cross_validation(args, args.k_folds)
    else:
        # 常规训练-验证-测试
        print("=" * 50)
        
        # 准备数据
        input_dim, num_classes, train_loader, val_loader, test_loader, scaler = prepare_data(
            args.random_seed, args.batch_size, args.ratio, args.jobid, args.use_unlabeled, args.k_folds
        )
        
        # 创建模型
        model = LadderNetwork(
            input_dim=input_dim,
            hidden_dims=[512, 256, 128],
            num_classes=num_classes,
            dropout_rate=args.dropout
        ).to(device)
        
        # 创建优化器
        if args.optimizer_function.lower() == 'adam':
            optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
        elif args.optimizer_function.lower() == 'sgd':
            optimizer = optim.SGD(model.parameters(), lr=args.learning_rate, momentum=0.9)
        elif args.optimizer_function.lower() == 'adamw':
            optimizer = optim.AdamW(model.parameters(), lr=args.learning_rate)
        elif args.optimizer_function.lower() == 'rmsprop':
            optimizer = optim.RMSprop(model.parameters(), lr=args.learning_rate)
        else:
            optimizer = optim.Adam(model.parameters(), lr=args.learning_rate)
        
        # 训练模型
        train_losses, val_losses = train_model(
            model, train_loader, val_loader, optimizer, device, 
            args.epochs, args.early_stopping_patience, "Ladder_Model", 
            loss_function=args.loss_function, alpha=args.alpha, beta=args.beta, 
            gamma=args.gamma, add_noise=args.add_noise
        )
        
        # 测试模型
        test_loss, test_sup, test_recon, test_reg = test_model(
            model, test_loader, device, loss_function=args.loss_function, 
            alpha=args.alpha, beta=args.beta, gamma=args.gamma
        )
    
    # 保存模型
    if args.save_model:
        save_model(model, scaler, args, args.model_path, 
                  args.scaler_path, input_dim, num_classes)
    
    # 模型评估
    if args.evaluate_model:
        print("\n" + "="*60)
        print("Start model evaluation")
        print("="*60)
        
        # 创建评估器
        evaluator = ModelEvaluator(device)
        
        # 进行综合评估
        metrics = evaluator.compute_comprehensive_metrics(model, test_loader, scaler)
        
        # 打印评估报告
        print_evaluation_report(metrics)
        
        # 可视化结果
        if args.show_plots:
            visualize_results(metrics, args.evaluation_path if args.save_evaluation else None)
        
        # 保存评估结果
        if args.save_evaluation:
            # 保存评估指标到JSON文件
            evaluation_data = {
                'classification_metrics': {
                    'accuracy': float(metrics['classification']['accuracy']),
                    'precision': float(metrics['classification']['precision']),
                    'recall': float(metrics['classification']['recall']),
                    'f1_score': float(metrics['classification']['f1_score']),
                    'precision_per_class': metrics['classification']['precision_per_class'].tolist(),
                    'recall_per_class': metrics['classification']['recall_per_class'].tolist(),
                    'f1_per_class': metrics['classification']['f1_per_class'].tolist()
                },
                'reconstruction_metrics': {
                    'mse': float(metrics['reconstruction']['mse']),
                    'mae': float(metrics['reconstruction']['mae']),
                    'correlation': float(metrics['reconstruction']['correlation'])
                }
            }
            
            json_path = args.evaluation_path.replace('.png', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # cmd: D:/Anaconda3/envs/pt37/python.exe f:/breeding/code/my_code/multi-omics/ladder.py --ratio 0 --jobid jobid
    # cmd: D:/Anaconda3/envs/pt37/python.exe f:/breeding/code/my_code/multi-omics/ladder.py --ratio 8:1:1 --k_folds 5 --jobid jobid
    # 输出：ladder_evaluation_results.json、ladder_evaluation_results.png、ladder_model.pth、ladder_scaler.pkl
    main()
