#!/usr/bin/env bash
# 从 GitHub Release 下载参考注释 SQL 压缩包，解压到 data/reference_sql（方案 B）。
#
# 前置：在仓库发 Release，上传附件（如 automata-reference-sql.tar.gz，内含 12 张表的 .sql / .sql.gz）。
#
# 环境变量（必填其一组合）：
#   REFERENCE_GITHUB_REPO   owner/repo，默认可不传（由调用方 export）
#   REFERENCE_ASSET_NAME    Release 附件精确文件名，未设置则直接跳过（不报错）
#   REFERENCE_RELEASE_TAG   标签名；设为 latest 或未设置则使用 /releases/latest
#   REFERENCE_SQL_DIR       解压目录，默认 ./data/reference_sql
#   REFERENCE_GITHUB_TOKEN  可选；私有仓库 Release 需 PAT（read 权限即可）
#
# 支持附件类型：.tar.gz / .tgz / .zip；若为单个 .sql 或 .sql.gz 则直接复制到目标目录。

set -euo pipefail

REPO="${REFERENCE_GITHUB_REPO:-}"
TAG="${REFERENCE_RELEASE_TAG:-latest}"
ASSET="${REFERENCE_ASSET_NAME:-}"
OUT="${REFERENCE_SQL_DIR:-./data/reference_sql}"
TOKEN="${REFERENCE_GITHUB_TOKEN:-}"

if [[ -z "${ASSET}" ]]; then
  echo "[reference-data] REFERENCE_ASSET_NAME 未设置，跳过 Release 下载（若无需注释库可忽略）"
  exit 0
fi

if [[ -z "${REPO}" ]]; then
  echo "[reference-data] 错误: 请设置 REFERENCE_GITHUB_REPO=owner/repo" >&2
  exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[reference-data] 错误: 需要 curl" >&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "[reference-data] 错误: 需要 jq" >&2
  exit 1
fi

hdr=()
if [[ -n "${TOKEN}" ]]; then
  hdr=( -H "Authorization: Bearer ${TOKEN}" )
fi

if [[ "${TAG}" == "latest" ]]; then
  API_URL="https://api.github.com/repos/${REPO}/releases/latest"
else
  API_URL="https://api.github.com/repos/${REPO}/releases/tags/${TAG}"
fi

echo "[reference-data] 获取 Release: ${API_URL}"
json="$(curl -fsSL "${hdr[@]}" "${API_URL}")"

asset_id="$(echo "${json}" | jq -r --arg n "${ASSET}" '.assets[]? | select(.name == $n) | .id' | head -1)"
if [[ -z "${asset_id}" || "${asset_id}" == "null" ]]; then
  echo "[reference-data] 错误: 附件「${ASSET}」不存在于该 Release" >&2
  exit 1
fi

DOWN_URL="https://api.github.com/repos/${REPO}/releases/assets/${asset_id}"
tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT

echo "[reference-data] 下载附件 id=${asset_id} ..."
curl -fsSL "${hdr[@]}" \
  -H "Accept: application/octet-stream" \
  "${DOWN_URL}" \
  -o "${tmp}"

mkdir -p "${OUT}"

lower="$(echo "${ASSET}" | tr '[:upper:]' '[:lower:]')"
if [[ "${lower}" == *.tar.gz || "${lower}" == *.tgz ]]; then
  echo "[reference-data] 解压 tar.gz -> ${OUT}"
  tar -xzf "${tmp}" -C "${OUT}"
elif [[ "${lower}" == *.zip ]]; then
  echo "[reference-data] 解压 zip -> ${OUT}"
  unzip -o -q "${tmp}" -d "${OUT}"
elif [[ "${lower}" == *.sql.gz ]]; then
  echo "[reference-data] 复制 ${ASSET} -> ${OUT}/"
  cp -f "${tmp}" "${OUT}/${ASSET}"
elif [[ "${lower}" == *.sql ]]; then
  echo "[reference-data] 复制 ${ASSET} -> ${OUT}/"
  cp -f "${tmp}" "${OUT}/${ASSET}"
else
  echo "[reference-data] 错误: 不支持的附件类型（请使用 .tar.gz / .zip / .sql / .sql.gz）: ${ASSET}" >&2
  exit 1
fi

echo "[reference-data] 完成。请确认 .env.prod 中 REFERENCE_DATA_SQL_DIR=/app/reference_sql 且 compose 已挂载 ./data/reference_sql"
