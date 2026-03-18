"""
数据分析相关的Pydantic模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== 通用响应模型 ====================

class AnalysisResponse(BaseModel):
    """分析任务提交响应模型"""
    job_id: str
    status: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisResultFile(BaseModel):
    """分析结果文件信息"""
    filename: str
    format: str
    size: Optional[int] = None
    path: Optional[str] = None


class AnalysisResultResponse(BaseModel):
    """分析结果响应模型"""
    job_id: str
    status: str
    result_files: List[AnalysisResultFile] = []
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


# ==================== PCA 分析 ====================

class PCAAnalysisRequest(BaseModel):
    """PCA分析请求模型"""
    confidence: float = Field(default=0.95, ge=0.0, le=1.0, description="置信区间")
    boundary: str = Field(default="FALSE", description="是否添加边际图 (TRUE/FALSE)")
    permanova: str = Field(default="FALSE", description="是否进行PERMANOVA分析 (TRUE/FALSE)")
    method: Optional[str] = Field(default=None, description="PERMANOVA分析方法")
    email: Optional[str] = None


# ==================== 相关性热图 ====================

class CorrelationHeatmapRequest(BaseModel):
    """相关性热图请求模型"""
    email: Optional[str] = None


# ==================== 火山图 ====================

class VolcanoRequest(BaseModel):
    """火山图请求模型"""
    gene_sig: Optional[str] = Field(default=None, description="强调的基因列表")
    fc_thr: float = Field(default=1.0, description="log2(Fold Change)阈值")
    padj_thr: float = Field(default=0.05, description="调整后p值阈值")
    top: int = Field(default=10, description="标记的top基因数量")
    top_fc_thr: float = Field(default=1.0, description="top基因的FC阈值")
    top_padj_thr: float = Field(default=0.05, description="top基因的padj阈值")
    gsea_analysis: str = Field(default="no", description="是否进行GSEA分析 (yes/no)")
    email: Optional[str] = None


# ==================== 韦恩图 ====================

class VennRequest(BaseModel):
    """韦恩图请求模型"""
    plot_type: str = Field(default="venn", description="图类型 (venn/vennpie/barplot)")
    email: Optional[str] = None


# ==================== 差异基因聚类热图 ====================

class GeneClusterHeatmapRequest(BaseModel):
    """差异基因聚类热图请求模型"""
    show_col_name: str = Field(default="TRUE", description="显示列名 (TRUE/FALSE)")
    show_row_name: str = Field(default="FALSE", description="显示行名 (TRUE/FALSE)")
    clustering_dis_row: str = Field(default="euclidean", description="行聚类距离方法")
    clustering_dis_col: str = Field(default="euclidean", description="列聚类距离方法")
    scale: str = Field(default="row", description="缩放方式 (row/column/none)")
    annotation_type: str = Field(default="only_data", description="注释类型")
    group: str = Field(default="FALSE", description="按组显示 (TRUE/FALSE)")
    email: Optional[str] = None


# ==================== 哑铃图 ====================

class DumbbellRequest(BaseModel):
    """哑铃图请求模型"""
    x_label: Optional[str] = Field(default=None, description="X轴标签")
    mark_fams: Optional[str] = Field(default=None, description="强调的term")
    email: Optional[str] = None


# ==================== 哑铃条形图 ====================

class DumbbellBarRequest(BaseModel):
    """哑铃条形图请求模型"""
    x_label: Optional[str] = Field(default=None, description="X轴标签")
    mark_fams: Optional[str] = Field(default=None, description="强调的term")
    email: Optional[str] = None


# ==================== GO富集分析 ====================

class GOEnrichmentRequest(BaseModel):
    """GO富集分析请求模型"""
    organism: str = Field(default="Homo_sapiens", description="物种")
    pvalue: float = Field(default=0.05, description="p值阈值")
    qvalue: float = Field(default=0.1, description="q值阈值")
    plot_type: str = Field(default="bubble", description="图类型 (bubble/barplot/circle/chord/cluster)")
    term_num: int = Field(default=10, description="显示的term数量")
    correction: str = Field(default="BH", description="多重检验校正方法")
    email: Optional[str] = None


# ==================== KEGG富集分析 ====================

class KEGGEnrichmentRequest(BaseModel):
    """KEGG富集分析请求模型"""
    organism: str = Field(default="hsa", description="物种代码 (hsa/mmu/bos/dme)")
    pvalue: float = Field(default=0.05, description="p值阈值")
    qvalue: float = Field(default=0.1, description="q值阈值")
    plot_type: str = Field(default="bubble", description="图类型 (bubble/circle/chord/cluster)")
    term_num: int = Field(default=10, description="显示的term数量")
    correction: str = Field(default="BH", description="多重检验校正方法")
    email: Optional[str] = None


# ==================== PPI分析 ====================

class PPIAnalysisRequest(BaseModel):
    """PPI分析请求模型"""
    organism: str = Field(default="Homo_sapiens", description="物种")
    nomenclature: str = Field(default="SYMBOL", description="命名方式 (SYMBOL/ENSEMBL/ENTREZID)")
    threshold: float = Field(default=0.4, description="相互作用阈值")
    plot_type: str = Field(default="network", description="图类型")
    show_nodes: int = Field(default=50, description="显示的节点数量")
    email: Optional[str] = None


# ==================== 综合分析 (差异表达分析) ====================

class ComprehensiveAnalysisRequest(BaseModel):
    """综合分析(差异表达分析)请求模型"""
    organism: str = Field(default="Homo_sapiens", description="物种")
    fc_threshold: float = Field(default=1.0, description="log2(Fold Change)阈值")
    padj_threshold: float = Field(default=0.05, description="调整后p值阈值")
    data_type: str = Field(default="read_counts", description="数据类型 (read_counts/fpkm)")
    correction: str = Field(default="BH", description="多重检验校正方法")
    email: Optional[str] = None


# ==================== 分析类型枚举定义(供参考) ====================

VALID_ORGANISMS = [
    "Homo_sapiens", "Mus_musculus", "Bos_taurus", 
    "Bovine", "Drosophila_melanogaster"
]

VALID_KEGG_ORGANISMS = ["hsa", "mmu", "bos", "dme"]

VALID_CORRECTION_METHODS = [
    "BH", "BY", "holm", "hochberg", "hommel", "bonferroni", "fdr", "none"
]

VALID_CLUSTERING_METHODS = [
    "euclidean", "correlation", "maximum", "manhattan", 
    "canberra", "binary", "minkowski"
]

VALID_PERMANOVA_METHODS = [
    "bray", "manhattan", "euclidean", "canberra", "clark", "kulczynski",
    "jaccard", "gower", "altGower", "morisita", "horn", "mountford",
    "raup", "binomial", "chao", "cao", "mahalanobis", "chisq", 
    "chord", "hellinger", "aitchison", "robust.aitchison"
]

VALID_ANNOTATION_TYPES = [
    "only_data", "data_with_row_annotation", 
    "data_with_col_annotation", "data_with_row_col"
]

VALID_NOMENCLATURE_TYPES = ["SYMBOL", "ENSEMBL", "ENTREZID"]
