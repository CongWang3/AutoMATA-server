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

class PseudoLabelNetwork(nn.Module):
    """
    伪标签半监督学习网络
    用于多分类任务的半监督学习
    """
    def __init__(self, input_dim, hidden_dims, num_classes, dropout_rate=0.1):
        super(PseudoLabelNetwork, self).__init__()
        
        self.input_dim = input_dim
        self.num_classes = num_classes
        
        # 编码器
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
        
        # 分类器
        self.classifier = nn.Linear(prev_dim, num_classes)
        
        # 置信度阈值
        self.confidence_threshold = 0.8
    
    def forward(self, x):
        """前向传播"""
        encoded = self.encoder(x)
        logits = self.classifier(encoded)
        return logits
    
    def predict_with_confidence(self, x):
        """预测并返回置信度"""
        with torch.no_grad():
            logits = self.forward(x)
            probabilities = F.softmax(logits, dim=1)
            max_probs, predictions = torch.max(probabilities, dim=1)
            return predictions, max_probs, probabilities

class PseudoLabelLoss(nn.Module):
    """
    伪标签损失函数
    结合监督损失和伪标签损失
    """
    def __init__(self, alpha=1.0, beta=0.5, reduction='mean'):
        super(PseudoLabelLoss, self).__init__()
        self.alpha = alpha  # 监督损失权重
        self.beta = beta    # 伪标签损失权重
        self.reduction = reduction
    
    def forward(self, logits, targets, pseudo_targets, pseudo_weights):
        # 监督损失 - 只对有标签数据计算
        if targets is not None and len(targets) > 0:
            # 分离有标签和无标签数据
            labeled_mask = targets != -1  # -1表示无标签
            if labeled_mask.sum() > 0:  # 有有标签数据
                labeled_logits = logits[labeled_mask]
                labeled_targets = targets[labeled_mask]
                supervised_loss = F.cross_entropy(labeled_logits, labeled_targets, reduction=self.reduction)
            else:
                supervised_loss = torch.tensor(0.0, device=logits.device)
        else:
            supervised_loss = torch.tensor(0.0, device=logits.device)
        
        # 伪标签损失
        if pseudo_targets is not None and len(pseudo_targets) > 0:
            pseudo_loss = F.cross_entropy(logits, pseudo_targets, reduction='none')
            pseudo_loss = (pseudo_loss * pseudo_weights).mean()
        else:
            pseudo_loss = torch.tensor(0.0, device=logits.device)
        
        total_loss = self.alpha * supervised_loss + self.beta * pseudo_loss
        
        return total_loss, supervised_loss, pseudo_loss

class FocalLoss(nn.Module):
    """Focal Loss for multi-class classification"""
    def __init__(self, alpha=1.0, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # 分离有标签和无标签数据
        labeled_mask = targets != -1  # -1表示无标签
        if labeled_mask.sum() > 0:  # 有有标签数据
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
    """Label Smoothing Loss"""
    def __init__(self, num_classes, smoothing=0.1, reduction='mean'):
        super(LabelSmoothingLoss, self).__init__()
        self.num_classes = num_classes
        self.smoothing = smoothing
        self.reduction = reduction
    
    def forward(self, inputs, targets):
        # 分离有标签和无标签数据
        labeled_mask = targets != -1  # -1表示无标签
        if labeled_mask.sum() > 0:  # 有有标签数据
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
    """Contrastive Loss for semi-supervised learning"""
    def __init__(self, margin=1.0, temperature=0.1, reduction='mean'):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
        self.temperature = temperature
        self.reduction = reduction
    
    def forward(self, features, labels):
        # 分离有标签和无标签数据
        labeled_mask = labels != -1  # -1表示无标签
        if labeled_mask.sum() > 0:  # 有有标签数据
            labeled_features = features[labeled_mask]
            labeled_labels = labels[labeled_mask]
            
            features_norm = F.normalize(labeled_features, p=2, dim=1)
            similarity_matrix = torch.mm(features_norm, features_norm.t()) / self.temperature
            
            labels_equal = labeled_labels.unsqueeze(0) == labeled_labels.unsqueeze(1)
            
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
    """半监督学习模型评估器"""
    def __init__(self, device):
        self.device = device
        self.metrics = {}
    
    def evaluate_classification(self, model, data_loader, scaler):
        """评估分类性能"""
        model.eval()
        all_predictions = []
        all_targets = []
        all_probabilities = []
        
        with torch.no_grad():
            for data, targets in data_loader:
                data = data.to(self.device)
                targets = targets.to(self.device)
                
                logits = model(data)
                probabilities = F.softmax(logits, dim=1)
                predictions = torch.argmax(logits, dim=1)
                
                all_predictions.extend(predictions.cpu().numpy())
                all_targets.extend(targets.cpu().numpy())
                all_probabilities.extend(probabilities.cpu().numpy())
        
        all_predictions = np.array(all_predictions)
        all_targets = np.array(all_targets)
        all_probabilities = np.array(all_probabilities)
        
        # 计算分类指标
        accuracy = accuracy_score(all_targets, all_predictions)
        precision = precision_score(all_targets, all_predictions, average='weighted')
        recall = recall_score(all_targets, all_predictions, average='weighted')
        f1 = f1_score(all_targets, all_predictions, average='weighted')
        
        # 计算每个类别的指标
        precision_per_class = precision_score(all_targets, all_predictions, average=None)
        recall_per_class = recall_score(all_targets, all_predictions, average=None)
        f1_per_class = f1_score(all_targets, all_predictions, average=None)
        
        # 计算混淆矩阵
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
    
    def compute_comprehensive_metrics(self, model, data_loader, scaler):
        """
        Calculate comprehensive evaluation metrics
        """
        print("Start comprehensive model evaluation...")
        
        # evaluate classification performance
        print("Evaluate classification performance...")
        classification_metrics = self.evaluate_classification(model, data_loader, scaler)
        
                
        comprehensive_metrics = {
            'classification': classification_metrics
        }
        
        return comprehensive_metrics
    
def visualize_results(metrics, save_path=None):
    """可视化评估结果"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Pseudo-label semi-supervised learning evaluation results', fontsize=16, fontweight='bold')
    
    # 1. 混淆矩阵
    ax1 = axes[0]
    cm = metrics['classification']['confusion_matrix']
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1)
    ax1.set_title(f'Confusion matrix (accuracy: {metrics["classification"]["accuracy"]:.3f})')
    ax1.set_xlabel('Predicted label')
    ax1.set_ylabel('True label')
    
    # 2. 分类性能指标
    ax2 = axes[1]
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
    
    # 添加数值标签
    for bar, value in zip(bars, metrics_values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 3. 各类别F1分数
    ax3 = axes[2]
    f1_per_class = metrics['classification']['f1_per_class']
    class_names = [f'Class {i}' for i in range(len(f1_per_class))]
    bars = ax3.bar(class_names, f1_per_class, color='lightblue')
    ax3.set_ylabel('F1 score')
    ax3.set_title('F1 score per class')
    ax3.set_ylim(0, 1)
    ax3.tick_params(axis='x', rotation=45)
    
    # 添加数值标签
    for bar, value in zip(bars, f1_per_class):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # # 4. 综合评分
    # ax4 = axes[1, 1]
    # score = metrics['overall_score']['classification_score']
    # max_score = metrics['overall_score']['max_score']
    
    # bars = ax4.bar(['分类质量'], [score], color='skyblue', alpha=0.7, edgecolor='black')
    # ax4.set_ylabel('评分')
    # ax4.set_title(f'综合评分: {score}/{max_score}')
    # ax4.set_ylim(0, 100)
    
    # # 添加数值标签
    # for bar, score_val in zip(bars, [score]):
    #     height = bar.get_height()
    #     ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
    #             f'{score_val}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')

    
    # plt.show()
    plt.close()

def print_evaluation_report(metrics):
    """
    Print detailed evaluation report
    """
    print("\n" + "="*60)
    print("Pseudo-label semi-supervised learning evaluation report")
    print("="*60)
    
    # classification performance
    print("\n Classification performance evaluation:")
    print("-" * 30)
    print(f"Accuracy: {metrics['classification']['accuracy']:.6f}")
    print(f"Precision: {metrics['classification']['precision']:.6f}")
    print(f"Recall: {metrics['classification']['recall']:.6f}")
    print(f"F1-Score: {metrics['classification']['f1_score']:.6f}")
    
    print("\nDetailed metrics for each class:")
    print("-" * 30)
    for i, (precision, recall, f1) in enumerate(zip(
        metrics['classification']['precision_per_class'],
        metrics['classification']['recall_per_class'],
        metrics['classification']['f1_per_class']
    )):
        print(f"Class {i}: Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")
    
    

class EarlyStopping:
    """早停机制"""
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
        """保存最佳模型权重"""
        self.best_weights = model.state_dict().copy()

def set_random_seed(seed):
    """设置随机种子确保可重现性"""
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.Generator().manual_seed(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

def prepare_data(seed, batch_size, ratio="8:1:1", jobID="example_pseudo", use_unlabeled=True, kfold=0):
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
        # train_data = pd.read_csv(f"./train_example/{jobid}_data.txt", sep="\t")
        # train_data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobid+"\\"+jobid+"_data.txt", sep="\t")
        train_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")
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
        
        # 创建无标签数据加载器
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
        # val_data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobid+"\\"+jobid+"_val.txt", sep="\t")
        val_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_val.txt", sep="\t")
        val_data = val_data.dropna()
        val_features = val_data.iloc[:, 1:-1].values.astype(float)
        val_labels = val_data.iloc[:, -1].values
        
        # 处理验证集标签
        try:
            val_labels_str = val_labels.astype(str)  # test
            val_labels_encoded = label_encoder.transform(val_labels_str)
            # val_labels_encoded = label_encoder.transform(val_labels)
        except ValueError as e:
            # print(f"警告：验证集标签格式不匹配，尝试直接转换: {e}")
            # val_labels_str = val_labels.astype(str)  # test
            all_labels = np.concatenate([labeled_labels, val_labels_str])
            label_encoder.fit(all_labels)
            val_labels_encoded = label_encoder.transform(val_labels_str)
        
        val_features_scaled = scaler.transform(val_features)
        val_data_tensor = torch.FloatTensor(val_features_scaled)
        val_labels_tensor = torch.LongTensor(val_labels_encoded)
        val_loader = DataLoader(TensorDataset(val_data_tensor, val_labels_tensor), 
                              batch_size=batch_size, shuffle=False)

        # test_data = pd.read_csv(f"./train_example/{jobid}_test.txt", sep="\t")
        # test_data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobid+"\\"+jobid+"_test.txt", sep="\t")
        test_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t")
        test_data = test_data.dropna()
        test_features = test_data.iloc[:, 1:-1].values.astype(float)
        test_labels = test_data.iloc[:, -1].values
        
        # 处理测试集标签
        try:
            test_labels_str = test_labels.astype(str)
            test_labels_encoded = label_encoder.transform(test_labels_str)
            # test_labels_encoded = label_encoder.transform(test_labels) # test
        except ValueError as e:
            # print(f"警告：测试集标签格式不匹配，尝试直接转换: {e}")
            # test_labels_str = test_labels.astype(str) # test
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
        # data = pd.read_csv(f"./train_example/{jobid}_data.txt", sep="\t")
        data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_data.txt", sep="\t")
        sample_names = data.iloc[:, 0].values  # 第一列是样本名称
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
        
        # 检查数据量是否足够进行分层抽样
        unique_labels, label_counts = np.unique(labeled_labels_encoded, return_counts=True)
        min_class_count = np.min(label_counts)
        
        if min_class_count < 2:
            print(f"Warning: Some classes have too few samples (minimum {min_class_count} samples), using random split instead of stratified sampling")
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
                print(f"Warning: Some classes have too few samples (minimum {min_res_class_count} samples) during validation set split, using random split instead of stratified sampling")
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
        
        # 创建无标签数据加载器
        if use_unlabeled and len(unlabeled_features) > 0:
            unlabeled_data_tensor = torch.FloatTensor(unlabeled_features_scaled)
            unlabeled_loader = DataLoader(TensorDataset(unlabeled_data_tensor), 
                                        batch_size=batch_size, shuffle=True)
        else:
            # 创建一个空的DataLoader
            empty_data = torch.FloatTensor([])
            unlabeled_loader = DataLoader(TensorDataset(empty_data), 
                                        batch_size=batch_size, shuffle=True)
        
        input_dim = features.shape[1]
        
    else:  
        scaler = StandardScaler()
        label_encoder = LabelEncoder()
        
        # Directly load training-validation-test set file
        # train_data = pd.read_csv(f"./train_example/{jobid}_data.txt", sep="\t")
        # train_data = pd.read_csv("D:\\wamp\www\\multi_omics_own\\download_data\\Jobs\\"+jobid+"\\"+jobid+"_data.txt", sep="\t")
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
        
        # Create unlabeled data loader
        unlabeled_data_tensor = torch.FloatTensor(unlabeled_features_scaled)
        unlabeled_loader = DataLoader(TensorDataset(unlabeled_data_tensor), 
                                    batch_size=batch_size, shuffle=True)
        
        # Merge labeled and unlabeled data for training
        if use_unlabeled and len(unlabeled_features) > 0:
            # Create semi-supervised training data loader
            all_features = np.vstack([labeled_features_scaled, unlabeled_features_scaled])
            all_labels = np.concatenate([labeled_labels_encoded, 
                                       np.full(len(unlabeled_features), -1)])  # -1 represents unlabeled data
            
            all_data_tensor = torch.FloatTensor(all_features)
            all_labels_tensor = torch.LongTensor(all_labels)
            train_loader = DataLoader(TensorDataset(all_data_tensor, all_labels_tensor), 
                                    batch_size=batch_size, shuffle=True)
        else:
            train_loader = labeled_loader

        val_loader = 0
        test_data = pd.read_csv("/xp/www/AutoMATA/download_data/Jobs/"+jobID+"/"+jobID+"_test.txt", sep="\t")
        test_data = test_data.dropna()
        test_features = test_data.iloc[:, 1:-1].values.astype(float)
        test_labels = test_data.iloc[:, -1].values
        
        # Process test set labels
        try:
            test_labels_str = test_labels.astype(str)  # test
            test_labels_encoded = label_encoder.transform(test_labels_str)
            # test_labels_encoded = label_encoder.transform(test_labels)  # test
        except ValueError as e:
            # test_labels_str = test_labels.astype(str)
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
    
    return input_dim, num_classes, train_loader, val_loader, test_loader, scaler, unlabeled_loader

def generate_pseudo_labels(model, unlabeled_loader, device, confidence_threshold=0.8):
    """生成伪标签"""
    model.eval()
    pseudo_data = []
    pseudo_labels = []
    pseudo_weights = []
    
    with torch.no_grad():
        for data in unlabeled_loader:
            data = data[0].to(device)  # 无标签数据只有特征
            predictions, confidences, probabilities = model.predict_with_confidence(data)
            
            # 选择高置信度的预测作为伪标签
            high_conf_mask = confidences >= confidence_threshold
            
            if high_conf_mask.sum() > 0:
                pseudo_data.append(data[high_conf_mask].cpu())
                pseudo_labels.append(predictions[high_conf_mask].cpu())
                pseudo_weights.append(confidences[high_conf_mask].cpu())
    
    if pseudo_data:
        pseudo_data = torch.cat(pseudo_data, dim=0)
        pseudo_labels = torch.cat(pseudo_labels, dim=0)
        pseudo_weights = torch.cat(pseudo_weights, dim=0)
        
        return pseudo_data, pseudo_labels, pseudo_weights
    else:
        return None, None, None

def train_epoch(model, train_loader, unlabeled_loader, optimizer, device, loss_function='pseudo_label', 
                alpha=1.0, beta=0.5, confidence_threshold=0.8, pseudo_ratio=0.5):
    """训练一个epoch - 伪标签半监督学习"""
    model.train()
    total_loss = 0
    total_supervised_loss = 0
    total_pseudo_loss = 0
    
    # 生成伪标签
    pseudo_data, pseudo_labels, pseudo_weights = generate_pseudo_labels(
        model, unlabeled_loader, device, confidence_threshold
    )
    
    for batch_idx, (data, targets) in enumerate(train_loader):
        data = data.to(device)
        targets = targets.to(device)
        optimizer.zero_grad()
        
        # 分离有标签和无标签数据
        labeled_mask = targets != -1  # -1表示无标签
        unlabeled_mask = targets == -1
        
        if labeled_mask.sum() > 0:  # 有有标签数据
            labeled_data = data[labeled_mask]
            labeled_targets = targets[labeled_mask]
        else:
            labeled_data = None
            labeled_targets = None
        
        if unlabeled_mask.sum() > 0:  # 有无标签数据
            unlabeled_data = data[unlabeled_mask]
        else:
            unlabeled_data = None
        
        # 计算损失
        if loss_function.lower() == 'pseudo_label':
            # 伪标签损失
            loss_fn = PseudoLabelLoss(alpha=alpha, beta=beta)
            
            # 合并有标签数据和伪标签数据
            if labeled_data is not None and pseudo_data is not None:
                # 随机选择部分伪标签数据
                n_pseudo = min(len(pseudo_data), int(len(labeled_data) * pseudo_ratio))
                if n_pseudo > 0:
                    pseudo_indices = torch.randperm(len(pseudo_data))[:n_pseudo]
                    selected_pseudo_data = pseudo_data[pseudo_indices].to(device)
                    selected_pseudo_labels = pseudo_labels[pseudo_indices].to(device)
                    selected_pseudo_weights = pseudo_weights[pseudo_indices].to(device)
                    
                    # 合并数据
                    combined_data = torch.cat([labeled_data, selected_pseudo_data], dim=0)
                    combined_targets = torch.cat([labeled_targets, selected_pseudo_labels], dim=0)
                    combined_weights = torch.cat([torch.ones(len(labeled_targets), device=device), 
                                                selected_pseudo_weights], dim=0)
                else:
                    combined_data = labeled_data
                    combined_targets = labeled_targets
                    combined_weights = torch.ones(len(labeled_targets), device=device)
            elif labeled_data is not None:
                combined_data = labeled_data
                combined_targets = labeled_targets
                combined_weights = torch.ones(len(labeled_targets), device=device)
            else:
                combined_data = None
                combined_targets = None
                combined_weights = None
            
            if combined_data is not None:
                logits = model(combined_data)
                loss, supervised_loss, pseudo_loss = loss_fn(logits, combined_targets, 
                                                           combined_targets, combined_weights)
            else:
                loss = torch.tensor(0.0, device=device)
                supervised_loss = torch.tensor(0.0, device=device)
                pseudo_loss = torch.tensor(0.0, device=device)
                
        elif loss_function.lower() == 'focal':
            if labeled_data is not None:
                logits = model(labeled_data)
                focal_loss_fn = FocalLoss(alpha=1.0, gamma=2.0)
                supervised_loss = focal_loss_fn(logits, labeled_targets)
            else:
                supervised_loss = torch.tensor(0.0, device=device)
            
            pseudo_loss = torch.tensor(0.0, device=device)
            loss = supervised_loss
            
        elif loss_function.lower() == 'label_smoothing':
            if labeled_data is not None:
                logits = model(labeled_data)
                label_smooth_loss_fn = LabelSmoothingLoss(num_classes=model.num_classes, smoothing=0.1)
                supervised_loss = label_smooth_loss_fn(logits, labeled_targets)
            else:
                supervised_loss = torch.tensor(0.0, device=device)
            
            pseudo_loss = torch.tensor(0.0, device=device)
            loss = supervised_loss
            
        else:
            # 默认使用伪标签损失
            if labeled_data is not None:
                logits = model(labeled_data)
                supervised_loss = F.cross_entropy(logits, labeled_targets)
            else:
                supervised_loss = torch.tensor(0.0, device=device)
            
            pseudo_loss = torch.tensor(0.0, device=device)
            loss = supervised_loss
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        total_supervised_loss += supervised_loss.item()
        total_pseudo_loss += pseudo_loss.item()
    
    return (total_loss / len(train_loader), 
            total_supervised_loss / len(train_loader), 
            total_pseudo_loss / len(train_loader))

def validate_epoch(model, val_loader, device, loss_function='pseudo_label', alpha=1.0, beta=0.5):
    """验证一个epoch"""
    model.eval()
    total_loss = 0
    total_supervised_loss = 0
    total_pseudo_loss = 0
    
    with torch.no_grad():
        for data, targets in val_loader:
            data = data.to(device)
            targets = targets.to(device)
            
            logits = model(data)
            
            # 根据损失函数类型计算损失
            if loss_function.lower() == 'pseudo_label':
                loss_fn = PseudoLabelLoss(alpha=alpha, beta=beta)
                loss, supervised_loss, pseudo_loss = loss_fn(logits, targets, None, None)
            elif loss_function.lower() == 'focal':
                focal_loss_fn = FocalLoss(alpha=1.0, gamma=2.0)
                supervised_loss = focal_loss_fn(logits, targets)
                pseudo_loss = torch.tensor(0.0, device=device)
                loss = supervised_loss
            elif loss_function.lower() == 'label_smoothing':
                label_smooth_loss_fn = LabelSmoothingLoss(num_classes=model.num_classes, smoothing=0.1)
                supervised_loss = label_smooth_loss_fn(logits, targets)
                pseudo_loss = torch.tensor(0.0, device=device)
                loss = supervised_loss
            else:
                supervised_loss = F.cross_entropy(logits, targets)
                pseudo_loss = torch.tensor(0.0, device=device)
                loss = supervised_loss
            
            total_loss += loss.item()
            total_supervised_loss += supervised_loss.item()
            total_pseudo_loss += pseudo_loss.item()
    
    return (total_loss / len(val_loader), 
            total_supervised_loss / len(val_loader), 
            total_pseudo_loss / len(val_loader))

def train_model(model, train_loader, val_loader, unlabeled_loader, optimizer, device, epochs, patience, model_name, 
                loss_function='pseudo_label', alpha=1.0, beta=0.5, confidence_threshold=0.8, pseudo_ratio=0.5):
    """训练模型"""
    early_stopping = EarlyStopping(patience=patience)
    train_losses = []
    val_losses = []
    
    print(f"Start training model: {model_name}")
    print(f"Use loss function: {loss_function}")
    print(f"Supervised loss weight: {alpha}, Pseudo-label loss weight: {beta}")
    print(f"Confidence threshold: {confidence_threshold}, Pseudo-label ratio: {pseudo_ratio}")
    print("-" * 50)
    
    for epoch in range(epochs):
        train_loss, train_sup, train_pseudo = train_epoch(
            model, train_loader, unlabeled_loader, optimizer, device, loss_function, 
            alpha, beta, confidence_threshold, pseudo_ratio
        )
        val_loss, val_sup, val_pseudo = validate_epoch(
            model, val_loader, device, loss_function, alpha, beta
        )
        
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        
        print(f'Epoch {epoch+1}/{epochs}:')
        print(f'  train loss: {train_loss:.4f} (supervised: {train_sup:.4f}, pseudo-label: {train_pseudo:.4f})')
        print(f'  validation loss: {val_loss:.4f} (supervised: {val_sup:.4f}, pseudo-label: {val_pseudo:.4f})')
        
        if early_stopping(val_loss, model):
            print(f'Early stopping triggered, stopping training at epoch {epoch+1}')
            break
    
    return train_losses, val_losses

def test_model(model, test_loader, device, loss_function='pseudo_label', alpha=1.0, beta=0.5):
    """测试模型"""
    model.eval()
    total_loss = 0
    total_supervised_loss = 0
    total_pseudo_loss = 0
    
    with torch.no_grad():
        for data, targets in test_loader:
            data = data.to(device)
            targets = targets.to(device)
            
            logits = model(data)
            
            # 根据损失函数类型计算损失
            if loss_function.lower() == 'pseudo_label':
                loss_fn = PseudoLabelLoss(alpha=alpha, beta=beta)
                loss, supervised_loss, pseudo_loss = loss_fn(logits, targets, None, None)
            elif loss_function.lower() == 'focal':
                focal_loss_fn = FocalLoss(alpha=1.0, gamma=2.0)
                supervised_loss = focal_loss_fn(logits, targets)
                pseudo_loss = torch.tensor(0.0, device=device)
                loss = supervised_loss
            elif loss_function.lower() == 'label_smoothing':
                label_smooth_loss_fn = LabelSmoothingLoss(num_classes=model.num_classes, smoothing=0.1)
                supervised_loss = label_smooth_loss_fn(logits, targets)
                pseudo_loss = torch.tensor(0.0, device=device)
                loss = supervised_loss
            else:
                supervised_loss = F.cross_entropy(logits, targets)
                pseudo_loss = torch.tensor(0.0, device=device)
                loss = supervised_loss
            
            total_loss += loss.item()
            total_supervised_loss += supervised_loss.item()
            total_pseudo_loss += pseudo_loss.item()
    
    avg_loss = total_loss / len(test_loader)
    avg_supervised_loss = total_supervised_loss / len(test_loader)
    avg_pseudo_loss = total_pseudo_loss / len(test_loader)
    
    print(f"Test results:")
    print(f"  Total loss: {avg_loss:.4f}")
    print(f"  Supervised loss: {avg_supervised_loss:.4f}")
    print(f"  Pseudo-label loss: {avg_pseudo_loss:.4f}")
    
    return avg_loss, avg_supervised_loss, avg_pseudo_loss

def kfold_cross_validation(args, k_folds=5):
    """k-fold交叉验证"""
    print(f"\nStart {k_folds}-fold cross-validation")
    print("=" * 60)

    input_dim, num_classes, train_loader, val_loader, test_loader, scaler, unlabeled_loader = prepare_data(
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
        model = PseudoLabelNetwork(
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
            model, fold_train_loader, fold_val_loader, unlabeled_loader, optimizer, device, 
            args.epochs, args.early_stopping_patience, f"Fold_{fold+1}", 
            args.loss_function, args.alpha, args.beta, args.confidence_threshold, args.pseudo_ratio
        )
        
        # 在验证集上测试模型
        test_loss, test_sup, test_pseudo = test_model(
            model, fold_val_loader, device, args.loss_function, args.alpha, args.beta
        )
        fold_results.append({
            'fold': fold + 1,
            'test_loss': test_loss,
            'test_supervised_loss': test_sup,
            'test_pseudo_loss': test_pseudo,
            'train_losses': train_losses,
            'val_losses': val_losses
        })
    
    # 计算平均结果
    avg_test_loss = np.mean([r['test_loss'] for r in fold_results])
    avg_test_sup = np.mean([r['test_supervised_loss'] for r in fold_results])
    avg_test_pseudo = np.mean([r['test_pseudo_loss'] for r in fold_results])
    
    print(f"\n{k_folds}-fold cross-validation results:")
    print("=" * 40)
    print(f"Average validation loss: {avg_test_loss:.4f} ± {np.std([r['test_loss'] for r in fold_results]):.4f}")
    print(f"Average supervised loss: {avg_test_sup:.4f} ± {np.std([r['test_supervised_loss'] for r in fold_results]):.4f}")
    print(f"Average pseudo-label loss: {avg_test_pseudo:.4f} ± {np.std([r['test_pseudo_loss'] for r in fold_results]):.4f}")
    
    return fold_results, model, scaler, test_loader, input_dim, num_classes

def save_model(model, scaler, args, model_path, scaler_path, input_dim, num_classes):
    """保存模型和预处理器"""
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
    
    # 保存scaler和label_encoder
    import pickle
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)

 

def load_model(model_path, scaler_path, device):
    """加载模型和预处理器"""
    # 加载模型
    checkpoint = torch.load(model_path, map_location=device)
    model_config = checkpoint['model_config']
    
    model = PseudoLabelNetwork(
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
    

    
    return model, scaler

def predict(model, scaler, data, device):
    """使用训练好的模型进行预测"""
    model.eval()
    
    # 数据预处理
    data_scaled = scaler.transform(data)
    data_tensor = torch.FloatTensor(data_scaled).to(device)
    
    with torch.no_grad():
        logits = model(data_tensor)
        probabilities = F.softmax(logits, dim=1)  # [4, 3]  概率
        predictions = torch.argmax(logits, dim=1)  # torch.Size([4]) label
    
    return (predictions.cpu().numpy(), 
            probabilities.cpu().numpy())

def main():
    parser = argparse.ArgumentParser(description='伪标签半监督学习训练脚本')

    # 数据路径
    parser.add_argument('--ratio', type=str, default='0', help='数据分割比例')
    parser.add_argument('--jobid', type=str, default='example_pseudo', help='数据集ID')
    
    # 模型参数
    parser.add_argument('--dropout', type=float, default=0.1, help='Dropout率')
    
    # 训练参数
    parser.add_argument('--epochs', type=int, default=10, help='训练轮数')
    parser.add_argument('--batch_size', type=int, default=32, help='批次大小')
    parser.add_argument('--learning_rate', type=float, default=0.001, help='学习率')
    parser.add_argument('--early_stopping_patience', type=int, default=10, help='早停耐心值')
    
    # 损失函数参数
    parser.add_argument('--loss_function', type=str, default='pseudo_label', 
                       choices=['pseudo_label', 'focal', 'label_smoothing'], 
                       help='损失函数类型')
    parser.add_argument('--alpha', type=float, default=1.0, help='监督损失权重')
    parser.add_argument('--beta', type=float, default=0.5, help='伪标签损失权重')
    parser.add_argument('--confidence_threshold', type=float, default=0.8, help='伪标签置信度阈值')
    parser.add_argument('--pseudo_ratio', type=float, default=0.5, help='伪标签比例')
    
    # 优化器
    parser.add_argument('--optimizer_function', type=str, default='adam', 
                       choices=['adam', 'sgd', 'adamw', 'rmsprop'], help='优化器类型')
    
    # 半监督学习参数
    parser.add_argument('--use_unlabeled', action='store_true', default=1, help='是否使用无标签数据进行半监督学习')
    
    # 其他参数
    parser.add_argument('--random_seed', type=int, default=42, help='随机种子')
    parser.add_argument('--k_folds', type=int, default=0, help='k-fold折数')
    parser.add_argument('--save_model', action='store_true', default=1, help='是否保存模型')
    parser.add_argument('--model_path', type=str, default='pseudo_model.pth', help='模型保存路径')
    parser.add_argument('--scaler_path', type=str, default='pseudo_scaler.pkl', help='预处理器保存路径')
    
    # 评估相关参数
    parser.add_argument('--evaluate_model', action='store_true', default=1, help='是否进行模型评估')
    parser.add_argument('--save_evaluation', action='store_true', default=1, help='是否保存评估结果')
    parser.add_argument('--evaluation_path', type=str, default='results.png', help='评估结果保存路径')
    parser.add_argument('--show_plots', action='store_true', default=1, help='是否显示可视化图表')
    
    args = parser.parse_args()

    print("Pseudo model")
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
    print('confidence_threshold =', args.confidence_threshold)
    print('pseudo_ratio =', args.pseudo_ratio)
    
    # 设置随机种子
    set_random_seed(args.random_seed)
    
    # 检查CUDA可用性
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    
    if args.k_folds:
        # k-fold交叉验证
        fold_results, model, scaler, test_loader, input_dim, num_classes = kfold_cross_validation(args, args.k_folds)
    else:
        # 常规训练-验证-测试
        print("\nStart regular training process")
        print("=" * 50)
        
        # 准备数据
        input_dim, num_classes, train_loader, val_loader, test_loader, scaler, unlabeled_loader = prepare_data(
            args.random_seed, args.batch_size, args.ratio, args.jobid, args.use_unlabeled, args.k_folds
        )
        
        # 创建模型
        model = PseudoLabelNetwork(
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
            model, train_loader, val_loader, unlabeled_loader, optimizer, device, 
            args.epochs, args.early_stopping_patience, "Pseudo_Model", 
            loss_function=args.loss_function, alpha=args.alpha, beta=args.beta, 
            confidence_threshold=args.confidence_threshold, pseudo_ratio=args.pseudo_ratio
        )
        
        # 测试模型
        test_loss, test_sup, test_pseudo = test_model(
            model, test_loader, device, loss_function=args.loss_function, 
            alpha=args.alpha, beta=args.beta
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
                    # 'precision_per_class': metrics['classification']['precision_per_class'].tolist(),
                    # 'recall_per_class': metrics['classification']['recall_per_class'].tolist(),
                    # 'f1_per_class': metrics['classification']['f1_per_class'].tolist()
                }

            }
            
            json_path = args.evaluation_path.replace('.png', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_data, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    # cmd: D:/Anaconda3/envs/pt37/python.exe f:/breeding/code/my_code/multi-omics/pseudo.py --ratio 0 --jobid jobid
    # cmd: D:/Anaconda3/envs/pt37/python.exe f:/breeding/code/my_code/multi-omics/pseudo.py --ratio 8:1:1 --k_folds 5 --jobid jobid
    # 输出：pseudo_evaluation_results.json、pseudo_evaluation_results.png、pseudo_model.pth、pseudo_scaler.pkl
    main()
