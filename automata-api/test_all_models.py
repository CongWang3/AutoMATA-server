#!/usr/bin/env python3
"""
AutoMATA 模型训练系统全面测试脚本
测试所有12种机器学习模型的功能和集成
"""

import requests
import json
import time
from typing import Dict, List

# API配置
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api"

class ModelTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = {"Content-Type": "application/json"}
        self.test_results = []
        
    def log_result(self, test_name: str, status: str, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: {details}")
        
    def test_api_health(self) -> bool:
        """测试API健康状态"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                self.log_result("API健康检查", "PASS", "API服务正常运行")
                return True
            else:
                self.log_result("API健康检查", "FAIL", f"状态码: {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API健康检查", "FAIL", f"连接错误: {str(e)}")
            return False
    
    def test_get_available_models(self) -> List[Dict]:
        """测试获取可用模型列表"""
        try:
            response = requests.get(f"{self.base_url}{API_PREFIX}/training/models/available")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                self.log_result("获取模型列表", "PASS", f"发现 {len(models)} 个模型")
                return models
            else:
                self.log_result("获取模型列表", "FAIL", f"状态码: {response.status_code}")
                return []
        except Exception as e:
            self.log_result("获取模型列表", "FAIL", f"错误: {str(e)}")
            return []
    
    def test_create_training_task(self, model_type: str, task_name: str) -> int:
        """测试创建训练任务"""
        task_data = {
            "task_name": task_name,
            "model_type": model_type,
            "language": "python",
            "parameters": json.dumps({
                "epochs": 1,
                "batch_size": 2,
                "learning_rate": 0.001
            }),
            "dataset_path": f"/data/test_{model_type}_data.csv",
            "created_by": 1
        }
        
        try:
            response = requests.post(
                f"{self.base_url}{API_PREFIX}/training/tasks",
                headers=self.headers,
                data=json.dumps(task_data)
            )
            
            if response.status_code == 200:
                task_info = response.json()
                task_id = task_info.get("id")
                self.log_result(f"创建{model_type}任务", "PASS", f"任务ID: {task_id}")
                return task_id
            else:
                self.log_result(f"创建{model_type}任务", "FAIL", f"状态码: {response.status_code}")
                return -1
                
        except Exception as e:
            self.log_result(f"创建{model_type}任务", "FAIL", f"错误: {str(e)}")
            return -1
    
    def test_get_task_status(self, task_id: int, model_type: str) -> str:
        """测试获取任务状态"""
        try:
            response = requests.get(f"{self.base_url}{API_PREFIX}/training/tasks/{task_id}")
            if response.status_code == 200:
                task_info = response.json()
                status = task_info.get("status", "unknown")
                self.log_result(f"查询{model_type}任务状态", "PASS", f"状态: {status}")
                return status
            else:
                self.log_result(f"查询{model_type}任务状态", "FAIL", f"状态码: {response.status_code}")
                return "error"
        except Exception as e:
            self.log_result(f"查询{model_type}任务状态", "FAIL", f"错误: {str(e)}")
            return "error"
    
    def test_get_task_logs(self, task_id: int, model_type: str) -> List[Dict]:
        """测试获取任务日志"""
        try:
            response = requests.get(f"{self.base_url}{API_PREFIX}/training/tasks/{task_id}/logs")
            if response.status_code == 200:
                logs = response.json()
                self.log_result(f"获取{model_type}任务日志", "PASS", f"日志条数: {len(logs)}")
                return logs
            else:
                self.log_result(f"获取{model_type}任务日志", "FAIL", f"状态码: {response.status_code}")
                return []
        except Exception as e:
            self.log_result(f"获取{model_type}任务日志", "FAIL", f"错误: {str(e)}")
            return []
    
    def wait_for_task_completion(self, task_id: int, model_type: str, timeout: int = 30) -> str:
        """等待任务完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.test_get_task_status(task_id, model_type)
            if status in ["completed", "failed"]:
                return status
            time.sleep(2)
        return "timeout"
    
    def test_all_models_comprehensive(self):
        """全面测试所有模型"""
        print("=" * 60)
        print("🚀 AutoMATA 模型训练系统全面测试开始")
        print("=" * 60)
        
        # 1. 基础API测试
        if not self.test_api_health():
            print("❌ API服务不可用，测试终止")
            return
        
        # 2. 获取模型列表
        available_models = self.test_get_available_models()
        if not available_models:
            print("❌ 无法获取模型列表，测试终止")
            return
        
        print(f"\n📋 可用模型 ({len(available_models)} 个):")
        for model in available_models:
            print(f"  - {model['model_type']}: {model['description']}")
        
        # 3. 测试每个模型
        print(f"\n🧪 开始逐个测试模型...")
        tested_models = []
        failed_models = []
        
        for i, model_info in enumerate(available_models):
            model_type = model_info["model_type"]
            task_name = f"{model_type.upper()}测试任务_{i+1}"
            
            print(f"\n--- 测试模型 {i+1}/{len(available_models)}: {model_type} ---")
            
            # 创建训练任务
            task_id = self.test_create_training_task(model_type, task_name)
            if task_id == -1:
                failed_models.append(model_type)
                continue
            
            tested_models.append({
                "model_type": model_type,
                "task_id": task_id,
                "task_name": task_name
            })
            
            # 等待任务处理
            print(f"⏳ 等待{model_type}任务处理...")
            final_status = self.wait_for_task_completion(task_id, model_type)
            
            # 获取详细日志
            logs = self.test_get_task_logs(task_id, model_type)
            
            # 分析结果
            if final_status == "completed":
                self.log_result(f"{model_type}完整测试", "PASS", "任务成功完成")
            elif final_status == "failed":
                self.log_result(f"{model_type}完整测试", "FAIL", "任务执行失败")
                # 显示失败原因
                error_logs = [log for log in logs if log.get("log_level") == "ERROR"]
                if error_logs:
                    print(f"    错误详情: {error_logs[-1].get('message', '未知错误')}")
            else:
                self.log_result(f"{model_type}完整测试", "TIMEOUT", "任务超时")
        
        # 4. 生成测试报告
        self.generate_test_report(tested_models, failed_models, available_models)
    
    def generate_test_report(self, tested_models: List[Dict], failed_models: List[str], all_models: List[Dict]):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告汇总")
        print("=" * 60)
        
        total_models = len(all_models)
        tested_count = len(tested_models)
        failed_count = len(failed_models)
        success_count = tested_count - failed_count
        
        print(f"总模型数: {total_models}")
        print(f"测试模型数: {tested_count}")
        print(f"成功数: {success_count}")
        print(f"失败数: {failed_count}")
        print(f"成功率: {success_count/tested_count*100:.1f}%" if tested_count > 0 else "成功率: 0%")
        
        if failed_models:
            print(f"\n❌ 失败的模型:")
            for model in failed_models:
                print(f"  - {model}")
        
        print(f"\n✅ 成功测试的模型:")
        for model_info in tested_models:
            if model_info["model_type"] not in failed_models:
                print(f"  - {model_info['model_type']} (任务ID: {model_info['task_id']})")
        
        # 详细结果
        print(f"\n📋 详细测试结果:")
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⏰"
            print(f"{status_icon} [{result['status']}] {result['test_name']}")
            if result['details']:
                print(f"    {result['details']}")
        
        # 保存结果到文件
        report_data = {
            "summary": {
                "total_models": total_models,
                "tested_count": tested_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": f"{success_count/tested_count*100:.1f}%" if tested_count > 0 else "0%"
            },
            "failed_models": failed_models,
            "successful_models": [m["model_type"] for m in tested_models if m["model_type"] not in failed_models],
            "all_results": self.test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("model_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 测试报告已保存到: model_test_report.json")

def main():
    """主函数"""
    tester = ModelTester()
    tester.test_all_models_comprehensive()

if __name__ == "__main__":
    main()