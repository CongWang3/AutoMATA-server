<?php
class OntologyDataProcessor {
    private $filePath;
    private $perPage;
    private $data = [];

    public function __construct($filePath, $perPage = 15) {
        $this->filePath = $filePath;
        $this->perPage = $perPage;
        $this->parseFile();
    }

    private function parseFile() {
        if (!file_exists($this->filePath)) {
            throw new Exception("File not found: {$this->filePath}");
        }
        $lines = file($this->filePath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if (empty($lines)) {
            throw new Exception("Empty file or invalid format: {$this->filePath}");
        }

        $headers = explode("\t", trim($lines[0]));
        $data = [];
        for ($i = 1; $i < count($lines); $i++) {
            $values = explode("\t", trim($lines[$i]));
            if (count($values) !== count($headers)) {
                continue; // 跳过格式错误的行
            }
            $row = [];
            for ($j = 0; $j < count($headers); $j++) {
                $row[$headers[$j]] = $values[$j] ?? '';
            }
            $data[] = $row;
        }
        $this->data = $data;
    }

    public function getFilteredData($page, $filters = []) {
        $filteredData = $this->data;

        $numericFields = ['zScore', 'pvalue', 'p.adjust', 'qvalue', 'Count'];
        foreach ($numericFields as $field) {
            $min = isset($filters["min_$field"]) && $filters["min_$field"] !== '' ? floatval(str_replace(',', '.', $filters["min_$field"])) : null;
            $max = isset($filters["max_$field"]) && $filters["max_$field"] !== '' ? floatval(str_replace(',', '.', $filters["max_$field"])) : null;

            if ($min !== null || $max !== null) {
                $filteredData = array_filter($filteredData, function($row) use ($field, $min, $max) {
                    $field = '"' . $field . '"';
                    if (!isset($row["{$field}"]) || $row["{$field}"] === '') {
                        return false; // 跳过空值或未定义字段
                    }
                    $value = floatval(str_replace(',', '.', $row[$field]));
                    if ($min !== null && $value < $min) return false;
                    if ($max !== null && $value > $max) return false;
                    return true;
                });
            }
        }

        $total = count($filteredData);
        $offset = ($page - 1) * $this->perPage;
        $paginatedData = array_slice($filteredData, $offset, $this->perPage);

        // 临时调试日志（可删除）
        // error_log("Filtered data count: $total, Page: $page, PerPage: $this->perPage, File: $this->filePath");

        if (empty($paginatedData)) {
            return [
                'data' => [],
                'total' => $total,
                'pages' => 0,
                'currentPage' => $page
            ];
        }

        return [
            'data' => array_values($paginatedData), // 确保索引连续
            'total' => $total,
            'pages' => ceil($total / $this->perPage),
            'currentPage' => $page
        ];
    }

    public function exportData($format) {
        $headers = array_keys($this->data[0] ?? []);
        $output = fopen('php://output', 'w');

        switch ($format) {
            case 'csv':
                header('Content-Type: text/csv; charset=utf-8');
                header('Content-Disposition: attachment; filename="data.csv"');
                fputcsv($output, $headers);
                foreach ($this->data as $row) {
                    if (!empty($row)) fputcsv($output, $row);
                }
                break;
            case 'txt':
                header('Content-Type: text/plain; charset=utf-8');
                header('Content-Disposition: attachment; filename="data.txt"');
                fputs($output, implode("\t", $headers) . "\n");
                foreach ($this->data as $row) {
                    if (!empty($row)) fputs($output, implode("\t", $row) . "\n");
                }
                break;
            case 'xls':
                header('Content-Type: application/vnd.ms-excel; charset=utf-8');
                header('Content-Disposition: attachment; filename="data.xls"');
                fputs($output, implode("\t", $headers) . "\n");
                foreach ($this->data as $row) {
                    if (!empty($row)) fputs($output, implode("\t", $row) . "\n");
                }
                break;
        }

        fclose($output);
        exit;
    }
}

// AJAX 或导出处理
if (isset($_GET['ajax']) || isset($_GET['export'])) {
    header('Content-Type: application/json');
    $filePath = $_GET['file'] ?? '';
    $perPage = isset($_GET['perPage']) ? (int)$_GET['perPage'] : 15;

    if (empty($filePath)) {
        echo json_encode(['error' => 'File path is required']);
        exit;
    }

    try {
        $processor = new OntologyDataProcessor($filePath, $perPage);

        if (isset($_GET['export'])) {
            $processor->exportData($_GET['export']);
        } else {
            $page = isset($_GET['page']) ? max(1, (int)$_GET['page']) : 1;
            $filters = [
                'min_zScore' => $_GET['min_zScore'] ?? '',
                'max_zScore' => $_GET['max_zScore'] ?? '',
                'min_pvalue' => $_GET['min_pvalue'] ?? '',
                'max_pvalue' => $_GET['max_pvalue'] ?? '',
                'min_p.adjust' => $_GET['min_p.adjust'] ?? '',
                'max_p.adjust' => $_GET['max_p.adjust'] ?? '',
                'min_qvalue' => $_GET['min_qvalue'] ?? '',
                'max_qvalue' => $_GET['max_qvalue'] ?? '',
                'min_Count' => $_GET['min_Count'] ?? '',
                'max_Count' => $_GET['max_Count'] ?? ''
            ];
            $result = $processor->getFilteredData($page, $filters);
            echo json_encode($result);
        }
    } catch (Exception $e) {
        echo json_encode(['error' => $e->getMessage()]);
    }
    exit;
}