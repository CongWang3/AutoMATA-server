#!/usr/bin/env python3
"""
测试后端自动关联功能
"""

import requests
import json
import io

BASE_URL = "http://localhost:8000"

def create_test_file():
    """创建测试文件"""
    content = """GeneID\tExpression1\tExpression2\tLabel
GENE001\t0.5\t0.3\t1
GENE002\t0.2\t0.7\t0
GENE003\t0.9\t0.4\t1
GENE004\t0.1\t0.2\t0
GENE005\t0.8\t0.9\t1"""
    
    file_buffer = io.BytesIO(content.encode('utf-8'))
    file_buffer.name = "auto_assoc_test.txt"
    return file_buffer

def test_automatic_association():
    """测试自动关联功能"""
    print("🧪 AutoMATA 后端自动关联功能测试")
    print("=" * 50)
    
    # 1. 上传文件
    print("1️⃣ 上传测试文件...")
    test_file = create_test_file()
    
    files = {'file': test_file}
    data = {'file_type': 'train', 'user_id': 1}
    
    upload_response = requests.post(
        f"{BASE_URL}/training/files/upload",
        files=files,
        data=data
    )
    
    if upload_response.status_code != 200:
        print(f"❌ 文件上传失败: {upload_response.status_code}")
        return False
    
    file_info = upload_response.json()
    file_id = file_info['id']
    print(f"✅ 文件上传成功! ID: {file_id}")
    
    # 2. 创建训练任务（使用file://格式）
    print("\n2️⃣ 创建训练任务并测试自动关联...")
    task_data = {
        "task_name": "自动关联测试任务",
        "model_type": "mlp",
        "language": "python",
        "parameters": json.dumps({
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.001
        }),
        "dataset_path": f"file://{file_id}",  # 关键：使用file://格式
        "created_by": 1
    }
    
    task_response = requests.post(
        f"{BASE_URL}/api/training/tasks",
        headers={"Content-Type": "application/json"},
        data=json.dumps(task_data)
    )
    
    if task_response.status_code != 200:
        print(f"❌ 训练任务创建失败: {task_response.status_code}")
        return False
    
    task_info = task_response.json()
    task_id = task_info['id']
    print(f"✅ 训练任务创建成功! ID: {task_id}")
    
    # 3. 等待并验证自动关联
    print("\n3️⃣ 验证自动关联结果...")
    import time
    
    # 等待后端处理完成
    time.sleep(3)
    
    # 检查任务关联的文件
    assoc_response = requests.get(f"{BASE_URL}/training/files/{task_id}/files")
    
    if assoc_response.status_code == 200:
        assoc_data = assoc_response.json()
        files = assoc_data.get('files', [])
        
        if len(files) > 0:
            print("✅ 自动关联成功!")
            print(f"   关联文件数量: {len(files)}")
            for file_assoc in files:
                print(f"   - 文件ID: {file_assoc['file_id']}")
                print(f"   - 文件名: {file_assoc['original_filename']}")
                print(f"   - 文件类型: {file_assoc['file_type']}")
            return True
        else:
            print("❌ 自动关联失败：未找到关联文件")
            return False
    else:
        print(f"❌ 查询关联文件失败: {assoc_response.status_code}")
        return False

def test_manual_association():
    """测试手动关联作为对比"""
    print("\n" + "=" * 50)
    print("🔄 对比测试：手动关联")
    
    # 上传另一个文件
    test_file = create_test_file()
    files = {'file': test_file}
    data = {'file_type': 'train', 'user_id': 1}
    
    upload_response = requests.post(
        f"{BASE_URL}/training/files/upload",
        files=files,
        data=data
    )
    
    if upload_response.status_code != 200:
        print("❌ 文件上传失败")
        return False
    
    file_info = upload_response.json()
    file_id = file_info['id']
    
    # 创建任务（不使用file://格式）
    task_data = {
        "task_name": "手动关联测试任务",
        "model_type": "mlp",
        "language": "python",
        "parameters": json.dumps({"epochs": 1}),
        "dataset_path": "regular_path.txt",
        "created_by": 1
    }
    
    task_response = requests.post(
        f"{BASE_URL}/api/training/tasks",
        headers={"Content-Type": "application/json"},
        data=json.dumps(task_data)
    )
    
    if task_response.status_code != 200:
        print("❌ 任务创建失败")
        return False
    
    task_info = task_response.json()
    task_id = task_info['id']
    
    # 手动关联
    assoc_response = requests.post(
        f"{BASE_URL}/training/files/{task_id}/associate/{file_id}?file_type=train"
    )
    
    if assoc_response.status_code == 200:
        print("✅ 手动关联成功")
        return True
    else:
        print("❌ 手动关联失败")
        return False

def main():
    """主测试函数"""
    print("🎯 AutoMATA 自动关联功能完整测试")
    
    # 测试自动关联
    auto_success = test_automatic_association()
    
    # 测试手动关联（作为对比）
    manual_success = test_manual_association()
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    print(f"   自动关联: {'✅ 成功' if auto_success else '❌ 失败'}")
    print(f"   手动关联: {'✅ 成功' if manual_success else '❌ 失败'}")
    
    if auto_success:
        print("\n🎉 后端自动关联功能工作正常!")
        print("\n📋 使用说明:")
        print("   前端只需在dataset_path中使用 'file://{file_id}' 格式")
        print("   后端会自动完成文件与任务的关联")
        print("   无需额外的API调用")
    else:
        print("\n⚠️  自动关联功能需要修复")

if __name__ == "__main__":
    main()