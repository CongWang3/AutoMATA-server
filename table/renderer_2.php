<?php
require_once 'dataProcessor.php';

function renderOntologyTable_2($filePath, $fileName, $perPage = 15, $tableId = 1) {
    ob_start();
    ?>
    <!DOCTYPE html>
    <html>
    <head>
        <title>Ontology Data Table <?php echo $tableId; ?></title>
        <style>
            .form-container {
                margin-bottom: 20px;
                padding: 15px;
                background: #f5f5f5;
                border-radius: 4px;
                border: 1px solid #eee;
            }
            .form-container form {
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                align-items: center;
            }
            .form-container input, .form-container select {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            .form-container button {
                padding: 6px 12px;
                background: #e6e6e6;
                color: #555;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.2s;
            }
            .form-container button:hover {
                background: #d9d9d9;
            }
            .table-section {
                border: 1px solid #eee;
                padding: 15px;
                border-radius: 4px;
                margin-bottom: 40px;
            }
            .table-section h2 {
                margin-top: 0;
                color: #333;
            }
            .table-container-<?php echo $tableId; ?> {
                max-width: 1300px;
                margin: 0 auto;
            }
            .export-buttons {
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
            }
            /*.export-buttons a {*/
            /*    padding: 6px 12px;*/
            /*    background: #e6e6e6;*/
            /*    color: #555;*/
            /*    text-decoration: none;*/
            /*    border-radius: 4px;*/
            /*    font-weight: 500;*/
            /*    transition: background 0.2s;*/
            /*}*/
            /*.export-buttons a:hover {*/
            /*    background: #d9d9d9;*/
            /*}*/
            .filters {
                margin-bottom: 20px;
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                align-items: center;
            }
            .filter-group {
                display: flex;
                gap: 5px;
                align-items: center;
            }
            .filter-group label {
                font-size: 14px;
            }
            .filter-group input {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 4px;
                width: 80px;
                font-size: 14px;
            }
            .filters button {
                padding: 6px 12px;
                background: #e6e6e6;
                color: #555;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                transition: background 0.2s;
            }
            .filters button:hover {
                background: #d9d9d9;
            }
            .table-wrapper {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: thin;
                scrollbar-color: #888 #f5f5f5;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
            }
            th, td {
                padding: 10px 12px;
                text-align: left;
                border-bottom: 1px solid #eee;
                white-space: nowrap;
            }
            th {
                background: #f5f5f5;
                font-weight: 500;
                position: sticky;
                top: 0;
                z-index: 1;
            }
            tr:hover {
                background: #fafafa;
            }
            .pagination {
                margin-top: 20px;
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 8px;
            }
            .pagination a, .pagination span {
                padding: 6px 10px;
                text-decoration: none;
                color: #555;
                border-radius: 4px;
                transition: background 0.2s;
                cursor: pointer;
            }
            .pagination a:hover {
                background: #f0f0f0;
            }
            .pagination a.active {
                background: #e6e6e6;
                color: #333;
                font-weight: 500;
            }
            .pagination .nav-btn {
                background: #e6e6e6;
                color: #555;
                padding: 6px 12px;
                font-weight: 500;
            }
            .pagination .nav-btn:hover {
                background: #d9d9d9;
            }
            .page-jump input {
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
                width: 60px;
                padding: 5px;
            }
            .page-jump button {
                margin-left: 5px;
                padding: 5px 10px;
                background: #e6e6e6;
                color: #555;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
            }
            .page-jump button:hover {
                background: #d9d9d9;
            }
        </style>
    </head>
    <body>
    <div class="table-container-<?php echo $tableId; ?>" id="table-container-<?php echo $tableId; ?>">
        <div class="form-container" style="display: none">
            <form method="POST" action="">
                <input type="hidden" name="tableId" value="<?php echo $tableId; ?>">
                <label for="file-<?php echo $tableId; ?>">File Path:</label>
                <input type="text" id="file-<?php echo $tableId; ?>" name="file-<?php echo $tableId; ?>"
                       value="<?php echo htmlspecialchars($filePath); ?>" required>

                <label for="perPage-<?php echo $tableId; ?>">Per Page:</label>
                <select id="perPage-<?php echo $tableId; ?>" name="perPage-<?php echo $tableId; ?>">
                    <option value="15" <?php echo $perPage === 15 ? 'selected' : ''; ?>>15</option>
                    <option value="25" <?php echo $perPage === 25 ? 'selected' : ''; ?>>25</option>
                    <option value="35" <?php echo $perPage === 35 ? 'selected' : ''; ?>>35</option>
                </select>

                <button type="submit">Update Table <?php echo $tableId; ?></button>
            </form>
        </div>
        <div class="table-section">
<!--            <h2>Table --><?php //echo $tableId; ?><!--: --><?php //echo htmlspecialchars($filePath); ?><!--</h2>-->
            <h2>Table: <?php echo $fileName;?></h2>
            <div class="export-buttons" id="export-buttons-<?php echo $tableId; ?>"></div>
            <div class="filters" style="display: none">
                <!-- <div class="filter-group">
                    <label>zScore:</label>
                    <input type="number" id="min_zScore-<?php echo $tableId; ?>" placeholder="Min" step="any">
                    <input type="number" id="max_zScore-<?php echo $tableId; ?>" placeholder="Max" step="any">
                </div>
                <div class="filter-group">
                    <label>pvalue:</label>
                    <input type="number" id="min_pvalue-<?php echo $tableId; ?>" placeholder="Min" step="any">
                    <input type="number" id="max_pvalue-<?php echo $tableId; ?>" placeholder="Max" step="any">
                </div>
                <div class="filter-group">
                    <label>p.adjust:</label>
                    <input type="number" id="min_p.adjust-<?php echo $tableId; ?>" placeholder="Min" step="any">
                    <input type="number" id="max_p.adjust-<?php echo $tableId; ?>" placeholder="Max" step="any">
                </div>
                <div class="filter-group">
                    <label>qvalue:</label>
                    <input type="number" id="min_qvalue-<?php echo $tableId; ?>" placeholder="Min" step="any">
                    <input type="number" id="max_qvalue-<?php echo $tableId; ?>" placeholder="Max" step="any">
                </div> -->
                <div class="filter-group">
                    <label>Prediction Probability:</label>
                    <input type="number" id="min_probability-<?php echo $tableId; ?>" placeholder="Min">
                    <input type="number" id="max_probability-<?php echo $tableId; ?>" placeholder="Max">
                </div>
                <button id="apply-filters-<?php echo $tableId; ?>">Apply Filters</button>
                <button id="reset-filters-<?php echo $tableId; ?>">Reset Filters</button>
            </div>
            <div class="table-wrapper">
                <table id="data-table-<?php echo $tableId; ?>">
                    <thead>
                    <tr id="table-header-<?php echo $tableId; ?>"></tr>
                    </thead>
                    <tbody id="table-body-<?php echo $tableId; ?>"></tbody>
                </table>
            </div>
            <div class="pagination" id="pagination-<?php echo $tableId; ?>"></div>
        </div>
    </div>

    <script>
        // 确保所有表格的 JS 都在文档加载后执行
        document.addEventListener('DOMContentLoaded', function() {
            function renderDataTable(filePath, perPage, tableId) {
                let currentPage = 1;
                let currentFilters = {}; // 保存当前筛选条件

                function getFilters() {
                    return {
                        // min_zScore: document.getElementById(`min_zScore-${tableId}`).value || '',
                        // max_zScore: document.getElementById(`max_zScore-${tableId}`).value || '',
                        // min_pvalue: document.getElementById(`min_pvalue-${tableId}`).value || '',
                        // max_pvalue: document.getElementById(`max_pvalue-${tableId}`).value || '',
                        // 'min_p.adjust': document.getElementById(`min_p.adjust-${tableId}`).value || '',
                        // 'max_p.adjust': document.getElementById(`max_p.adjust-${tableId}`).value || '',
                        // min_qvalue: document.getElementById(`min_qvalue-${tableId}`).value || '',
                        // max_qvalue: document.getElementById(`max_qvalue-${tableId}`).value || '',
                        min_probability: document.getElementById(`min_probability-${tableId}`).value || '',
                        max_probability: document.getElementById(`max_probability-${tableId}`).value || ''
                    };
                }

                function resetFilters() {
                    // 清空所有输入框
                    // ['min_zScore', 'max_zScore', 'min_pvalue', 'max_pvalue', 'min_p.adjust', 'max_p.adjust',
                    //     'min_qvalue', 'max_qvalue', 'min_Count', 'max_Count'].forEach(field => {
                    //     document.getElementById(`${field}-${tableId}`).value = '';
                    // });
                    ['min_probability', 'max_probability'].forEach(field => {
                        document.getElementById(`${field}-${tableId}`).value = '';
                    });
                    currentFilters = {}; // 重置筛选条件
                    loadData(tableId, 1, false); // 重新加载原始数据
                }

                function loadData(page, applyFilters = false) {
                    if (applyFilters) {
                        currentFilters = getFilters(); // 更新筛选条件
                    }
                    const filters = currentFilters;
                    const params = new URLSearchParams({
                        ajax: 1,
                        page: page,
                        perPage: perPage,
                        file: filePath,
                        ...filters
                    });

                    fetch('table/dataProcessor_2.php?' + params.toString())
                        .then(response => response.json())
                        .then(data => {
                            if (data.error) {
                                alert(`Table ${tableId} Error: ${data.error}`);
                                console.error('AJAX Error:', data.error);
                                return;
                            }
                            updateTable(tableId, data);
                            updatePagination(tableId, data);
                            updateExportButtons(tableId);
                        })
                        .catch(error => {
                            console.error('Fetch Error for Table ' + tableId + ':', error);
                            alert('Failed to load data for Table ' + tableId + '. Check console for details.');
                        });
                }

                function updateTable(tableId, data) {
                    const thead = document.getElementById(`table-header-${tableId}`);
                    const tbody = document.getElementById(`table-body-${tableId}`);

                    if (thead.children.length === 0 && data.data.length > 0) {
                        const headers = Object.keys(data.data[0]);
                        thead.innerHTML = headers.map(header => `<th>${header}</th>`).join('');
                    }

                    tbody.innerHTML = data.data.length > 0
                        ? data.data.map(row => {
                            return '<tr>' + Object.values(row).map(value => `<td>${value}</td>`).join('') + '</tr>';
                        }).join('')
                        : '<tr><td colspan="100">No data available</td></tr>';
                }

                function updatePagination(tableId, data) {
                    const pagination = document.getElementById(`pagination-${tableId}`);
                    let html = '';

                    if (data.currentPage > 1) {
                        html += `<a class="nav-btn" onclick="loadData${tableId}(${data.currentPage - 1})">«</a>`;
                    }

                    if (data.pages <= 7) {
                        for (let i = 1; i <= data.pages; i++) {
                            html += `<a ${i === data.currentPage ? 'class="active"' : ''} onclick="loadData${tableId}(${i})">${i}</a>`;
                        }
                    } else {
                        html += `<a ${data.currentPage === 1 ? 'class="active"' : ''} onclick="loadData${tableId}(1)">1</a>`;
                        if (data.currentPage > 4) html += '<span>...</span>';

                        const start = Math.max(2, data.currentPage - 2);
                        const end = Math.min(data.pages - 1, data.currentPage + 2);

                        for (let i = start; i <= end; i++) {
                            html += `<a ${i === data.currentPage ? 'class="active"' : ''} onclick="loadData${tableId}(${i})">${i}</a>`;
                        }

                        if (data.currentPage < data.pages - 3) html += '<span>...</span>';
                        html += `<a ${data.currentPage === data.pages ? 'class="active"' : ''} onclick="loadData${tableId}(${data.pages})">${data.pages}</a>`;
                    }

                    if (data.currentPage < data.pages) {
                        html += `<a class="nav-btn" onclick="loadData${tableId}(${data.currentPage + 1})">»</a>`;
                    }

                    html += `
                            <div class="page-jump">
                                <input type="number" id="jump-page-${tableId}" min="1" max="${data.pages}" placeholder="Go to">
                                <button onclick="loadData${tableId}(document.getElementById('jump-page-${tableId}').value)">Go</button>
                            </div>
                        `;

                    pagination.innerHTML = html;
                }

                function updateExportButtons(tableId) {
                    const exportButtons = document.getElementById(`export-buttons-${tableId}`);
                    exportButtons.innerHTML = `
                        <a href="table/dataProcessor_2.php?export=csv&file=${encodeURIComponent(filePath)}" class="btn btn-primary">Download CSV</a>
                        <a href="table/dataProcessor_2.php?export=txt&file=${encodeURIComponent(filePath)}" class="btn btn-primary">Download Text</a>
                        <a href="table/dataProcessor_2.php?export=xls&file=${encodeURIComponent(filePath)}" class="btn btn-primary">Download Excel</a>
                    `;
                }

                // 初始加载（无筛选）
                loadData(tableId, 1);

                // 筛选按钮事件
                document.getElementById(`apply-filters-${tableId}`).addEventListener('click', () => {
                    loadData(tableId, 1, true); // 从第一页加载并应用筛选
                });

                // 重置按钮事件
                document.getElementById(`reset-filters-${tableId}`).addEventListener('click', () => {
                    resetFilters(); // 重置筛选并加载原始数据
                });

                // 暴露特定于每个表格的 loadData 函数
                window[`loadData${tableId}`] = loadData;
            }

            // 从函数参数获取文件路径和每页条数
            renderDataTable('<?php echo htmlspecialchars($filePath); ?>', <?php echo (int)$perPage; ?>, <?php echo $tableId; ?>);
        });
    </script>
    </body>
    </html>
    <?php
    return ob_get_clean();
}