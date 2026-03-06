#!/usr/bin/env python3
"""
文件上传功能完整测试脚本
"""

import requests
import json
import os
import io
from datetime import datetime

BASE_URL = "http://localhost:8000"

def create_test_file(content: str, filename: str) -> io.BytesIO:
    """创建测试文件"""
    file_buffer = io.BytesIO(content.encode('utf-8'))
    file_buffer.name = filename
    return file_buffer

def test_file_upload():
    """测试文件上传功能"""
    print("🚀 测试文件上传功能")
    print("=" * 40)
    
    # 创建测试数据
    test_content = """GeneID\tExpression1\tExpression2\tLabel
GENE001\t0.5\t0.3\t1
GENE002\t0.2\t0.7\t0
GENE003\t0.9\t0.4\t1
GENE004\t0.1\t0.2\t0
GENE005\t0.8\t0.9\t1"""
    
    test_file = create_test_file(test_content, "test_dataset.txt")
    
    try:
        # 上传文件
        files = {'file': test_file}
        data = {'file_type': 'train', 'user_id': 1}
        
        response = requests.post(
            f"{BASE_URL}/training/files/upload",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            file_info = response.json()
            print(f"✅ 文件上传成功!")
            print(f"   文件ID: {file_info['id']}")
            print(f"   原始文件名: {file_info['original_filename']}")
            print(f"   存储文件名: {file_info['stored_filename']}")
            print(f"   文件大小: {file_info['file_size']} bytes")
            return file_info['id']
        else:
            print(f"❌ 文件上传失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 上传请求出错: {str(e)}")
        return None

def test_file_download(file_id: str):
    """测试文件下载功能"""
    print(f"\n📥 测试文件下载功能 (ID: {file_id})")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/training/files/{file_id}/download")
        
        if response.status_code == 200:
            print(f"✅ 文件下载成功!")
            print(f"   内容长度: {len(response.content)} bytes")
            # 显示部分内容预览
            content_preview = response.text[:200] + "..." if len(response.text) > 200 else response.text
            print(f"   内容预览: {content_preview}")
            return True
        else:
            print(f"❌ 文件下载失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 下载请求出错: {str(e)}")
        return False

def test_file_info(file_id: str):
    """测试获取文件信息"""
    print(f"\n🔍 测试获取文件信息 (ID: {file_id})")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/training/files/{file_id}/info")
        
        if response.status_code == 200:
            file_info = response.json()
            print(f"✅ 获取文件信息成功!")
            print(f"   文件名: {file_info['original_filename']}")
            print(f"   上传时间: {file_info['upload_time']}")
            print(f"   文件大小: {file_info['file_size']} bytes")
            return True
        else:
            print(f"❌ 获取文件信息失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 获取信息请求出错: {str(e)}")
        return False

def test_create_training_task_with_file(file_id: str):
    """测试创建关联文件的训练任务"""
    print(f"\n🧠 测试创建关联文件的训练任务")
    print("=" * 40)
    
    task_data = {
        "task_name": "文件上传测试任务",
        "model_type": "mlp",
        "language": "python",
        "parameters": json.dumps({
            "epochs": 1,
            "batch_size": 32,
            "learning_rate": 0.001,
            "train_file_id": file_id  # 新增：关联文件ID
        }),
        "dataset_path": f"file://{file_id}",  # 使用文件ID作为数据集路径
        "created_by": 1
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/training/tasks",
            headers={"Content-Type": "application/json"},
            data=json.dumps(task_data)
        )
        
        if response.status_code == 200:
            task_info = response.json()
            task_id = task_info['id']
            print(f"✅ 训练任务创建成功!")
            print(f"   任务ID: {task_id}")
            print(f"   任务名称: {task_info['task_name']}")
            return task_id
        else:
            print(f"❌ 训练任务创建失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建任务请求出错: {str(e)}")
        return None

def test_associate_file_with_task(task_id: int, file_id: str):
    """测试文件与任务关联"""
    print(f"\n🔗 测试文件与任务关联")
    print("=" * 40)
    
    try:
        response = requests.post(
            f"{BASE_URL}/training/files/{task_id}/associate/{file_id}",
            json={"file_type": "train"}
        )
        
        if response.status_code == 200:
            assoc_info = response.json()
            print(f"✅ 文件关联成功!")
            print(f"   任务ID: {assoc_info['task_id']}")
            print(f"   文件ID: {assoc_info['file_id']}")
            print(f"   文件类型: {assoc_info['file_type']}")
            return True
        else:
            print(f"❌ 文件关联失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 关联请求出错: {str(e)}")
        return False

def test_get_task_files(task_id: int):
    """测试获取任务关联文件"""
    print(f"\n📋 测试获取任务关联文件 (任务ID: {task_id})")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/training/files/{task_id}/files")
        
        if response.status_code == 200:
            files_info = response.json()
            print(f"✅ 获取任务文件成功!")
            print(f"   关联文件数量: {len(files_info['files'])}")
            
            for file_assoc in files_info['files']:
                print(f"   - {file_assoc['original_filename']} ({file_assoc['file_type']})")
            return True
        else:
            print(f"❌ 获取任务文件失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 获取文件请求出错: {str(e)}")
        return False

def test_list_uploaded_files():
    """测试列出已上传文件"""
    print(f"\n📂 测试列出已上传文件")
    print("=" * 40)
    
    try:
        response = requests.get(f"{BASE_URL}/training/files/list")
        
        if response.status_code == 200:
            files = response.json()
            print(f"✅ 获取文件列表成功!")
            print(f"   文件总数: {len(files)}")
            
            for file_info in files[:3]:  # 只显示前3个
                print(f"   - {file_info['original_filename']} ({file_info['file_size']} bytes)")
            return True
        else:
            print(f"❌ 获取文件列表失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 列表请求出错: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🧪 AutoMATA 文件上传功能完整测试")
    print("=" * 50)
    
    # 1. 测试文件上传
    file_id = test_file_upload()
    if not file_id:
        print("💥 文件上传测试失败，停止测试")
        return
    
    # 2. 测试文件下载
    test_file_download(file_id)
    
    # 3. 测试获取文件信息
    test_file_info(file_id)
    
    # 4. 测试创建关联文件的任务
    task_id = test_create_training_task_with_file(file_id)
    
    # 5. 如果任务创建成功，测试文件关联功能
    if task_id:
        test_associate_file_with_task(task_id, file_id)
        test_get_task_files(task_id)
    
    # 6. 测试文件列表
    test_list_uploaded_files()
    
    print("\n" + "=" * 50)
    print("🎉 文件上传功能测试完成!")

if __name__ == "__main__":
    main()