"""
AutoMATA 模型训练集成模块
集成 /xp/www/AutoMATA/code 中的机器学习模型
"""

import sys
import os
import json
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import shutil

# 添加模型代码路径
MODEL_CODE_PATH = "/xp/www/AutoMATA/code"
sys.path.insert(0, MODEL_CODE_PATH)
sys.path.insert(0, os.path.join(MODEL_CODE_PATH, "train_model"))
sys.path.insert(0, os.path.join(MODEL_CODE_PATH, "use_model"))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelTrainer:
    """模型训练器"""
    
    def __init__(self, job_id: str, model_type: str = "mlp"):
        self.job_id = job_id
        self.model_type = model_type
        self.job_path = f"/xp/www/AutoMATA/download_data/Jobs/{job_id}"
        self.model_code_path = MODEL_CODE_PATH
        
    def prepare_training_data(self, data_config: Dict[str, Any]) -> bool:
        """
        准备训练数据
        """
        try:
            # 确保作业目录存在
            os.makedirs(self.job_path, exist_ok=True)
            
            # 处理前端传入的数据文件
            if self._handle_frontend_data_files(data_config):
                logger.info("使用前端传入的数据文件")
            else:
                # 如果没有前端数据，则生成测试数据
                self._generate_sample_data()
                logger.info("生成示例数据文件")
            
            # 如果需要数据整合，调用integration.py
            if data_config.get('integration_needed', False):
                self._run_data_integration(data_config)
            
            logger.info(f"数据准备完成: {self.job_path}")
            return True
            
        except Exception as e:
            logger.error(f"数据准备失败: {str(e)}")
            return False
    
    def _run_data_integration(self, data_config: Dict[str, Any]):
        """运行数据整合脚本"""
        integration_script = os.path.join(self.model_code_path, "train_model", "integration.py")
        
        cmd = [
            "python", integration_script,
            "--jobID", self.job_id,
            "--pheno_file", data_config.get('pheno_file', ''),
            "--file_1", data_config.get('file_1', ''),
            "--file_2", data_config.get('file_2', ''),
            "--file_3", data_config.get('file_3', ''),
            "--output_file", f"{self.job_path}/{self.job_id}_data.txt"
        ]
        
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if result.returncode != 0:
            raise Exception(f"数据整合失败: {result.stderr}")
    
    def _generate_sample_data(self):
        """
        生成示例训练数据
        """
        import numpy as np
        import pandas as pd
        
        # 生成示例数据
        np.random.seed(42)
        n_samples = 100
        n_features = 10
        
        # 生成特征数据
        X = np.random.randn(n_samples, n_features)
        
        # 生成标签（二分类）
        y = np.random.randint(0, 2, n_samples)
        
        # 创建DataFrame
        feature_columns = [f"feature_{i}" for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_columns)
        df['label'] = y
        
        # 保存数据文件
        data_file_path = f"{self.job_path}/{self.job_id}_data.txt"
        df.to_csv(data_file_path, sep='\t', index=False)
        
        # 生成测试数据
        test_df = df.sample(n=20, random_state=42)
        test_file_path = f"{self.job_path}/{self.job_id}_test.txt"
        test_df.to_csv(test_file_path, sep='\t', index=False)
        
        # 生成验证数据
        val_df = df.sample(n=20, random_state=24)
        val_file_path = f"{self.job_path}/{self.job_id}_val.txt"
        val_df.to_csv(val_file_path, sep='\t', index=False)
        
        logger.info(f"生成示例数据文件: {data_file_path}")
    
    def _handle_frontend_data_files(self, data_config: Dict[str, Any]) -> bool:
        """
        处理前端传入的数据文件
        """
        try:
            # 获取前端传入的文件名
            train_file = data_config.get('train_file', '')
            val_file = data_config.get('val_file', '')
            test_file = data_config.get('test_file', '')
            
            # 检查是否有有效的文件名
            if not any([train_file, val_file, test_file]):
                return False
            
            # 假设文件存储在特定目录中，这里需要根据实际部署情况调整
            base_data_path = "/xp/www/AutoMATA/uploaded_data"  # 前端上传文件的存储路径
            
            # 复制训练文件
            if train_file:
                source_path = os.path.join(base_data_path, train_file)
                dest_path = f"{self.job_path}/{self.job_id}_data.txt"
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"复制训练文件: {source_path} -> {dest_path}")
                else:
                    logger.warning(f"训练文件不存在: {source_path}")
                    return False
            
            # 复制验证文件
            if val_file:
                source_path = os.path.join(base_data_path, val_file)
                dest_path = f"{self.job_path}/{self.job_id}_val.txt"
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"复制验证文件: {source_path} -> {dest_path}")
            
            # 复制测试文件
            if test_file:
                source_path = os.path.join(base_data_path, test_file)
                dest_path = f"{self.job_path}/{self.job_id}_test.txt"
                if os.path.exists(source_path):
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"复制测试文件: {source_path} -> {dest_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"处理前端数据文件失败: {str(e)}")
            return False
    
    def train_model(self, training_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        训练模型
        """
        try:
            # 根据模型类型选择对应的训练脚本
            model_script = self._get_model_script()
            
            # 构建训练命令
            cmd = self._build_training_command(model_script, training_params)
            
            # 执行训练
            logger.info(f"开始训练模型: {self.model_type}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=self.job_path)
            
            if result.returncode != 0:
                raise Exception(f"模型训练失败: {result.stderr}")
            
            # 保存训练结果
            training_result = self._save_training_result(result.stdout, training_params)
            
            logger.info(f"模型训练完成: {self.job_id}")
            return training_result
            
        except Exception as e:
            logger.error(f"模型训练出错: {str(e)}")
            raise
    
    def _get_model_script(self) -> str:
        """获取对应模型类型的训练脚本"""
        model_scripts = {
            'mlp': 'mlp.py',
            'cnn': 'cnn.py',
            'lstm': 'lstm.py',
            'rnn': 'rnn.py',
            'transformer': 'transformer.py',
            'autoencoder': 'autoencoder.py',
            'vae': 'VAE.py',
            'som': 'som.py',
            'rbfn': 'rbfn.py',
            'deepcluster': 'deepcluster.py',
            'ladder': 'ladder.py',
            'pseudo': 'pseudo.py'
        }
        
        script_name = model_scripts.get(self.model_type.lower())
        if not script_name:
            raise ValueError(f"不支持的模型类型: {self.model_type}")
        
        return os.path.join(self.model_code_path, "train_model", script_name)
    
    def _build_training_command(self, model_script: str, params: Dict[str, Any]) -> list:
        """构建训练命令"""
        cmd = ["python", model_script, "--jobID", self.job_id]
        
        # 添加通用参数
        if 'epochs' in params:
            cmd.extend(["--epochs", str(params['epochs'])])
        if 'batch_size' in params:
            cmd.extend(["--bs", str(params['batch_size'])])
        if 'learning_rate' in params:
            cmd.extend(["--lr", str(params['learning_rate'])])
        if 'dropout_rate' in params:
            cmd.extend(["--dropout_rate", str(params['dropout_rate'])])
        
        return cmd
    
    def _save_training_result(self, output: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """保存训练结果"""
        result = {
            'job_id': self.job_id,
            'model_type': self.model_type,
            'parameters': params,
            'training_log': output,
            'model_path': f"{self.job_path}/model.pth",
            'result_path': f"{self.job_path}/results.json"
        }
        
        # 保存结果到文件
        with open(result['result_path'], 'w') as f:
            json.dump(result, f, indent=2)
        
        return result

class ModelPredictor:
    """模型预测器"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job_path = f"/xp/www/AutoMATA/download_data/Jobs/{job_id}"
        self.model_code_path = MODEL_CODE_PATH
    
    def predict(self, test_data_path: str, model_path: str = None) -> Dict[str, Any]:
        """
        使用训练好的模型进行预测
        """
        try:
            # 复制测试数据到作业目录
            test_filename = os.path.basename(test_data_path)
            destination = f"{self.job_path}/{test_filename}"
            shutil.copy2(test_data_path, destination)
            
            # 确定使用的预测脚本
            predictor_script = self._get_predictor_script()
            
            # 构建预测命令
            cmd = [
                "python", predictor_script,
                "--jobID", self.job_id,
                "--test_file", destination
            ]
            
            if model_path:
                cmd.extend(["--model_path", model_path])
            
            # 执行预测
            logger.info(f"开始模型预测: {self.job_id}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, cwd=self.job_path)
            
            if result.returncode != 0:
                raise Exception(f"模型预测失败: {result.stderr}")
            
            # 保存预测结果
            prediction_result = self._save_prediction_result(result.stdout)
            
            logger.info(f"模型预测完成: {self.job_id}")
            return prediction_result
            
        except Exception as e:
            logger.error(f"模型预测出错: {str(e)}")
            raise
    
    def _get_predictor_script(self) -> str:
        """获取预测脚本"""
        # 这里可以根据模型类型选择不同的预测脚本
        return os.path.join(self.model_code_path, "use_model", "general.py")
    
    def _save_prediction_result(self, output: str) -> Dict[str, Any]:
        """保存预测结果"""
        result = {
            'job_id': self.job_id,
            'prediction_output': output,
            'result_file': f"{self.job_path}/predictions.csv",
            'timestamp': str(pd.Timestamp.now())
        }
        
        # 保存结果到文件
        result_file = f"{self.job_path}/prediction_result.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result

# 工具函数
def get_available_models() -> list:
    """获取可用的模型列表"""
    return [
        'mlp', 'cnn', 'lstm', 'rnn', 'transformer',
        'autoencoder', 'vae', 'som', 'rbfn',
        'deepcluster', 'ladder', 'pseudo'
    ]

def validate_model_type(model_type: str) -> bool:
    """验证模型类型是否有效"""
    return model_type.lower() in get_available_models()

def get_model_description(model_type: str) -> str:
    """获取模型描述"""
    descriptions = {
        'mlp': '多层感知机 - 适用于特征工程后的表格数据',
        'cnn': '卷积神经网络 - 适用于图像或序列数据',
        'lstm': '长短期记忆网络 - 适用于时间序列数据',
        'rnn': '循环神经网络 - 适用于序列数据',
        'transformer': 'Transformer模型 - 适用于序列建模',
        'autoencoder': '自编码器 - 适用于无监督学习和降维',
        'vae': '变分自编码器 - 适用于生成模型',
        'som': '自组织映射 - 适用于聚类和可视化',
        'rbfn': '径向基函数网络 - 适用于函数逼近',
        'deepcluster': '深度聚类 - 适用于无监督聚类',
        'ladder': 'Ladder网络 - 适用于半监督学习',
        'pseudo': '伪标签网络 - 适用于半监督学习'
    }
    return descriptions.get(model_type.lower(), '未知模型类型')