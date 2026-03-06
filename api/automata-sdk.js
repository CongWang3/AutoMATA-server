/**
 * AutoMATA 训练任务管理前端SDK
 * 简化前端调用API的复杂度
 */

class AutoMATA_SDK {
  constructor(baseURL = 'http://localhost:8000/api') {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  /**
   * 通用请求方法
   */
  async _request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      method: 'GET',
      headers: { ...this.defaultHeaders },
      ...options
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`API请求失败 ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * 模型相关API
   */
  models = {
    // 获取可用模型列表
    getAvailable: () => this._request('/training/models/available'),
    
    // 根据模型类型获取描述
    getDescription: async (modelType) => {
      const models = await this.models.getAvailable();
      return models.models.find(m => m.model_type === modelType)?.description || '未知模型';
    }
  };

  /**
   * 训练任务相关API
   */
  training = {
    // 创建训练任务
    create: async (taskConfig) => {
      const taskData = {
        task_name: taskConfig.taskName,
        model_type: taskConfig.modelType,
        language: 'python',
        parameters: typeof taskConfig.parameters === 'string' 
          ? taskConfig.parameters 
          : JSON.stringify(taskConfig.parameters),
        dataset_path: taskConfig.datasetPath,
        created_by: taskConfig.userId
      };

      return this._request('/training/tasks', {
        method: 'POST',
        body: JSON.stringify(taskData)
      });
    },

    // 获取任务列表
    list: (page = 0, pageSize = 10) => {
      const params = new URLSearchParams({
        skip: page * pageSize,
        limit: pageSize
      });
      return this._request(`/training/tasks?${params}`);
    },

    // 获取单个任务详情
    get: (taskId) => this._request(`/training/tasks/${taskId}`),

    // 获取任务日志
    getLogs: (taskId) => this._request(`/training/tasks/${taskId}/logs`),

    // 监控任务状态变化
    monitorStatus: (taskId, callback, interval = 3000) => {
      let lastStatus = null;
      let polling = true;

      const checkStatus = async () => {
        if (!polling) return;
        
        try {
          const task = await this.training.get(taskId);
          const currentStatus = task.status;
          
          if (currentStatus !== lastStatus) {
            callback(currentStatus, task);
            lastStatus = currentStatus;
            
            // 任务结束时停止轮询
            if (['completed', 'failed'].includes(currentStatus)) {
              polling = false;
            }
          }
        } catch (error) {
          console.error('状态监控失败:', error);
        }
      };

      // 立即执行并开始轮询
      checkStatus();
      const intervalId = setInterval(checkStatus, interval);
      
      // 返回停止监控的方法
      return () => {
        polling = false;
        clearInterval(intervalId);
      };
    },

    // 实时监控训练日志
    monitorLogs: (taskId, callback, interval = 2000) => {
      let polling = true;
      let lastLogCount = 0;

      const checkLogs = async () => {
        if (!polling) return;
        
        try {
          const logs = await this.training.getLogs(taskId);
          const newLogs = logs.slice(lastLogCount);
          
          if (newLogs.length > 0) {
            callback(newLogs, logs);
            lastLogCount = logs.length;
          }
        } catch (error) {
          console.error('日志监控失败:', error);
        }
      };

      // 立即执行并开始轮询
      checkLogs();
      const intervalId = setInterval(checkLogs, interval);
      
      // 返回停止监控的方法
      return () => {
        polling = false;
        clearInterval(intervalId);
      };
    }
  };

  /**
   * 用户相关API
   */
  users = {
    // 创建用户
    create: (userData) => {
      return this._request('/users/', {
        method: 'POST',
        body: JSON.stringify(userData)
      });
    },

    // 获取用户列表
    list: () => this._request('/users/'),

    // 获取单个用户
    get: (userId) => this._request(`/users/${userId}`)
  };

  /**
   * 实用工具方法
   */
  utils = {
    // 等待任务完成
    waitForCompletion: async (taskId, checkInterval = 3000, timeout = 300000) => {
      return new Promise((resolve, reject) => {
        const startTime = Date.now();
        let stopMonitoring = null;

        const cleanup = () => {
          if (stopMonitoring) stopMonitoring();
        };

        stopMonitoring = this.training.monitorStatus(taskId, (status, task) => {
          // 检查超时
          if (Date.now() - startTime > timeout) {
            cleanup();
            reject(new Error('任务执行超时'));
            return;
          }

          switch (status) {
            case 'completed':
              cleanup();
              resolve(task);
              break;
            case 'failed':
              cleanup();
              reject(new Error('任务执行失败'));
              break;
          }
        }, checkInterval);

        // 设置超时清理
        setTimeout(() => {
          cleanup();
          reject(new Error('任务监控超时'));
        }, timeout);
      });
    },

    // 格式化参数对象为API所需格式
    formatParameters: (params) => {
      const mapping = {
        'batch_size': 'bs',
        'learning_rate': 'lr'
      };
      
      const formatted = {};
      Object.keys(params).forEach(key => {
        const apiKey = mapping[key] || key;
        formatted[apiKey] = params[key];
      });
      
      return formatted;
    },

    // 验证任务配置
    validateTaskConfig: (config) => {
      const required = ['taskName', 'modelType', 'userId'];
      const missing = required.filter(field => !config[field]);
      
      if (missing.length > 0) {
        throw new Error(`缺少必要参数: ${missing.join(', ')}`);
      }

      // 验证模型类型
      const validModels = ['mlp', 'cnn', 'lstm', 'rnn', 'transformer', 
                          'autoencoder', 'vae', 'som', 'rbfn', 'deepcluster', 
                          'ladder', 'pseudo'];
      
      if (!validModels.includes(config.modelType)) {
        throw new Error(`不支持的模型类型: ${config.modelType}`);
      }

      return true;
    }
  };
}

// 创建默认实例
const automata = new AutoMATA_SDK();

// 导出供模块使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AutoMATA_SDK, automata };
} else if (typeof window !== 'undefined') {
  window.AutoMATA_SDK = AutoMATA_SDK;
  window.automata = automata;
}

// Vue插件版本
if (typeof Vue !== 'undefined') {
  Vue.prototype.$automata = automata;
  
  Vue.mixin({
    methods: {
      // 快捷方法
      $createTrainingTask(config) {
        return this.$automata.training.create(config);
      },
      
      $waitForTaskCompletion(taskId) {
        return this.$automata.utils.waitForCompletion(taskId);
      },
      
      $monitorTaskStatus(taskId, callback) {
        return this.$automata.training.monitorStatus(taskId, callback);
      }
    }
  });
}

export { AutoMATA_SDK, automata };
export default automata;