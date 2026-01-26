<?php include __DIR__ . '/header.php' ?>

<script type="text/javascript">

</script>




<section id="banner">
    <div class="container padding-medium-2">
        <div class="hero-content">
            <!-- <h2 class="display-2 fw-semibold">About <span class="text-primary"> Us</span></h2> -->
            <h2 class="display-2 fw-semibold">Data Analysis</span></h2>
            <nav class="breadcrumb">
                <a class="breadcrumb-item text-muted nav-link" href="#">Home</a>
                <!-- <a class="breadcrumb-item text-muted nav-link" href="index.php">Data Analysis</a> -->
                <span class="breadcrumb-item active" aria-current="page">Data Analysis</span>
            </nav>
        </div>
    </div>
</section>


<section id="service" class="padding-medium">
    <div class="container">
        <!-- <div class="text-center">
            <h2 class="display-5 fw-semibold">Why to <span class="text-primary"> choose us</span></h2>
            <p class="secondary-font">Get many features from us exactly what you are looking for.</p>
        </div> -->

        <div class="row g-md-4 mt-2">
            <div class="col-md-4 mt-4" style="position: relative;">   <!--height: 81.6px;-->
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="fluent:notepad-person-24-regular"></iconify-icon>
                    </div>
                    <a href="all_analysis.php" target="_blank">
                    <div class="ps-3">
                        <p style="font-size: 22px; font-weight: bold;">Differential Expression Flow</p>  <!--All Analysis Flow -->
                        <p style="margin-top: 10px; height: 83.2px;">Differential Expression Flow incorporates differential genes screening and enrichment analysis steps using Read Counts or FPKM data.</p>
                    </div></a>
                </div>
            </div>

            <div class="col-md-4 mt-4" style="position: relative;">   <!--height: 81.6px;-->
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="fluent:notepad-person-24-regular"></iconify-icon>
                    </div>
                    <a href="draw_cor_heatmap.php" target="_blank">
                    <div class="ps-3">
                        <p style="font-size: 22px; font-weight: bold;">Correlation Heatmap</p>
                        <p style="margin-top: 10px; height: 83.2px;">Correlation analysis mainly focuses on sample differences between groups and sample duplication within groups</p>
                    </div></a>
                </div>
            </div>
            <!-- height: 131px; position: absolute; 想着把按钮隐藏在div后面，点击div就是点击后面的button
            <div style=" width: 400px; height: 150px; padding: 50px; left: 90px; top: 20px; ">
                <button type="submit" onclick="window.open('cor_heatmap.php')" style="width: 400px; height: 150px; padding: 50px; left: 90px; top: 20px; "></button>
            </div>
            -->
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="la:certificate"></iconify-icon>
                    </div>

                    <a href="draw_PCA.php" target="_blank">
                    <div class="ps-3">
                        <p style="font-size: 22px; font-weight: bold;">Principal Component Analysis</p>
                        <p style="margin-top: 10px; height: 83.2px;">PCA can assess inter-group differences and intra-group sample duplication</p>  <!-- Ideally, inter-group samples should be dispersed and intra-group samples aggregated-->
                    </div></a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="mdi:virtual-meeting"></iconify-icon>
                    </div>
                    
                    <a href="draw_volcano.php" target="_blank">
                        <div class="ps-3">
                            <p style="font-size: 22px; font-weight: bold;">Volcano Plot with GSEA</p>
                            <p style="margin-top: 10px; height: 83.2px;">Volcano plot can quickly and intuitively identify genes with statistically significant multiplicative differences</p>  <!-- Commonly used for visualisation of transcriptome difference analysis, but can also be applied to genome, proteome, metabolome, etc.-->
                        </div>
                    </a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="mdi:school-online"></iconify-icon>
                    </div>
                    <a href="draw_venn.php" target="_blank">
                    <div class="ps-3">
                       
                        <p style="font-size: 22px; font-weight: bold;">Venn Plot</p>
                        <p style="margin-top: 10px; height: 83.2px;">Venn Plot demonstrates the intersecting and non-intersecting parts of the data, often used in genetic screening</p>
                    </div></a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="uil:notebooks"></iconify-icon>
                    </div>
                    <a href="draw_df_gene_cluster.php"  target="_blank">
                    <div class="ps-3">
                        
                        <p style="font-size: 22px; font-weight: bold;">Differential Gene Cluster Heatmap</p>  <!--差异基因聚类分析-->
                        <p style="margin-top: 10px; height: 59.2px;">Expression of differential genes in different samples</p>
                    </div></a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="uiw:global"></iconify-icon>
                    </div>
                    <a href="draw_go.php" target="_blank">
                    <div class="ps-3">
                        
                        <p  style="font-size: 22px; font-weight: bold;">GO Enrichment</p>
                        <!--GO和KEGG概念和作用：https://www.xiaohongshu.com/explore/667513f1000000001f0052cc?xsec_token=AB2Lewohknapw0xcAABp42IUN_DlKsktWrQ9q84o1wHpM=&xsec_source=pc_search&source=web_search_result_notes -->
                        <p style="margin-top: 10px; height: 83.2px;">GO Enrichment is used to determine the enrichment of a set list of genes in gene ontology</p>
                    </div></a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="uiw:global"></iconify-icon>
                    </div>
                    <a href="draw_kegg.php" target="_blank">
                    <div class="ps-3">
                       
                        <p  style="font-size: 22px; font-weight: bold;">KEGG Enrichment</p>
                        <p style="margin-top: 10px; height: 83.2px;">KEGG Enrichment annotates genes for pathways and analyses the major metabolic and signal transduction pathways</p>
                    </div></a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="uiw:global"></iconify-icon>
                    </div>
                    <a href="draw_ppi.php">
                    <div class="ps-3" target="_blank">
                        <p style="font-size: 22px; font-weight: bold;">PPI Network</p>
                        <p style="margin-top: 10px;">Protein-Protein Interaction Network is used to visualize functional relationships and interactions between proteins in a cellular context</p>
                    </div></a>
                </div>
            </div>
            <div class="col-md-4 mt-4" style="position: relative;">
                <div class="services-element p-4 rounded-3 d-flex">
                    <div>
                        <iconify-icon class="service-icon fs-1" icon="uiw:global"></iconify-icon>
                    </div>
                    <a href="draw_dumbbell_bar.php" target="_blank">
                    <div class="ps-3">
                        <!-- <h4 class="py-2 m-0">模块功能2</h4> -->
                        <p style="font-size: 22px; font-weight: bold;">Dumbbell with Bar Plot</p>
                        <p style="margin-top: 10px; height: 83.2px;">Dumbbell with Bar Plot can clearly see the differences between data</p>
                    </div></a>
                </div>
            </div>
            



        </div>
    </div>
</section>






<?php include __DIR__ . '/footer.php' ?>