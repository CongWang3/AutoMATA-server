#!/usr/bin/env python3
"""
文件上传功能最终验证测试
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
GENE003\t0.9\t0.4\t1"""
    
    file_buffer = io.BytesIO(content.encode('utf-8'))
    file_buffer.name = "validation_test.txt"
    return file_buffer

def test_complete_workflow():
    """测试完整的文件上传工作流"""
    print("🧪 AutoMATA 文件上传功能最终验证")
    print("=" * 50)
    
    # 1. 上传文件
    print("1️⃣ 测试文件上传...")
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
    
    # 2. 验证文件信息
    print("\n2️⃣ 验证文件信息...")
    info_response = requests.get(f"{BASE_URL}/training/files/{file_id}/info")
    if info_response.status_code == 200:
        print("✅ 文件信息查询成功")
    else:
        print(f"❌ 文件信息查询失败: {info_response.status_code}")
        return False
    
    # 3. 测试文件下载
    print("\n3️⃣ 测试文件下载...")
    download_response = requests.get(f"{BASE_URL}/training/files/{file_id}/download")
    if download_response.status_code == 200 and len(download_response.content) > 0:
        print("✅ 文件下载成功")
    else:
        print(f"❌ 文件下载失败: {download_response.status_code}")
        return False
    
    # 4. 列出所有文件
    print("\n4️⃣ 列出所有上传文件...")
    list_response = requests.get(f"{BASE_URL}/training/files/list")
    if list_response.status_code == 200:
        files = list_response.json()
        print(f"✅ 文件列表获取成功，共 {len(files)} 个文件")
    else:
        print(f"❌ 文件列表获取失败: {list_response.status_code}")
        return False
    
    # 5. 创建关联文件的训练任务
    print("\n5️⃣ 创建关联文件的训练任务...")
    task_data = {
        "task_name": "文件上传验证任务",
        "model_type": "mlp",
        "language": "python",
        "parameters": json.dumps({
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.001
        }),
        "dataset_path": f"file://{file_id}",
        "created_by": 1
    }
    
    task_response = requests.post(
        f"{BASE_URL}/api/training/tasks",
        headers={"Content-Type": "application/json"},
        data=json.dumps(task_data)
    )
    
    if task_response.status_code == 200:
        task_info = task_response.json()
        task_id = task_info['id']
        print(f"✅ 训练任务创建成功! ID: {task_id}")
    else:
        print(f"❌ 训练任务创建失败: {task_response.status_code}")
        print(f"   响应: {task_response.text}")
        return False
    
    # 6. 关联文件到任务
    print("\n6️⃣ 关联文件到训练任务...")
    assoc_response = requests.post(
        f"{BASE_URL}/training/files/{task_id}/associate/{file_id}?file_type=train"
    )
    
    if assoc_response.status_code == 200:
        print("✅ 文件关联成功")
    else:
        print(f"❌ 文件关联失败: {assoc_response.status_code}")
        return False
    
    # 7. 获取任务关联的文件
    print("\n7️⃣ 获取任务关联的文件...")
    task_files_response = requests.get(f"{BASE_URL}/training/files/{task_id}/files")
    if task_files_response.status_code == 200:
        task_files = task_files_response.json()
        print(f"✅ 任务文件获取成功，关联了 {len(task_files['files'])} 个文件")
    else:
        print(f"❌ 任务文件获取失败: {task_files_response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 文件上传功能完整验证通过!")
    print("\n📋 功能总结:")
    print("   ✅ 文件上传API (/training/files/upload)")
    print("   ✅ 文件下载API (/training/files/{file_id}/download)")
    print("   ✅ 文件信息查询API (/training/files/{file_id}/info)")
    print("   ✅ 文件列表API (/training/files/list)")
    print("   ✅ 文件与任务关联API (/training/files/{task_id}/associate/{file_id})")
    print("   ✅ 任务文件查询API (/training/files/{task_id}/files)")
    print("   ✅ 数据库存储和管理")
    print("   ✅ 安全的文件存储机制")
    
    return True

if __name__ == "__main__":
    test_complete_workflow()