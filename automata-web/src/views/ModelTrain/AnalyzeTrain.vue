<template>
    <div class="automata-training-supervised">
        <!-- 监督学习训练表单 -->
        <div class="container-fluid p-4">
            <div class="row justify-content-center">
                <div class="col-12 col-lg-10">
                    <el-card class="form-card">
                        <template #header>
                            <div class="card-header">
                                <span class="title">Analyze and Train</span>
                                <el-tag type="success">Differential analysis + Supervised training</el-tag>
                            </div>
                        </template>
                        <div class="card-body p-4">
                            <form @submit.prevent="handleSubmit" class="train_form" enctype="multipart/form-data">

                                <div class="step-section mb-4">
                                    <div class="step-header d-flex justify-content-between align-items-center" style="border-bottom: none; padding-bottom: 0;">
                                        <h5 class="section-title">
                                            1. Differential analysis settings
                                            <span class="section-subtitle">Required</span>
                                        </h5>

                                        <el-button 
                                            type="primary" 
                                            size="small" 
                                            @click="downloadStrategyExample"
                                            class="example-btn"
                                            >
                                            Download Example Data
                                        </el-button>
                                    </div>
                                    <div class="row g-3 mt-2">
                                        <div class="col-md-4">
                                            <label class="form-label">Data type</label>
                                            <select class="form-select" v-model="analysisForm.dataType">
                                                <option value="read_counts">Read counts (DESeq2)</option>
                                                <option value="fpkm">FPKM (limma)</option>
                                            </select>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Gene nomenclature</label>
                                            <select class="form-select" v-model="analysisForm.geneNomenclature">
                                                <option value="symbol">Gene Symbol</option>
                                                <option value="ensembl">Ensembl ID</option>
                                                <option value="gene_id">Gene ID</option>
                                            </select>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Organism</label>
                                            <select class="form-select" v-model="analysisForm.organism">
                                                <option value="Homo_sapiens">Homo sapiens</option>
                                                <option value="Bovine">Bovine</option>
                                                <option value="Mus_musculus">Mus musculus</option>
                                                <option value="Drosophila_melanogaster">Drosophila melanogaster</option>
                                            </select>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">log2(FC) threshold</label>
                                            <input type="number" class="form-control" v-model.number="analysisForm.fc" min="0" step="0.1">
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">padj threshold</label>
                                            <input type="number" class="form-control" v-model.number="analysisForm.padj" min="0" max="1" step="0.01">
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Correction</label>
                                            <select class="form-select" v-model="analysisForm.correction">
                                                <option value="BH">BH</option>
                                                <option value="BY">BY</option>
                                                <option value="holm">holm</option>
                                                <option value="hochberg">hochberg</option>
                                                <option value="hommel">hommel</option>
                                                <option value="bonferroni">bonferroni</option>
                                                <option value="none">none</option>
                                            </select>
                                        </div>
                                        <div class="col-12">
                                            <label class="form-label">Group info (Sample / Group, tab-separated)</label>
                                            <input type="file" class="form-control"
                                                @change="handleFileUpload($event, 'groupInfo')"
                                                accept=".txt,.csv,.tsv,.xlsx,.xls" required>
                                            <div v-if="uploadProgress.groupInfo > 0 && uploadProgress.groupInfo < 100" class="mt-2">
                                                <div class="progress">
                                                    <div class="progress-bar" role="progressbar"
                                                        :style="{ width: uploadProgress.groupInfo + '%' }">
                                                        {{ uploadProgress.groupInfo }}%
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="uploadedFiles.groupInfo" class="mt-2">
                                                <span class="badge bg-success">{{ uploadedFiles.groupInfo }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 步骤 1：选择策略并上传文件 -->
                                <div class="step-section mb-4">
                                    <div class="step-header d-flex justify-content-between align-items-center" style="border-bottom: none; padding-bottom: 0;">
                                        <!-- <h5 class="step-title mb-0">
                                            <span class="step-number">1</span>
                                            选择策略并上传数据
                                        </h5> -->
                                        <h5 class="section-title">
                                            2. Select Strategy and Upload Data
                                            <span class="section-subtitle">Required</span>
                                        </h5>
                                        
                                        <!-- <el-button 
                                            type="primary" 
                                            size="small" 
                                            @click="downloadStrategyExample"
                                            class="example-btn"
                                            >
                                            Download Example Data
                                        </el-button> -->
                                    </div>
                                    <div class="strategy-options mb-4 mt-3">
                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="radio" name="strategy"
                                                id="splitStrategy" value="split" v-model="strategy"
                                                @change="handleStrategyChange" checked>
                                            <label class="form-check-label" for="splitStrategy" style="color: #606266; font-size: 14px;">
                                                Upload a dataset to conduct training/validation/testing split (Samples must match group info)
                                            </label>
                                            
                                        </div>

                                        <div class="form-check mb-3">
                                            <input class="form-check-input" type="radio" name="strategy"
                                                id="uploadStrategy" value="upload" v-model="strategy"
                                                @change="handleStrategyChange">
                                            <label class="form-check-label" for="uploadStrategy" style="color: #606266; font-size: 14px;">
                                                Upload training/validation/testing datasets respectively (Training samples must match group info)
                                            </label>
                                        </div>

                                        <div class="form-check">
                                            <input class="form-check-input" type="radio" name="strategy"
                                                id="kfoldStrategy" value="kfold" v-model="strategy"
                                                @change="handleStrategyChange">
                                            <label class="form-check-label" for="kfoldStrategy" style="color: #606266; font-size: 14px;">
                                                Upload a dataset to conduct K-Fold cross-validation (Samples must match group info)
                                            </label>
                                        </div>
                                        
                                        
                                    </div>

                                    <!-- 数据集上传区域 -->
                                    <div class="upload-section" v-if="strategy === 'split'">
                                        <div class="mb-3">
                                            <label class="form-label">Upload Dataset</label>
                                            <input type="file" class="form-control"
                                                @change="handleFileUpload($event, 'dataset')"
                                                accept=".txt,.csv,.xlsx,.xls" required>
                                          
                                            <!-- 上传进度条 -->
                                            <div v-if="uploadProgress.dataset > 0 && uploadProgress.dataset < 100"
                                                class="mt-2">
                                                <div class="progress">
                                                    <div class="progress-bar" role="progressbar"
                                                        :style="{ width: uploadProgress.dataset + '%' }">
                                                        {{ uploadProgress.dataset }}%
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="uploadedFiles.dataset" class="mt-2">
                                                <span class="badge bg-success">
                                                    <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.dataset }}
                                                </span>
                                            </div>
                                        </div>
                                        <label class="form-label">Current Ratio</label>
                                        <div class="ratio-controls d-flex align-items-center">
                                            <div class="ratio-item d-flex align-items-center me-4">
                                                <label class="ratio-label me-2">Train Set:</label>
                                                <input type="number" class="form-control ratio-input text-center"
                                                    v-model="splitRatio.train" min="1" max="10" step="1"
                                                    @input="updateRatios" style="width: 180px;">
                                            </div>
                                            <span class="ratio-separator me-4">-</span>
                                            <div class="ratio-item d-flex align-items-center me-4">
                                                <label class="ratio-label me-2">Validation Set:</label>
                                                <input type="number" class="form-control ratio-input text-center"
                                                    v-model="splitRatio.validation" min="1" max="10" step="1"
                                                    @input="updateRatios" style="width: 180px;">
                                            </div>
                                            <span class="ratio-separator me-4">-</span>
                                            <div class="ratio-item d-flex align-items-center">
                                                <label class="ratio-label me-2">Test Set:</label>
                                                <input type="number" class="form-control ratio-input text-center"
                                                    v-model="splitRatio.test" min="1" max="10" step="1" readonly
                                                    style="width: 180px; background-color: #e9ecef;">
                                            </div>
                                        </div>
                                    </div>

                                    <!-- 分别上传区域 -->
                                    <div class="upload-section" v-if="strategy === 'upload'">
                                        <div class="row g-3">
                                            <div class="col-md-4">
                                                <label class="form-label">Upload Training Set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'train')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                              
                                                <!-- 上传进度条 -->
                                                <div v-if="uploadProgress.train > 0 && uploadProgress.train < 100"
                                                    class="mt-2">
                                                    <div class="progress">
                                                        <div class="progress-bar" role="progressbar"
                                                            :style="{ width: uploadProgress.train + '%' }">
                                                            {{ uploadProgress.train }}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div v-if="uploadedFiles.train" class="mt-2">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.train
                                                        }}
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Upload Validation Set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'validation')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                               
                                                <!-- 上传进度条 -->
                                                <div v-if="uploadProgress.validation > 0 && uploadProgress.validation < 100"
                                                    class="mt-2">
                                                    <div class="progress">
                                                        <div class="progress-bar" role="progressbar"
                                                            :style="{ width: uploadProgress.validation + '%' }">
                                                            {{ uploadProgress.validation }}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div v-if="uploadedFiles.validation" class="mt-2">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check-circle me-1"></i>{{
                                                            uploadedFiles.validation }}
                                                    </span>
                                                </div>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Upload Test Set</label>
                                                <input type="file" class="form-control"
                                                    @change="handleFileUpload($event, 'test')"
                                                    accept=".txt,.csv,.xlsx,.xls" required>
                                                <!-- 上传进度条 -->
                                                <div v-if="uploadProgress.test > 0 && uploadProgress.test < 100"
                                                    class="mt-2">
                                                    <div class="progress">
                                                        <div class="progress-bar" role="progressbar"
                                                            :style="{ width: uploadProgress.test + '%' }">
                                                            {{ uploadProgress.test }}%
                                                        </div>
                                                    </div>
                                                </div>
                                                <div v-if="uploadedFiles.test" class="mt-2">
                                                    <span class="badge bg-success">
                                                        <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.test }}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <!-- K 折交叉验证区域（与 modelTrainPage.php：训练集 + K + 测试集 一致） -->
                                    <div class="upload-section" v-if="strategy === 'kfold'">
                                        <div class="mb-3">
                                            <label class="form-label">Upload Training Set</label>
                                            <input type="file" class="form-control"
                                                @change="handleFileUpload($event, 'kfoldDataset')"
                                                accept=".txt,.csv,.xlsx,.xls" required>
                                            <div v-if="uploadProgress.kfoldDataset > 0 && uploadProgress.kfoldDataset < 100"
                                                class="mt-2">
                                                <div class="progress">
                                                    <div class="progress-bar" role="progressbar"
                                                        :style="{ width: uploadProgress.kfoldDataset + '%' }">
                                                        {{ uploadProgress.kfoldDataset }}%
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="uploadedFiles.kfoldDataset" class="mt-2">
                                                <span class="badge bg-success">
                                                    <i class="fas fa-check-circle me-1"></i>{{
                                                        uploadedFiles.kfoldDataset }}
                                                </span>
                                            </div>
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">K value</label>
                                            <input type="number" class="form-control" v-model="kfoldValue" min="2"
                                                max="10" placeholder="3">
                                        </div>
                                        <div class="mb-3">
                                            <label class="form-label">Upload Testing Set</label>
                                            <input type="file" class="form-control"
                                                @change="handleFileUpload($event, 'kfoldTest')"
                                                accept=".txt,.csv,.xlsx,.xls" required>
                                            <div v-if="uploadProgress.kfoldTest > 0 && uploadProgress.kfoldTest < 100"
                                                class="mt-2">
                                                <div class="progress">
                                                    <div class="progress-bar" role="progressbar"
                                                        :style="{ width: uploadProgress.kfoldTest + '%' }">
                                                        {{ uploadProgress.kfoldTest }}%
                                                    </div>
                                                </div>
                                            </div>
                                            <div v-if="uploadedFiles.kfoldTest" class="mt-2">
                                                <span class="badge bg-success">
                                                    <i class="fas fa-check-circle me-1"></i>{{ uploadedFiles.kfoldTest }}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 步骤 2：选择模型 -->
                                <div class="step-section mb-4">
                                    <div class="step-header d-flex justify-content-between align-items-center"  style="border-bottom: none; padding-bottom: 0;">
                                        <!-- <h5 class="step-title mb-0">
                                            <span class="step-number">2</span>
                                            选择模型
                                            <span class="step-subtitle">Choose Model</span>
                                        </h5> -->
                                        <h5 class="section-title">
                                            3. Choose Model
                                            <span class="section-subtitle">Required</span>
                                        </h5>
                                    </div>

                                    <div class="model-selection mt-3">
                                        <div v-if="loadingModels" class="text-center py-4">
                                            <div class="spinner-border text-primary" role="status">
                                                <span class="visually-hidden">Loading...</span>
                                            </div>
                                            <p class="mt-2 text-muted">Loading available models…</p>
                                        </div>

                                        <div v-else class="row">
                                            <!-- <div v-if="availableModels && availableModels.length > 0">
                                                <p class="text-muted mb-3">共找到 {{ availableModels.length }} 个可用模型</p>
                                            </div>
                                            <div v-else>
                                                <p class="text-warning">暂无可用模型，请检查后端服务</p>
                                            </div> -->
                                            <div class="col-md-6 mb-3" v-for="model in availableModels" :key="model.id">
                                                <div class="model-card"
                                                    :class="{ 'selected': selectedModel === model.id }"
                                                    @click="selectModel(model.id)">
                                                    <div class="model-header">
                                                        <input class="form-check-input me-2" type="radio" name="supervised_model_type"
                                                            :id="'model_' + model.id"
                                                            :checked="selectedModel === model.id"
                                                            @change="selectModel(model.id)">
                                                        <label class="form-check-label fw-bold"
                                                            :for="'model_' + model.id">
                                                            {{ model.name }}
                                                        </label>
                                                    </div>
                                                    <div class="model-description mt-2">
                                                        <small class="text-muted">{{ model.description }}</small>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                    </div>
                                </div>

                                <!-- 步骤 3：设置训练超参数 -->
                                <div class="step-section mb-4">
                                    <!-- <h5 class="step-title">
                                        <span class="step-number">3</span>
                                        设置训练超参数
                                        <span class="step-subtitle">Set Training Hyperparameters</span>
                                    </h5> -->

                                    <h5 class="section-title">
                                        4. Set Training Hyperparameters
                                        <span class="section-subtitle">Required</span>
                                    </h5>

                                    <div class="hyperparameters-form">
                                        <div class="row g-3">
                                            <div class="col-md-4">
                                                <!-- <label class="form-label">Epoch *</label> -->
                                                <div class="form-label">Epoch *</div>
                                                <input type="number" class="form-control" id="epoch"
                                                    v-model="hyperparameters.epoch" min="1" max="1000" required>
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Learning Rate *</label>
                                                <input type="number" class="form-control" id="lr"
                                                    v-model="hyperparameters.learningRate" step="0.00001" min="0.00001"
                                                    max="1" required>
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Early Stopping Patience *</label>
                                                <input type="number" class="form-control" id="es"
                                                    v-model="hyperparameters.earlyStopping" min="1" max="100" required>
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Batch Size *</label>
                                                <input type="number" class="form-control"
                                                    v-model="hyperparameters.batchSize" min="1" max="256">
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Random Seed *</label>
                                                <input type="number" class="form-control"
                                                    v-model="hyperparameters.randomSeed" min="0" max="999999">
                                            </div>

                                            <div class="col-md-4">
                                                <label class="form-label">Label Count *</label>
                                                <input type="number" class="form-control"
                                                    v-model="hyperparameters.labelCount" min="2" max="1000">
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Loss Function *</label>
                                                <select class="form-select" v-model="hyperparameters.lossFunction">
                                                    <option value="crossentropy">CrossEntropyLoss</option>
                                                    <option value="focalloss">FocalLoss</option>
                                                    <option value="nllloss">NLLLoss</option>
                                                </select>
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Optimizer *</label>
                                                <select class="form-select" v-model="hyperparameters.optimizerFunction">
                                                    <option value="adam">Adam</option>
                                                    <option value="sgd">SGD</option>
                                                    <option value="rmsprop">RMSprop</option>
                                                </select>
                                            </div>

                                            <div class="col-md-4" v-if="modelExtraCaps.regularization">
                                                <label class="form-label">Regularization method</label>
                                                <select
                                                    class="form-select"
                                                    v-model="hyperparameters.regularizationMethod"
                                                >
                                                    <option value="">None</option>
                                                    <option value="l1">L1</option>
                                                    <option value="l2">L2</option>
                                                    <option value="maxnorm">Max norm</option>
                                                    <option value="sparsity">Sparsity</option>
                                                </select>
                                            </div>
                                            <div class="col-md-4" v-if="modelExtraCaps.regularization">
                                                <label class="form-label">Regularization weight / strength</label>
                                                <input
                                                    type="number"
                                                    class="form-control"
                                                    v-model.number="hyperparameters.regularizationWeight"
                                                    step="0.0001"
                                                    min="0"
                                                >
                                            </div>
                                            <div class="col-md-4" v-if="modelExtraCaps.dropout">
                                                <label class="form-label">Dropout rate</label>
                                                <input
                                                    type="number"
                                                    class="form-control"
                                                    v-model.number="hyperparameters.dropoutRate"
                                                    step="0.01"
                                                    min="0"
                                                    max="1"
                                                >
                                            </div>
                                            <div class="col-md-4">
                                                <label class="form-label">Feature selection method</label>
                                                <select
                                                    class="form-select"
                                                    v-model="hyperparameters.featureMethod"
                                                    :disabled="!modelExtraCaps.featureSelection"
                                                >
                                                    <option value="">None</option>
                                                    <option value="PCC">Pearson</option>
                                                    <option value="SPEARMAN">Spearman</option>
                                                    <option value="CHI2">Chi-squared</option>
                                                    <option value="RF">Random Forest</option>
                                                </select>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <!-- 通知信息 -->
                                <div class="notification-section mb-4">
                                    <h5 class="section-title">
                                        <!-- 通知信息 -->
                                        5. Notification
                                        <span class="section-subtitle">Optional</span>
                                    </h5>
                                    <div class="row g-3">
                                        <div class="col-12">
                                            <!-- <label class="form-label">Email（Optional ）</label> -->
                                            <input
                                                type="email"
                                                class="form-control"
                                                id="email"
                                                v-model="notification.email"
                                                placeholder="Email (optional, for training result notifications)"
                                            >
                                        </div>
                                    </div>
                                </div>

                                <!-- 提交按钮 -->
                                <div class="submission-section">
                                    <!-- <div class="d-grid gap-2">
                                        <button type="submit" class="btn btn-primary btn-lg"
                                            :disabled="isSubmitting || !isFormValid">
                                            <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"
                                                role="status"></span>
                                            {{ isSubmitting ? 'Submitting...' : 'Submit' }}
                                        </button>
                                        <button type="button" class="btn btn-outline-secondary" @click="resetForm">Reset</button>
                                    </div> -->
                                    <div class="d-flex justify-content-center gap-3">
                                        <el-button
                                            native-type="submit"
                                            type="primary"
                                            :loading="isSubmitting"
                                            :disabled="isSubmitting || !isFormValid"
                                            size="large"
                                            style="width: 150px;"
                                        >
                                            {{ isSubmitting ? 'Submitting...' : 'Submit' }}
                                        </el-button>
                                        <el-button @click="resetForm">Reset</el-button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </el-card>
                </div>
            </div>

            <!-- 任务结果弹窗 -->
            <el-dialog
                v-model="showResultDialog"
                width="80%"
                :close-on-click-modal="false"
                @close="handleClose"
            >
                <AnalysisResultPanel
                    v-if="currentJob"
                    :job-id="currentJob.id"
                    :status="currentJob.status"
                    :progress="currentJob.progress ?? 0"
                    analysis-type-label="Analyze and Train"
                    waiting-banner-title="Analyze and Train"
                    waiting-hint="Task is in progress, please wait"
                    :param-rows="analysisResultParamRows"
                    :result-files="analysisResultFiles"
                    :error-message="unifiedJob?.error_message || currentJob.errorMessage"
                    :show-package-download="showPackageDownloadInPanel"
                    :on-download-package="handleDownloadFromPanel"
                    result-failure-label="Analyze and Train"
                    @enrichment-followup-started="onEnrichmentFollowupStarted"
                />
                
                <template #footer>
                    <div class="dialog-footer">
                        <el-button @click="handleClose">Close and submit a new task</el-button>
                    </div>
                </template>
            </el-dialog>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { trainingApi, submitAnalysisTrain } from '@/api'
import { AnalysisAPI, type AnalysisResultFile } from '@/api/analysis'
import { WebSocketService } from '@/api/websocket'
import AnalysisResultPanel from '@/components/AnalysisResultPanel.vue'
import { buildTrainingResultParamRows } from '@/components/Training/trainingResultParams'
import { jobsApi, type UnifiedJob } from '@/api/jobs'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { getDownloadOrigin } from '@/config/deploy'

// 类型定义
interface Job {
    id: string
    name: string
    status:
        | 'Submitted'
        | 'Processing'
        | 'Completed'
        | 'Failed'
        | 'Cancelled'
        | 'PENDING'
        | 'RUNNING'
        | 'COMPLETED'
        | 'FAILED'
        | 'CANCELLED'
    progress: number
    currentStep?: string   // 当前执行步骤
    createdAt: string
    updatedAt: string
    duration: number
    resultFile?: string    // 结果文件路径
    errorMessage?: string  // 错误信息
}

interface UploadedFileInfo {
    id: string
    file_id: string
    file_path: string
}

// <!-- 
// 审查上下文：
// - 设计意图：监督学习训练页面，支持多种策略（split/upload/kfold）和多模型选择
// - 已知局限：UI较为复杂，保留原有布局但接入了新的API调用模式
// - 业务背景：与后端 /v1/analysis-train/tasks 及统一 jobs 接口集成
// - 测试重点：确保文件上传、表单提交、WebSocket状态更新正常工作
// -->

// 路由
const router = useRouter()
// 响应式数据
const strategy = ref('split')
const selectedModel = ref('cnn') // 单选模型（默认CNN）
const kfoldValue = ref(3)

const uploadedFiles = reactive<Record<string, string>>({
    dataset: '',
    train: '',
    validation: '',
    test: '',
    kfoldDataset: '',
    kfoldTest: '',
    groupInfo: '',
})

// 文件上传进度（使用固定字段，避免 ts 推断为 possibly undefined）
interface UploadProgress {
    dataset: number
    train: number
    validation: number
    test: number
    kfoldDataset: number
    kfoldTest: number
    groupInfo: number
}

const uploadProgress = reactive<UploadProgress>({
    dataset: 0,
    train: 0,
    validation: 0,
    test: 0,
    kfoldDataset: 0,
    kfoldTest: 0,
    groupInfo: 0,
})

// 已上传文件信息
const uploadedFileInfo = reactive<Record<string, UploadedFileInfo | null>>({
    dataset: null,
    train: null,
    validation: null,
    test: null,
    kfoldDataset: null,
    kfoldTest: null,
    groupInfo: null,
})

const analysisForm = reactive({
    dataType: 'read_counts' as 'read_counts' | 'fpkm',
    geneNomenclature: 'symbol' as 'symbol' | 'ensembl' | 'gene_id',
    organism: 'Homo_sapiens',
    fc: 1,
    padj: 0.05,
    correction: 'BH',
})

const splitRatio = reactive({
    train: 8,
    validation: 1,
    test: 1
})

const hyperparameters = reactive({
    epoch: 20,
    learningRate: 0.001,
    earlyStopping: 10,
    batchSize: 32,
    randomSeed: 42,
    labelCount: 2,
    lossFunction: 'crossentropy',
    optimizerFunction: 'adam',
    /** 与后端 / 脚本一致：空字符串表示 None */
    regularizationMethod: '',
    regularizationWeight: 0.0,
    dropoutRate: 0.0,
    featureMethod: '',
})

/** 当前监督模型是否支持正则 / Dropout / 特征选择（与 train_model 脚本对齐） */
const modelExtraCaps = computed(() => {
    const id = selectedModel.value
    if (id === 'som') {
        return { regularization: false, dropout: false, featureSelection: true }
    }
    return { regularization: true, dropout: true, featureSelection: true }
})

const notification = reactive({
    email: ''
})

const userStore = useUserStore()
const emailTouched = ref(false) // 用户是否动过邮箱（包含清空）
const isAutoFilling = ref(false) // 程序性赋值：避免触发 emailTouched=true
const userEmailCache = ref<string>('') // 缓存登录邮箱

const programmaticSetEmail = async (nextEmail: string) => {
    isAutoFilling.value = true
    notification.email = nextEmail
    await nextTick()
    isAutoFilling.value = false
}

const tryAutoFillEmail = async () => {
    const nextEmail = userStore.userInfo?.email || ''
    userEmailCache.value = nextEmail

    if (emailTouched.value) return
    if (notification.email) return // 已有值则不再自动回填
    if (!nextEmail) return

    await programmaticSetEmail(nextEmail)
}

watch(
    () => userStore.userInfo?.email,
    async (newEmail) => {
        const nextEmail = newEmail || ''
        userEmailCache.value = nextEmail

        if (emailTouched.value) return
        if (!nextEmail) return
        if (notification.email) return

        await programmaticSetEmail(nextEmail)
    }
)

watch(
    () => notification.email,
    () => {
        if (isAutoFilling.value) return
        emailTouched.value = true
    }
)

const isSubmitting = ref(false)
const jobId = ref('')
const currentStatus = ref('')
const statusText = ref('Initializing...')
const trainingResults = ref<Record<string, any>>({})

// 可用模型 - 从API获取
const availableModels = ref<Array<{ id: string; name: string; description: string }>>([
    { id: 'cnn', name: 'CNN', description: 'Excels at extracting discriminative features from 1D signals with local patterns.' },
    { id: 'lstm', name: 'LSTM', description: 'Designed for modeling data with long-term dependencies.' },
    { id: 'rnn', name: 'RNN', description: 'Used for processing simple sequences with short-term dependencies.' },
    { id: 'mlp', name: 'MLP', description: 'General-purpose benchmark model for non-linear classification.' },
    { id: 'autoencoder', name: 'AutoEncoder', description: 'Learns robust feature representation via denoising and compression.' },
    { id: 'transformer', name: 'Transformer', description: 'Models global context using self-attention.' },
    { id: 'som', name: 'SOM', description: 'Suitable for discovering inherent cluster structures within data.' },
    { id: 'rbfn', name: 'RBFNN', description: 'Suitable for fast learning and local approximation.' },
    // { id: 'all', name: 'All', description: 'Train all models in parallel on the same data.' },
])
const loadingModels = ref(false)

// 任务状态
const showResultDialog = ref(false)
const currentJob = ref<Job | null>(null)
const unifiedJob = ref<UnifiedJob | null>(null)
const submittedInputParams = ref<Record<string, any> | null>(null)
const analysisResultFiles = ref<AnalysisResultFile[]>([])

function mergeInputParamsForDisplay(): Record<string, unknown> {
    const u = unifiedJob.value?.input_params
    const s = submittedInputParams.value
    if (u && typeof u === 'object') return u as Record<string, unknown>
    if (s) return s
    return {}
}

const analysisResultParamRows = computed(() => {
    const src = mergeInputParamsForDisplay()
    const base = buildTrainingResultParamRows(src)
    const a = (src as Record<string, unknown>).analysis as Record<string, unknown> | undefined
    if (!a || typeof a !== 'object') {
        return base.map((r) => ({ label: r.label, value: r.value }))
    }
    const extra = [
        { label: 'DE data type', value: String(a.data_type ?? '') },
        { label: 'Gene nomenclature', value: String(a.gene_nomenclature ?? '') },
        { label: 'Organism (DE)', value: String(a.organism ?? '') },
        { label: 'log2 FC threshold', value: String(a.fc ?? '') },
        { label: 'padj threshold', value: String(a.padj ?? '') },
        { label: 'Correction (DE)', value: String(a.correction ?? '') },
    ].filter((r) => r.value !== '')
    return [...base.map((r) => ({ label: r.label, value: r.value })), ...extra]
})

/** 主流程 Completed，或 GO/KEGG 进行中（仍为 Processing 但已有差异分析结果文件）时允许展示整包下载 */
const showPackageDownloadInPanel = computed(() => {
    const st = String(currentJob.value?.status || '').toLowerCase()
    if (st === 'completed') return true
    if (st === 'processing') {
        const names = analysisResultFiles.value.map((f) => f.filename.toLowerCase())
        return names.includes('select_all.txt')
    }
    return false
})

async function loadAnalysisResultFiles(jobId: string) {
    try {
        const r = await AnalysisAPI.getResult(jobId)
        const files = r.result_files || []
        analysisResultFiles.value = files.map((f) => ({
            filename: f.filename,
            format: f.format,
            url: AnalysisAPI.getResultFileUrl(jobId, f.filename),
        }))
    } catch (e) {
        console.warn('加载分析并训练结果文件列表失败:', e)
        analysisResultFiles.value = []
    }
}

// WebSocket 服务
let wsService: WebSocketService | null = null

// 任务轮询控制
let pollingInterval: ReturnType<typeof setTimeout> | null = null
/** WebSocket 高频推状态时合并刷新，避免 resultFiles 抖动导致子组件反复重绘 */
let resultFilesRefreshDebounce: ReturnType<typeof setTimeout> | null = null

function scheduleLoadAnalysisResultFiles(jobId: string) {
    if (resultFilesRefreshDebounce) clearTimeout(resultFilesRefreshDebounce)
    resultFilesRefreshDebounce = setTimeout(() => {
        resultFilesRefreshDebounce = null
        void loadAnalysisResultFiles(jobId)
    }, 1200)
}

// 计算属性
const ratioDisplay = computed(() => {
    return `${splitRatio.train}:${splitRatio.validation}:${splitRatio.test}`
})

const simplifiedRatioDisplay = computed(() => {
    // 计算最大公约数
    const gcd = (a: number, b: number): number => {
        return b === 0 ? a : gcd(b, a % b)
    }

    const total = splitRatio.train + splitRatio.validation + splitRatio.test
    if (total === 0) return '0:0:0'

    // 计算简化比例
    const trainPart = Math.round((splitRatio.train / total) * 10)
    const validationPart = Math.round((splitRatio.validation / total) * 10)
    let testPart = 10 - trainPart - validationPart

    // 确保总和为10
    if (testPart < 0) testPart = 0

    return `${trainPart}:${validationPart}:${testPart}`
})

const isFormValid = computed(() => {
    // 检查基本必填项
    const basicValid = !!selectedModel.value &&
        hyperparameters.epoch &&
        hyperparameters.learningRate &&
        hyperparameters.earlyStopping

    // 根据策略检查文件上传
    let filesValid = false
    if (strategy.value === 'split') {
        filesValid = !!uploadedFiles.dataset
    } else if (strategy.value === 'upload') {
        filesValid = !!(uploadedFiles.train && uploadedFiles.validation && uploadedFiles.test)
    } else if (strategy.value === 'kfold') {
        filesValid = !!(uploadedFiles.kfoldDataset && uploadedFiles.kfoldTest && kfoldValue.value)
    }

    const groupOk = !!uploadedFiles.groupInfo && !!uploadedFileInfo.groupInfo?.id

    return basicValid && filesValid && groupOk
})

// 方法
const handleFileUpload = async (event: Event, fileType: keyof UploadProgress) => {
    const input = event.target as HTMLInputElement
    const file = input.files?.[0]
    if (file) {
        // 检查文件格式
        const allowedExtensions = ['txt']
        const fileExtension = file.name.split('.').pop()?.toLowerCase() || ''

        if (!allowedExtensions.includes(fileExtension)) {
            ElMessage.error('Please upload a txt file with tab delimiter.')
            input.value = ''
            return
        }

        if (file.size > 100 * 1024 * 1024) {
            ElMessage.error('File size cannot exceed 100MB')
            input.value = ''
            return
        }

        try {
            // 重置进度
            uploadProgress[fileType] = 0

            // 上传文件到后端
            const fileInfo = await trainingApi.uploadFile(file, fileType, (progressEvent) => {
                if (progressEvent.total) {
                    uploadProgress[fileType] = Math.round((progressEvent.loaded * 100) / progressEvent.total)
                }
            })

            // 保存文件信息
            uploadedFileInfo[fileType] = {
                ...fileInfo,
                id: fileInfo.file_id  // 映射后端返回的 file_id 到 id
            }
            uploadedFiles[fileType] = file.name

            console.log(`Uploaded ${fileType} file:`, file.name, 'File ID:', fileInfo.file_id)
            ElMessage.success(`File "${file.name}" uploaded successfully`)

        } catch (error: any) {
            console.error('文件上传失败:', error)
            ElMessage.error('File upload failed: ' + (error.response?.data?.detail || error.message || 'Unknown error'))
            input.value = ''
        }
    }
}

const handleStrategyChange = () => {
    const preserve = new Set(['groupInfo'])
    Object.keys(uploadedFiles).forEach(key => {
        if (preserve.has(key)) return
        const k = key as keyof UploadProgress
        uploadedFiles[key] = ''
        uploadProgress[k] = 0
        uploadedFileInfo[key] = null
    })
}

const updateRatios = () => {
    const total = splitRatio.train + splitRatio.validation
    if (total <= 10) {
        splitRatio.test = 10 - total
    } else {
        // 如果总和超过10，按比例调整
        const ratioSum = splitRatio.train + splitRatio.validation
        splitRatio.train = Math.round((splitRatio.train / ratioSum) * 10)
        splitRatio.validation = 10 - splitRatio.train
        splitRatio.test = 0
    }
}

const selectModel = (modelId: string) => {
    selectedModel.value = modelId
}

const getModelName = (modelId: string) => {
    const model = availableModels.value.find(m => m.id === modelId)
    return model ? model.name : ''
}

const handleSubmit = async () => {
    isSubmitting.value = true

    try {
        // 验证表单
        if (!checkInput()) {
            isSubmitting.value = false
            return
        }

        // 构建训练参数
        const parameters: Record<string, any> = {
            strategy: strategy.value,
            epochs: hyperparameters.epoch,
            learning_rate: hyperparameters.learningRate,
            batch_size: hyperparameters.batchSize,
            seed: hyperparameters.randomSeed,
            early_stopping: hyperparameters.earlyStopping,
            label_count: hyperparameters.labelCount,
            loss_function: hyperparameters.lossFunction,
            optimizer_function: hyperparameters.optimizerFunction,
        }

        const caps = modelExtraCaps.value
        parameters.r_method = caps.regularization
            ? (hyperparameters.regularizationMethod || null)
            : null
        parameters.r_weight = caps.regularization ? hyperparameters.regularizationWeight : 0.0
        parameters.dropout_rate = caps.dropout ? hyperparameters.dropoutRate : 0.0
        parameters.feature_method = caps.featureSelection
            ? (hyperparameters.featureMethod || null)
            : null

        // 根据策略添加特定参数
        if (strategy.value === 'split') {
            parameters.split_ratio = {
                train: splitRatio.train,
                validation: splitRatio.validation,
                test: splitRatio.test
            }
        } else if (strategy.value === 'kfold') {
            parameters.kfold = kfoldValue.value
            parameters.kfold_train_dataset_file_id = uploadedFileInfo.kfoldDataset?.id
            parameters.kfold_test_dataset_file_id = uploadedFileInfo.kfoldTest?.id
        } else if (strategy.value === 'upload') {
            // 与 PHP modelTrain.php 一致：三份文件分别落盘为 _data / _val / _test
            parameters.train_dataset_file_id = uploadedFileInfo.train?.id
            parameters.validation_dataset_file_id = uploadedFileInfo.validation?.id
            parameters.test_dataset_file_id = uploadedFileInfo.test?.id
        }

        // 准备训练任务数据
        const modelType = selectedModel.value

        const trainingParams = {
            task_name: `AnalyzeTrain_${getModelName(modelType)}_${Date.now()}`,
            model_type: modelType,
            parameters: parameters,
            dataset_path: getDatasetPathWithFileIds(),
            group_info_file_id: uploadedFileInfo.groupInfo!.id,
            analysis: {
                organism: analysisForm.organism,
                data_type: analysisForm.dataType,
                gene_nomenclature: analysisForm.geneNomenclature,
                fc: analysisForm.fc,
                padj: analysisForm.padj,
                correction: analysisForm.correction,
            },
            email: notification.email || undefined,
        }
        submittedInputParams.value = {
            training_type: 'analysis_train',
            model_type: modelType,
            parameters,
            analysis: trainingParams.analysis,
            email: notification.email || undefined,
        }

        console.log('Submitting analyze-train task:', trainingParams)

        const response = await submitAnalysisTrain(trainingParams)

        jobId.value = response.job_id
        currentStatus.value = response.status
        statusText.value = 'Analyze-and-train task submitted'

        analysisResultFiles.value = []
        unifiedJob.value = null
        currentJob.value = {
            id: response.job_id,
            name: response.task_name,
            status: response.status as Job['status'],
            progress: response.progress || 0,
            currentStep: response.current_step || 'Submitted, waiting to run',
            createdAt: response.created_at,
            updatedAt: response.created_at,
            duration: 0,
            resultFile: response.result_file || undefined,
            errorMessage: response.error_message || undefined,
        }
        showResultDialog.value = true

        await refreshUnifiedJobDetail(response.job_id)

        ElMessage.success('Analyze-and-train task submitted')

        pollTaskStatus(response.job_id)

    } catch (error: any) {
        console.error('Submission error:', error)
        const errorMessage = error.response?.data?.detail || error.message || 'Submission failed'
        statusText.value = 'Submission failed: ' + errorMessage
        ElMessage.error('Submission failed: ' + errorMessage)
        showResultDialog.value = false
        currentJob.value = null
        submittedInputParams.value = null
    } finally {
        isSubmitting.value = false
    }
}

const checkInput = () => {
    // 检查邮箱格式
    const emailRegex = /^[\w\-\.]+@[a-z0-9]+(\-[a-z0-9]+)?(\.[a-z0-9]+(\-[a-z0-9]+)?)*\.[a-z]{2,4}$/i
    if (notification.email && !emailRegex.test(notification.email)) {
        ElMessage.error('Please enter a valid email address or leave it empty')
        return false
    }

    return true
}

const resetForm = () => {
    // 重置表单数据
    strategy.value = 'split'
    selectedModel.value = 'cnn'
    kfoldValue.value = 3

    // 重置文件上传状态
    Object.keys(uploadedFiles).forEach(key => {
        uploadedFiles[key] = ''
        const k = key as keyof UploadProgress
        uploadProgress[k] = 0
        uploadedFileInfo[key] = null
    })

    // 重置文件输入元素
    const fileInputs = document.querySelectorAll('input[type="file"]') as NodeListOf<HTMLInputElement>
    fileInputs.forEach(input => {
        input.value = ''
    })

    // 重置分割比例
    splitRatio.train = 8
    splitRatio.validation = 1
    splitRatio.test = 1

    analysisForm.dataType = 'read_counts'
    analysisForm.geneNomenclature = 'symbol'
    analysisForm.organism = 'Homo_sapiens'
    analysisForm.fc = 1
    analysisForm.padj = 0.05
    analysisForm.correction = 'BH'

    // 重置超参数
    hyperparameters.epoch = 20
    hyperparameters.learningRate = 0.001
    hyperparameters.earlyStopping = 10
    hyperparameters.batchSize = 32
    hyperparameters.randomSeed = 42
    hyperparameters.labelCount = 2
    hyperparameters.lossFunction = 'crossentropy'
    hyperparameters.optimizerFunction = 'adam'
    hyperparameters.regularizationMethod = ''
    hyperparameters.regularizationWeight = 0.0
    hyperparameters.dropoutRate = 0.0
    hyperparameters.featureMethod = ''

    // 重置通知设置：如果用户已清空（emailTouched=true），则保持为空
    const nextEmail = emailTouched.value ? notification.email : (userEmailCache.value || '')
    isAutoFilling.value = true
    notification.email = nextEmail
    nextTick(() => {
        isAutoFilling.value = false
    })

    // 关闭弹窗并重置状态
    showResultDialog.value = false
    jobId.value = ''
    currentStatus.value = ''
    statusText.value = 'Initializing...'
    trainingResults.value = {}
    currentJob.value = null
    unifiedJob.value = null
    analysisResultFiles.value = []

    // 停止任务轮询
    stopPolling()
}

const startNewTraining = () => {
    resetForm()
}

// 关闭弹窗并重置表单（关闭按钮、右上角×、提交新任务都调用此方法）
const handleClose = () => {
    showResultDialog.value = false
    currentJob.value = null
    unifiedJob.value = null
    submittedInputParams.value = null
    analysisResultFiles.value = []
    jobId.value = ''
    currentStatus.value = ''
    statusText.value = 'Initializing...'
    trainingResults.value = {}
    
    // 重置表单
    resetForm()
}

// 加载可用模型
const loadAvailableModels = async () => {
    // 模型列表按 PHP 页面固定，不再依赖后端返回顺序/内容
    loadingModels.value = false
}

const getDatasetPath = () => {
    if (strategy.value === 'split') {
        return uploadedFiles.dataset
    } else if (strategy.value === 'upload') {
        return `${uploadedFiles.train},${uploadedFiles.validation},${uploadedFiles.test}`
    } else if (strategy.value === 'kfold') {
        return `${uploadedFiles.kfoldDataset},${uploadedFiles.kfoldTest}`
    }
    return ''
}

// 获取包含文件ID的数据集路径（用于后端自动关联）
const getDatasetPathWithFileIds = () => {
    if (strategy.value === 'split' && uploadedFileInfo.dataset) {
        return `file://${uploadedFileInfo.dataset.id}`
    } else if (strategy.value === 'upload') {
        // 对于分别上传，返回主要训练文件ID
        if (uploadedFileInfo.train) {
            return `file://${uploadedFileInfo.train.id}`
        }
    } else if (strategy.value === 'kfold' && uploadedFileInfo.kfoldDataset) {
        return `file://${uploadedFileInfo.kfoldDataset.id}`
    }

    return getDatasetPath()
}

// 任务状态轮询（作为 WebSocket 的后备）
const pollTaskStatus = async (taskId: string) => {
    // 停止之前的轮询
    stopPolling()

    const poll = async () => {
        try {
            const task = await jobsApi.getJobDetail(taskId)
            const st = task.status
            currentStatus.value = st
            statusText.value = task.current_step || `Status: ${st}`
            
            if (currentJob.value && currentJob.value.id === taskId) {
                currentJob.value.status = st as Job['status']
                currentJob.value.progress = task.progress || 0
                if (task.current_step) {
                    currentJob.value.currentStep = task.current_step
                }
                if (task.result_file) {
                    currentJob.value.resultFile = task.result_file
                }
                if (task.error_message) {
                    currentJob.value.errorMessage = task.error_message
                }
            }

            if (st === 'Processing' || st === 'Submitted') {
                await loadAnalysisResultFiles(taskId)
            }

            if (st === 'Completed') {
                stopPolling()
                await refreshUnifiedJobDetailIfTerminal(taskId, st)
                ElMessage.success('Analyze and train finished')
            } else if (st === 'Submitted' || st === 'Processing') {
                pollingInterval = setTimeout(poll, 5000)
            } else if (st === 'Failed') {
                stopPolling()
                statusText.value = task.error_message || 'Task failed'
                await refreshUnifiedJobDetailIfTerminal(taskId, st)
                ElMessage.error(task.error_message || 'Task failed')
            } else if (st === 'Cancelled') {
                stopPolling()
                statusText.value = 'Task cancelled'
                await refreshUnifiedJobDetailIfTerminal(taskId, st)
            }
        } catch (error) {
            console.error('轮询任务状态失败:', error)
            // 出错时也停止轮询
            stopPolling()
        }
    }

    // 立即执行一次
    poll()
}

const stopPolling = () => {
    if (pollingInterval) {
        clearTimeout(pollingInterval)
        pollingInterval = null
    }
}

// <!-- 
// 审查上下文：
// - 设计意图：根据当前选择的训练策略下载相应的示例数据
// - 已知局限：对于upload策略提供压缩包下载，其他策略提供单个文件
// - 业务背景：让用户能够快速获取与所选策略匹配的示例数据
// - 测试重点：请验证不同策略下的示例数据下载功能
// -->
const downloadStrategyExample = () => {
    try {
        const fileName = 'new_analysis_train_example.zip'
        // 直接从后端暴露的 example 目录下载（避免 Vite public/example 缺失导致返回 html）
        // const downloadUrl = `http://localhost:8005/example/${fileName}`

        const link = document.createElement('a')
        // 直接使用Vite服务（因为它们在public目录下）
        const downloadUrl = '/example/new_analysis_train_example.zip'
        link.href = downloadUrl
        
        link.download = fileName
        link.target = '_blank' // 新窗口打开，避免阻塞当前页面
        link.style.display = 'none'

        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
    } catch (error: any) {
        console.error('❓️ 示例文件下载失败:', error)
        ElMessage.error(`Download failed: ${error.message || 'Unknown error'}`)
    }
}

const downloadExample = (filePath: string) => {
    try {
        const base = getDownloadOrigin()
        const downloadUrl = `${base}/example/${filePath}`
        
        // 获取文件名（从路径中提取）
        const fileName = filePath.split('/').pop() || filePath
        
        console.log(`📥 下载监督学习示例文件: ${fileName}`)
        
        // 使用 a 标签触发下载
        const link = document.createElement('a')
        link.href = downloadUrl
        link.download = fileName
        link.target = '_blank'
        link.style.display = 'none'
        
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
    } catch (error: any) {
        console.error('❓️ 监督学习示例文件下载失败:', error)
        ElMessage.error(`Download failed: ${error.message || 'Unknown error'}`)
    }
}

function isTerminalJobStatus(status: string) {
    const s = String(status || '').toUpperCase()
    return s === 'COMPLETED' || s === 'FAILED' || s === 'CANCELLED'
}

/** 继续 GO+KEGG 后主任务轮询往往已停，需重启轮询并拉取 result/ 新文件，否则结果弹窗一直 Running */
function onEnrichmentFollowupStarted(jobId: string) {
    void loadAnalysisResultFiles(jobId)
    pollTaskStatus(jobId)
}

async function refreshUnifiedJobDetail(id: string) {
    try {
        unifiedJob.value = await jobsApi.getJobDetail(id)
        const st = String(unifiedJob.value?.status || '').toLowerCase()
        // GO/KEGG 富集阶段任务多为 Processing，磁盘上 result/ 会持续新增文件；必须同步刷新列表，
        // 否则 AnalysisResultPanel 的 props.resultFiles 不更新，富集 UI 会一直停在 Running。
        if (st === 'completed' || st === 'processing' || st === 'submitted') {
            await loadAnalysisResultFiles(id)
        }
    } catch (error) {
        console.warn('获取任务详情失败:', error)
    }
}

async function refreshUnifiedJobDetailIfTerminal(id: string, status: string) {
    if (!isTerminalJobStatus(status)) return
    await refreshUnifiedJobDetail(id)
}

async function handleDownloadFromPanel() {
    const id = currentJob.value?.id
    if (!id) {
        ElMessage.warning('No job ID')
        return
    }
    try {
        const downloadUrl = await jobsApi.getDownloadUrl(id)
        window.open(downloadUrl, '_blank')
    } catch (error: any) {
        console.error('获取下载链接失败:', error)
        ElMessage.error('Failed to get download URL: ' + (error?.response?.data?.detail || error?.message || 'Unknown error'))
    }
}

// WebSocket 状态更新集成
const setupWebSocket = async () => {
    try {
        wsService = WebSocketService.getInstance()
        
        // 设置任务状态回调
        wsService.setOnTaskStatus((message: any) => {
            if (message && currentJob.value && message.job_id === currentJob.value.id) {
                // 更新当前任务状态（直接使用后端返回的状态值，不转换大小写）
                if (message.status) {
                    currentJob.value.status = message.status
                }
                if (message.progress !== undefined) {
                    currentJob.value.progress = message.progress
                }
                if (message.current_step) {
                    currentJob.value.currentStep = message.current_step
                }
                if (message.result_file) {
                    currentJob.value.resultFile = message.result_file
                }
                if (message.error_message) {
                    currentJob.value.errorMessage = message.error_message
                }

                // 主任务完成后轮询已停；继续 GO/KEGG 会再次进入 Processing，需重启轮询并刷新 result 文件列表
                if (message.status === 'Processing' || message.status === 'Submitted') {
                    scheduleLoadAnalysisResultFiles(message.job_id)
                    if (!pollingInterval) {
                        pollTaskStatus(currentJob.value.id)
                    }
                }

                // 更新状态文本
                currentStatus.value = message.status
                statusText.value = message.current_step || `Status: ${message.status}`
                
                // 处理完成或失败状态（匹配后端新状态枚举值）
                if (message.status === 'Completed') {
                    ElMessage.success(message.message || 'Analyze and train finished')
                    stopPolling() // 停止轮询
                    refreshUnifiedJobDetailIfTerminal(currentJob.value.id, message.status)
                } else if (message.status === 'Failed') {
                    ElMessage.error(message.error_message || 'Training failed')
                    stopPolling() // 停止轮询
                    refreshUnifiedJobDetailIfTerminal(currentJob.value.id, message.status)
                } else if (message.status === 'Cancelled') {
                    stopPolling()
                    refreshUnifiedJobDetailIfTerminal(currentJob.value.id, message.status)
                }
            }
        })
        
        // 连接任务状态 WebSocket
        await wsService.connectTaskStatus()
        console.log('🔌 WebSocket 已连接，用于任务状态更新')
        
    } catch (error) {
        console.warn('❗ WebSocket 连接失败，将使用轮询方式:', error)
        // WebSocket 连接失败不影响正常使用，会回退到轮询方式
    }
}

// 组件挂载时加载数据
onMounted(async () => {
    userStore.initializeFromStorage()
    loadAvailableModels()
    await setupWebSocket()
    await tryAutoFillEmail()
})

// 组件卸载时清理
onUnmounted(() => {
    stopPolling()
    if (resultFilesRefreshDebounce) {
        clearTimeout(resultFilesRefreshDebounce)
        resultFilesRefreshDebounce = null
    }
    if (wsService) {
        wsService.disconnectTaskStatus()
        wsService = null
    }
})
</script>

<style scoped>
/* 弹窗样式 */
.dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.automata-training-supervised {
    min-height: 100vh;
    background-color: #f5f7fa;
    /* 浅灰色背景 */
}

.form-card {
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    max-width: 1200px;
    margin: 0 auto;
}

.card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: white; /* 白色背景 */
    border-bottom: 1px solid #e4e7ed; /* 添加底部边框以区分内容区域 */
}

.title {
    font-size: 18px;
    font-weight: bold;
    color: #303133;
}

.card {
    border-radius: 10px;
    border: 1px solid #e0e0e0;
}

.step-section {
    margin-bottom: 2rem;
}

.step-title {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
}

.step-subtitle {
    font-size: 14px;
    color: #6c757d;
    margin-left: 12px;
    font-weight: normal;
}

.section-subtitle {
    font-size: 14px;
    color: #6c757d;
    margin-left: 12px;
    font-weight: normal;
}

.step-number {
    /* background-color: #0d6efd; */
    /* Bootstrap 主蓝色数字背景 */
    color: black;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    font-size: 1rem;
    /* font-weight: bold; */
}

.section-title {
    font-size: 1.1rem;
    font-weight: 600;
    color: #333333;
    /* 深灰色标题 */
    margin-bottom: 1rem;
}

.model-card {
    border: 2px solid #e0e0e0;
    /* 浅灰色边框 */
    border-radius: 8px;
    padding: 15px;
    cursor: pointer;
    transition: all 0.3s ease;
    height: 100%;
    background-color: #fafafa;
    /* 浅灰背景 */
}

.model-card:hover {
    border-color: #409eff;
    /* Bootstrap 主蓝色悬停边框 */
    box-shadow: 0 2px 8px rgba(13, 110, 253, 0.2);
    /* Bootstrap 主蓝色阴影 */
}

.model-card.selected {
    border-color: #409eff;
    /* Bootstrap 主蓝色选中边框 */
    background-color: rgba(13, 110, 253, 0.1);
    /* Bootstrap 主蓝色背景 */
}

.model-header {
    display: flex;
    align-items: center;
}

.model-description {
    min-height: 60px;
    color: #666666;
    /* 中灰色文字 */
}

.form-label {
    font-weight: 500;
    /* color: #444444; */
    color: #606266;
    font-size: 14px;
    /* 深灰色标签 */
}

/* Bootstrap 主蓝色主按钮 */
.btn-primary {
    /* background-color: #0d6efd; */
    border-color: #0d6efd;
    color: white;
}

.btn-primary:hover {
    background-color: #0b5ed7;
    /* 稍深的 Bootstrap 主蓝色 */
    border-color: #0b5ed7;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(13, 110, 253, 0.3);
}

/* 灰色次要按钮 */
.btn-outline-secondary {
    border-color: #cccccc;
    color: #666666;
}

.btn-outline-secondary:hover {
    background-color: #f0f0f0;
    border-color: #999999;
    color: #333333;
}

.badge.bg-success {
    background-color: #409eff;
    /* Bootstrap 主蓝色徽章 */
    font-size: 0.875rem;
}

.ratio-controls {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    align-items: center;
    padding: 15px;
    background-color: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
}

.ratio-item {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 150px;
}

.ratio-label {
    font-size: 14px;
    font-weight: 500;
    color: #495057;
    white-space: nowrap;
    margin-bottom: 0;
}

.ratio-input {
    width: 80px;
    padding: 6px 10px;
    text-align: center;
    border-radius: 4px;
}

.ratio-input:focus {
    border-color: #409eff;
    box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
}

.ratio-display {
    background-color: #f0f0f0;
    padding: 10px 15px;
    border-radius: 6px;
    border: 1px solid #dddddd;
    color: #555555;
    text-align: center;
}

.upload-section {
    background-color: #f8f8f8;
    /* 浅灰色上传区域 */
    padding: 20px;
    border-radius: 8px;
    margin-top: 15px;
    border: 1px solid #eeeeee;
}

/* All Models 卡片特殊样式 */
.all-models-card {
    background: linear-gradient(135deg, #f0f0f0 0%, #e8e8e8 100%);
    border: 2px dashed #409eff;
}

.all-models-card.selected {
    background: linear-gradient(135deg, rgba(13, 110, 253, 0.1) 0%, rgba(13, 110, 253, 0.2) 100%);
    border-style: solid;
}

.form-control,
.form-select {
    border: 1px solid #cccccc;
    background-color: white;
    color: #606266;
    font-size: 14px;
}

.form-control:focus,
.form-select:focus {
    border-color: #409eff;
    box-shadow: 0 0 0 0.1rem rgba(13, 110, 253, 0.25);
}

.form-check-input:checked {
    /* background-color: #0d6efd;
    border-color: #0d6efd; */
    background-color: #409eff;
    border-color: #409eff;
    /* font-weight: 500; */
}

/* 卡片头部样式 */
.card-header {
    /* background: linear-gradient(135deg, #0d6efd 0%, #0b5ed7 100%); */
    /* Bootstrap 主蓝色渐变 */
    border-bottom: none;
}

/* 成功状态 Bootstrap 主蓝色 */
.bg-success {
    background-color: #409eff !important;
}

.text-success {
    color: #409eff !important;
}

/* 输入框悬停效果 */
.form-control:hover,
.form-select:hover {
    border-color: #aaaaaa;
}

/* 响应式调整 */
@media (max-width: 768px) {
    .step-section {
        padding-left: 15px;
    }

    .model-card {
        margin-bottom: 15px;
    }

    .upload-section {
        padding: 15px;
    }
}

/* 新增样式 - All按钮和信息区域 */
.step-header {
    padding-bottom: 15px;
    border-bottom: 2px solid #e9ecef;
}

.all-models-info {
    border-left: 3px solid #409eff;
}

.btn-outline-primary.active {
    background-color: #409eff;
    border-color: #409eff;
    color: white;
}

.btn-outline-primary:not(.active):hover {
    background-color: #f8f9fa;
    border-color: #409eff;
    color: #409eff;
}

/* 策略选项样式 */
.strategy-options .form-check-input:checked {
    background-color: #409eff;
    border-color: #409eff;
    /* font-weight: 500; */
}

/* 步骤标题区域样式 */
.step-header {
    padding-bottom: 15px;
    border-bottom: 2px solid #e9ecef;
}
</style>