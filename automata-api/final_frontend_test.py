#!/usr/bin/env python3
"""
最终验证：前端新数据格式完全适配测试
"""

import requests
import json
import os
import time

def test_complete_workflow():
    """测试完整的前端数据格式工作流"""
    print("🧪 AutoMATA 前端新数据格式完整测试")
    print("=" * 50)
    
    # 准备测试数据文件
    test_dir = "/xp/www/AutoMATA/uploaded_data"
    os.makedirs(test_dir, exist_ok=True)
    
    # 创建训练数据文件
    train_data = """GeneID\tfeature_1\tfeature_2\tfeature_3\tlabel
GENE001\t0.5\t0.3\t0.8\t1
GENE002\t0.2\t0.7\t0.1\t0
GENE003\t0.9\t0.4\t0.6\t1
GENE004\t0.1\t0.2\t0.3\t0
GENE005\t0.8\t0.9\t0.7\t1"""
    
    train_file = "20240808232043_OtJF37SH_train.txt"
    with open(os.path.join(test_dir, train_file), 'w') as f:
        f.write(train_data)
    
    # 创建验证数据文件
    val_data = """GeneID\tfeature_1\tfeature_2\tfeature_3\tlabel
GENE006\t0.4\t0.5\t0.2\t0
GENE007\t0.6\t0.1\t0.9\t1"""
    
    val_file = "20240808232043_OtJF37SH_val.txt"
    with open(os.path.join(test_dir, val_file), 'w') as f:
        f.write(val_data)
    
    # 创建测试数据文件
    test_data = """GeneID\tfeature_1\tfeature_2\tfeature_3\tlabel
GENE008\t0.3\t0.6\t0.4\t0
GENE009\t0.7\t0.8\t0.5\t1"""
    
    test_file = "20240808232043_OtJF37SH_test.txt"
    with open(os.path.join(test_dir, test_file), 'w') as f:
        f.write(test_data)
    
    print("✅ 测试数据文件准备完成")
    
    # 前端提供的数据格式
    frontend_data = {
        "task_name": "前端标准格式完整测试",
        "model_type": "cnn",
        "language": "python",
        "parameters": json.dumps({
            "epochs": 1,
            "learning_rate": 0.001,
            "early_stopping": 10,
            "batch_size": 32,
            "random_seed": 42,
            "label_count": 2,
            "strategy": "split",
            "split_ratio": {"train": 8, "validation": 1, "test": 1},
            "kfold_value": 5
        }),
        "dataset_path": "20240808232043_OtJF37SH_train.txt",  # 关键：文件名在此处
        "created_by": 1
    }
    
    print("\n📤 前端发送的标准数据格式:")
    print(json.dumps(frontend_data, indent=2, ensure_ascii=False))
    
    try:
        # 1. 创建训练任务
        print("\n🚀 步骤1: 创建训练任务")
        response = requests.post(
            "http://localhost:8000/api/training/tasks",
            headers={"Content-Type": "application/json"},
            data=json.dumps(frontend_data)
        )
        
        if response.status_code != 200:
            print(f"❌ 任务创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
        task_info = response.json()
        task_id = task_info.get("id")
        print(f"✅ 任务创建成功! ID: {task_id}")
        
        # 2. 验证数据解析
        print("\n🔍 步骤2: 验证后端数据解析")
        stored_parameters = json.loads(task_info.get('parameters', '{}'))
        dataset_path = task_info.get('dataset_path', '')
        
        print(f"   存储的parameters字段: {list(stored_parameters.keys())}")
        print(f"   dataset_path字段: {dataset_path}")
        
        # 3. 监控任务执行
        print("\n⏳ 步骤3: 监控任务执行过程")
        max_wait = 90
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status_response = requests.get(f"http://localhost:8000/api/training/tasks/{task_id}")
            if status_response.status_code == 200:
                status_info = status_response.json()
                status = status_info.get("status")
                print(f"   当前状态: {status}")
                
                if status == "completed":
                    print("✅ 任务成功完成!")
                    
                    # 4. 验证结果
                    print("\n📋 步骤4: 验证处理结果")
                    
                    # 检查作业目录
                    job_dir = f"/xp/www/AutoMATA/download_data/Jobs/task_{task_id}_{task_info.get('task_name')}"
                    if os.path.exists(job_dir):
                        files = os.listdir(job_dir)
                        print(f"   作业目录文件: {files}")
                        
                        # 检查关键文件
                        expected_files = [
                            f"task_{task_id}_{task_info.get('task_name')}_data.txt",
                            f"task_{task_id}_{task_info.get('task_name')}_val.txt",
                            f"task_{task_id}_{task_info.get('task_name')}_test.txt"
                        ]
                        
                        all_found = True
                        for expected_file in expected_files:
                            if expected_file in files:
                                print(f"   ✅ 找到文件: {expected_file}")
                            else:
                                print(f"   ❌ 缺少文件: {expected_file}")
                                all_found = False
                        
                        if all_found:
                            print("\n🎉 测试完全通过!")
                            print("   ✅ 前端数据格式被正确接收")
                            print("   ✅ 后端自动解析文件名")
                            print("   ✅ 自动生成验证和测试文件名")
                            print("   ✅ 文件复制处理成功")
                            return True
                        else:
                            print("\n⚠️  文件处理不完整")
                            return False
                    else:
                        print("❌ 作业目录未创建")
                        return False
                        
                elif status == "failed":
                    print("❌ 任务执行失败")
                    # 获取错误日志
                    logs_response = requests.get(f"http://localhost:8000/api/training/tasks/{task_id}/logs")
                    if logs_response.status_code == 200:
                        logs = logs_response.json()
                        error_logs = [log for log in logs if log.get("log_level") == "ERROR"]
                        if error_logs:
                            print(f"   错误详情: {error_logs[-1].get('message', '未知错误')}")
                    return False
                    
                elif status == "running":
                    print("   ⏳ 任务正在运行中...")
                    
            time.sleep(3)
            
        print("⏰ 任务执行超时")
        return False
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {str(e)}")
        return False

def main():
    success = test_complete_workflow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎊 前端新数据格式适配完全成功!")
        print("\n📋 总结:")
        print("   • 前端无需修改现有代码")
        print("   • 后端自动适配dataset_path字段")
        print("   • 支持自动生成验证和测试文件名")
        print("   • 保持原有功能完全兼容")
    else:
        print("💥 测试失败，请检查系统配置")

if __name__ == "__main__":
    main()