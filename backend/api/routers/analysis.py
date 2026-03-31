"""
数据分析路由：提供各种生物数据分析的API接口
"""
import re
import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Path, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Optional
from pathlib import Path as FilePath

from config.database import get_db
from api.dependencies.auth import get_current_active_user
from api.services.analysis_service import AnalysisService
from api.models.user import User
from api.schemas.analysis import (
    AnalysisResponse,
    AnalysisResultResponse,
    ComprehensiveEnrichmentRequest,
    VALID_ORGANISMS,
    VALID_KEGG_ORGANISMS,
    VALID_CORRECTION_METHODS,
    VALID_CLUSTERING_METHODS,
    VALID_PERMANOVA_METHODS,
    VALID_ANNOTATION_TYPES,
    VALID_NOMENCLATURE_TYPES
)

logger = logging.getLogger(__name__)

# Job ID 格式验证：YYYYMMDDHHMMSS_8 位随机字符
JOB_ID_PATTERN = re.compile(r'^\d{14}_[a-zA-Z0-9]{8}$')

router = APIRouter(prefix="/api/v1/analysis", tags=["数据分析"])


def validate_job_id(job_id: str) -> str:
    """验证Job ID格式"""
    if not JOB_ID_PATTERN.match(job_id):
        raise HTTPException(status_code=400, detail="Invalid task ID format")
    return job_id


# ==================== PCA 分析 ====================

@router.post("/pca", response_model=AnalysisResponse)
async def analyze_pca(
    file: UploadFile = File(..., description="数据文件"),
    confidence: float = Form(default=0.95, description="置信区间 (0-1)"),
    boundary: str = Form(default="FALSE", description="是否添加边际图 (TRUE/FALSE)"),
    permanova: str = Form(default="FALSE", description="是否进行PERMANOVA分析 (TRUE/FALSE)"),
    method: Optional[str] = Form(default=None, description="PERMANOVA分析方法"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    PCA主成分分析
    
    对表达矩阵进行主成分分析，支持置信椭圆和PERMANOVA分析。
    """
    try:
        # 验证文件类型
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        # 验证参数
        if confidence < 0 or confidence > 1:
            raise HTTPException(status_code=400, detail="Confidence interval must be between 0 and 1")
        
        if boundary not in ["TRUE", "FALSE"]:
            raise HTTPException(status_code=400, detail="boundary parameter must be TRUE or FALSE")
        
        if permanova not in ["TRUE", "FALSE"]:
            raise HTTPException(status_code=400, detail="permanova parameter must be TRUE or FALSE")
        
        if permanova == "TRUE" and method and method not in VALID_PERMANOVA_METHODS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid PERMANOVA method, supported: {', '.join(VALID_PERMANOVA_METHODS)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_pca(
            file=file,
            confidence=confidence,
            boundary=boundary,
            permanova=permanova,
            method=method,
            email=email
        )
        
        logger.info(f"PCA分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 相关性热图 ====================

@router.post("/correlation-heatmap", response_model=AnalysisResponse)
async def analyze_correlation_heatmap(
    file: UploadFile = File(..., description="数据文件"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    相关性热图分析
    
    计算样本间相关性并绘制热图。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_correlation_heatmap(file=file, email=email)
        
        logger.info(f"相关性热图分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 火山图 ====================

@router.post("/volcano", response_model=AnalysisResponse)
async def analyze_volcano(
    file: UploadFile = File(..., description="差异表达数据文件"),
    gmt_file: Optional[UploadFile] = File(default=None, description="GMT基因集文件(用于GSEA分析)"),
    gene_sig: Optional[str] = Form(default=None, description="强调的基因列表(逗号分隔)"),
    fc_thr: float = Form(default=1.0, description="log2(Fold Change)阈值"),
    padj_thr: float = Form(default=0.05, description="调整后p值阈值"),
    top: int = Form(default=10, description="标记的top基因数量"),
    top_fc_thr: float = Form(default=1.0, description="top基因的FC阈值"),
    top_padj_thr: float = Form(default=0.05, description="top基因的padj阈值"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    火山图分析
    
    绘制差异表达火山图，支持GSEA富集分析叠加。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if gmt_file and not gmt_file.filename.endswith('.gmt'):
            raise HTTPException(status_code=400, detail="Only gmt format files are supported")
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_volcano(
            file=file,
            gmt_file=gmt_file,
            gene_sig=gene_sig,
            fc_thr=fc_thr,
            padj_thr=padj_thr,
            top=top,
            top_fc_thr=top_fc_thr,
            top_padj_thr=top_padj_thr,
            email=email
        )
        
        logger.info(f"火山图分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 韦恩图 ====================

@router.post("/venn", response_model=AnalysisResponse)
async def analyze_venn(
    file: UploadFile = File(..., description="数据文件"),
    plot_type: str = Form(default="venn", description="图类型 (venn/vennpie/barplot)"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    韦恩图分析
    
    绘制集合交集韦恩图，支持多种展示类型。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        valid_plot_types = ["venn", "vennpie", "barplot"]
        if plot_type not in valid_plot_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Plot type must be: {', '.join(valid_plot_types)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_venn(file=file, plot_type=plot_type, email=email)
        
        logger.info(f"韦恩图分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 差异基因聚类热图 ====================

@router.post("/gene-cluster-heatmap", response_model=AnalysisResponse)
async def analyze_gene_cluster_heatmap(
    file: UploadFile = File(..., description="表达矩阵文件"),
    row_annotation_file: Optional[UploadFile] = File(default=None, description="行注释文件"),
    col_annotation_file: Optional[UploadFile] = File(default=None, description="列注释文件"),
    show_col_name: str = Form(default="TRUE", description="显示列名 (TRUE/FALSE)"),
    show_row_name: str = Form(default="FALSE", description="显示行名 (TRUE/FALSE)"),
    clustering_dis_row: str = Form(default="euclidean", description="行聚类距离方法"),
    clustering_dis_col: str = Form(default="euclidean", description="列聚类距离方法"),
    scale: str = Form(default="row", description="缩放方式 (row/column/none)"),
    annotation_type: str = Form(default="only_data", description="注释类型"),
    group: str = Form(default="FALSE", description="按组显示 (TRUE/FALSE)"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    差异基因聚类热图分析
    
    对差异表达基因进行层次聚类并绘制热图。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if clustering_dis_row not in VALID_CLUSTERING_METHODS:
            raise HTTPException(
                status_code=400,
                detail=f"Row clustering method must be: {', '.join(VALID_CLUSTERING_METHODS)}"
            )
        
        if clustering_dis_col not in VALID_CLUSTERING_METHODS:
            raise HTTPException(
                status_code=400,
                detail=f"Column clustering method must be: {', '.join(VALID_CLUSTERING_METHODS)}"
            )
        
        if annotation_type not in VALID_ANNOTATION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Annotation type must be: {', '.join(VALID_ANNOTATION_TYPES)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_gene_cluster_heatmap(
            file=file,
            row_annotation_file=row_annotation_file,
            col_annotation_file=col_annotation_file,
            show_col_name=show_col_name,
            show_row_name=show_row_name,
            clustering_dis_row=clustering_dis_row,
            clustering_dis_col=clustering_dis_col,
            scale=scale,
            annotation_type=annotation_type,
            group=group,
            email=email
        )
        
        logger.info(f"差异基因聚类热图分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 哑铃图 ====================

@router.post("/dumbbell", response_model=AnalysisResponse)
async def analyze_dumbbell(
    file: UploadFile = File(..., description="数据文件"),
    x_label: Optional[str] = Form(default=None, description="X轴标签"),
    mark_fams: Optional[str] = Form(default=None, description="强调的term"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    哑铃图分析
    
    绘制哑铃图展示富集分析结果。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_dumbbell(
            file=file,
            x_label=x_label,
            mark_fams=mark_fams,
            email=email
        )
        
        logger.info(f"哑铃图分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 哑铃条形图 ====================

@router.post("/dumbbell-bar", response_model=AnalysisResponse)
async def analyze_dumbbell_bar(
    file1: UploadFile = File(..., description="数据文件1"),
    file2: UploadFile = File(..., description="数据文件2"),
    x_label: Optional[str] = Form(default=None, description="X轴标签"),
    mark_fams: Optional[str] = Form(default=None, description="强调的term"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    哑铃条形图分析
    
    绘制哑铃条形组合图。
    """
    try:
        if not file1.filename or not file1.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if not file2.filename or not file2.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_dumbbell_bar(
            file1=file1,
            file2=file2,
            x_label=x_label,
            mark_fams=mark_fams,
            email=email
        )
        
        logger.info(f"哑铃条形图分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== GO富集分析 ====================

@router.post("/go-enrichment", response_model=AnalysisResponse)
async def analyze_go_enrichment(
    file: UploadFile = File(..., description="基因列表文件"),
    organism: str = Form(default="Homo_sapiens", description="物种"),
    pvalue: float = Form(default=0.05, description="p值阈值"),
    qvalue: float = Form(default=0.1, description="q值阈值"),
    plot_type: str = Form(default="bubble", description="图类型"),
    term_num: int = Form(default=10, description="显示的term数量"),
    correction: str = Form(default="BH", description="多重检验校正方法"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    GO富集分析
    
    对基因列表进行GO富集分析并可视化。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if organism not in VALID_ORGANISMS:
            raise HTTPException(
                status_code=400,
                detail=f"Supported species: {', '.join(VALID_ORGANISMS)}"
            )
        
        if correction not in VALID_CORRECTION_METHODS:
            raise HTTPException(
                status_code=400,
                detail=f"Correction method must be: {', '.join(VALID_CORRECTION_METHODS)}"
            )
        
        valid_plot_types = ["bubble", "barplot", "circle", "chord", "cluster"]
        if plot_type not in valid_plot_types:
            raise HTTPException(
                status_code=400,
                detail=f"Plot type must be: {', '.join(valid_plot_types)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_go_enrichment(
            file=file,
            organism=organism,
            pvalue=pvalue,
            qvalue=qvalue,
            plot_type=plot_type,
            term_num=term_num,
            correction=correction,
            email=email
        )
        
        logger.info(f"GO富集分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== KEGG富集分析 ====================

@router.post("/kegg-enrichment", response_model=AnalysisResponse)
async def analyze_kegg_enrichment(
    file: UploadFile = File(..., description="基因列表文件"),
    organism: str = Form(default="hsa", description="物种代码 (hsa/mmu/bos/dme)"),
    pvalue: float = Form(default=0.05, description="p值阈值"),
    qvalue: float = Form(default=0.1, description="q值阈值"),
    plot_type: str = Form(default="bubble", description="图类型"),
    term_num: int = Form(default=10, description="显示的term数量"),
    correction: str = Form(default="BH", description="多重检验校正方法"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    KEGG富集分析
    
    对基因列表进行KEGG通路富集分析并可视化。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if organism not in VALID_KEGG_ORGANISMS:
            raise HTTPException(
                status_code=400,
                detail=f"Supported species code: {', '.join(VALID_KEGG_ORGANISMS)}"
            )
        
        if correction not in VALID_CORRECTION_METHODS:
            raise HTTPException(
                status_code=400,
                detail=f"Correction method must be: {', '.join(VALID_CORRECTION_METHODS)}"
            )
        
        valid_plot_types = ["bubble", "circle", "chord", "cluster"]
        if plot_type not in valid_plot_types:
            raise HTTPException(
                status_code=400,
                detail=f"Plot type must be: {', '.join(valid_plot_types)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_kegg_enrichment(
            file=file,
            organism=organism,
            pvalue=pvalue,
            qvalue=qvalue,
            plot_type=plot_type,
            term_num=term_num,
            correction=correction,
            email=email
        )
        
        logger.info(f"KEGG富集分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== PPI分析 ====================

@router.post("/ppi", response_model=AnalysisResponse)
async def analyze_ppi(
    file: UploadFile = File(..., description="基因列表文件"),
    organism: str = Form(default="Homo_sapiens", description="物种"),
    nomenclature: str = Form(default="SYMBOL", description="命名方式 (SYMBOL/ENSEMBL/ENTREZID)"),
    threshold: float = Form(default=0.4, description="相互作用阈值"),
    plot_type: str = Form(default="network", description="图类型"),
    show_nodes: int = Form(default=50, description="显示的节点数量"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    PPI蛋白互作网络分析
    
    构建蛋白质相互作用网络并可视化。
    """
    try:
        if not file.filename or not file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        ppi_organisms = ["Homo_sapiens", "Mus_musculus", "Bos_taurus", "Drosophila_melanogaster"]
        if organism not in ppi_organisms:
            raise HTTPException(
                status_code=400,
                detail=f"Supported species: {', '.join(ppi_organisms)}"
            )
        
        if nomenclature not in VALID_NOMENCLATURE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Naming method must be: {', '.join(VALID_NOMENCLATURE_TYPES)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_ppi(
            file=file,
            organism=organism,
            nomenclature=nomenclature,
            threshold=threshold,
            plot_type=plot_type,
            show_nodes=show_nodes,
            email=email
        )
        
        logger.info(f"PPI分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 综合分析(差异表达分析) ====================

@router.post("/comprehensive", response_model=AnalysisResponse)
async def analyze_comprehensive(
    expression_file: UploadFile = File(..., description="表达矩阵文件"),
    group_file: UploadFile = File(..., description="分组信息文件"),
    organism: str = Form(default="Homo_sapiens", description="物种"),
    fc_threshold: float = Form(default=1.0, description="log2(Fold Change)阈值"),
    padj_threshold: float = Form(default=0.05, description="调整后p值阈值"),
    data_type: str = Form(default="read_counts", description="数据类型 (read_counts/fpkm)"),
    correction: str = Form(default="BH", description="多重检验校正方法"),
    email: Optional[str] = Form(default=None, description="结果通知邮箱"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    综合分析(差异表达分析)
    
    使用DESeq2或limma进行差异表达分析，生成火山图和聚类热图。
    """
    try:
        if not expression_file.filename or not expression_file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if not group_file.filename or not group_file.filename.endswith(('.txt', '.csv', '.tsv')):
            raise HTTPException(status_code=400, detail="Only txt format files are supported")
        
        if organism not in VALID_ORGANISMS:
            raise HTTPException(
                status_code=400,
                detail=f"Supported species: {', '.join(VALID_ORGANISMS)}"
            )
        
        valid_data_types = ["read_counts", "fpkm"]
        if data_type not in valid_data_types:
            raise HTTPException(
                status_code=400,
                detail=f"Data type must be: {', '.join(valid_data_types)}"
            )
        
        valid_corrections = ["BH", "BY", "holm", "hochberg", "hommel", "bonferroni", "none"]
        if correction not in valid_corrections:
            raise HTTPException(
                status_code=400,
                detail=f"Correction method must be: {', '.join(valid_corrections)}"
            )
        
        service = AnalysisService(db, current_user)
        result = await service.analyze_comprehensive(
            expression_file=expression_file,
            group_file=group_file,
            organism=organism,
            fc_threshold=fc_threshold,
            padj_threshold=padj_threshold,
            data_type=data_type,
            correction=correction,
            email=email
        )
        
        logger.info(f"综合分析任务已提交: job_id={result.job_id}, user={current_user.username}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"数据库错误：{str(e)}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"未知错误：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 综合分析：继续 GO/KEGG 富集 ====================

@router.post("/comprehensive/{job_id}/enrichment", response_model=AnalysisResponse)
async def analyze_comprehensive_enrichment(
    job_id: str = Path(..., description="综合分析任务ID"),
    req: ComprehensiveEnrichmentRequest = Body(...),  # JSON body
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    在综合分析结果基础上继续进行 GO + KEGG 富集分析（沿用同一 job_id）。
    后端串行执行：GO -> KEGG，避免并发读取 select_*.txt 引发的问题。
    """
    try:
        validate_job_id(job_id)

        if req.type_analysis not in ["up", "down", "all"]:
            raise HTTPException(status_code=400, detail="type_analysis must be up, down, all")

        if req.go_organism not in VALID_ORGANISMS:
            raise HTTPException(
                status_code=400,
                detail=f"GO species must be: {', '.join(VALID_ORGANISMS)}"
            )

        if req.kegg_organism not in VALID_KEGG_ORGANISMS:
            raise HTTPException(
                status_code=400,
                detail=f"KEGG species must be: {', '.join(VALID_KEGG_ORGANISMS)}"
            )

        if req.go_correction not in VALID_CORRECTION_METHODS:
            raise HTTPException(
                status_code=400,
                detail=f"GO correction method must be: {', '.join(VALID_CORRECTION_METHODS)}"
            )

        if req.kegg_correction not in VALID_CORRECTION_METHODS:
            raise HTTPException(
                status_code=400,
                detail=f"KEGG correction method must be: {', '.join(VALID_CORRECTION_METHODS)}"
            )

        service = AnalysisService(db, current_user)
        result = await service.analyze_comprehensive_enrichment(job_id, req)
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"综合分析继续富集失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# ==================== 获取分析结果 ====================

@router.get("/result/{job_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(
    job_id: str = Path(..., description="任务ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取分析结果
    
    获取指定任务的结果文件列表。
    """
    try:
        validate_job_id(job_id)
        
        service = AnalysisService(db, current_user)
        result = service.get_analysis_result(job_id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Getting result failed: {str(e)}")


# ==================== 下载结果文件 ====================

@router.get("/result/{job_id}/{filename}")
async def download_result_file(
    job_id: str = Path(..., description="任务ID"),
    filename: str = Path(..., description="文件名"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    下载结果文件
    
    下载指定任务的指定结果文件。
    """
    try:
        validate_job_id(job_id)
        
        # 安全验证文件名
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid file name")
        
        service = AnalysisService(db, current_user)
        file_path = service.get_result_file_path(job_id, filename)
        
        # 根据文件扩展名设置媒体类型
        media_type_map = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.svg': 'image/svg+xml',
            '.tiff': 'image/tiff',
            '.jpeg': 'image/jpeg',
            '.jpg': 'image/jpeg',
            '.bmp': 'image/bmp',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.tsv': 'text/tab-separated-values'
        }
        
        suffix = file_path.suffix.lower()
        media_type = media_type_map.get(suffix, 'application/octet-stream')
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载结果文件失败：{str(e)}")
        raise HTTPException(status_code=500, detail=f"Downloading result file failed: {str(e)}")
