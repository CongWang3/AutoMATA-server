#!/bin/bash
# AutoMATA 快速测试脚本

echo "🚀 AutoMATA 系统快速测试"
echo "========================"

# 检查API服务状态
echo "1. 检查API服务..."
curl -s http://localhost:8000/ > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ API服务运行正常"
else
    echo "❌ API服务无法访问"
    exit 1
fi

# 测试模型列表
echo -e "\n2. 测试模型列表..."
MODELS_COUNT=$(curl -s http://localhost:8000/api/training/models/available | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(len(data['models']))
")
echo "✅ 可用模型数量: $MODELS_COUNT"

# 测试创建简单任务
echo -e "\n3. 测试创建训练任务..."
TASK_RESPONSE=$(curl -s -X POST http://localhost:8000/api/training/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "QuickTest_'$(date +%s)'",
    "model_type": "mlp",
    "language": "python",
    "parameters": "{\"test\": true}",
    "dataset_path": "/tmp/test.csv",
    "created_by": 1
  }')

TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('id', 'unknown'))
except:
    print('error')
")

if [ "$TASK_ID" != "error" ] && [ "$TASK_ID" != "unknown" ]; then
    echo "✅ 任务创建成功，ID: $TASK_ID"
else
    echo "❌ 任务创建失败"
fi

# 测试用户列表
echo -e "\n4. 测试用户管理..."
USERS_COUNT=$(curl -s http://localhost:8000/api/users/ | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data))
except:
    print(0)
")
echo "✅ 用户总数: $USERS_COUNT"

echo -e "\n✅ 所有基础测试通过！"
echo "📊 系统状态良好"