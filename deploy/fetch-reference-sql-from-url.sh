#!/usr/bin/env bash
# 从 HTTPS（如阿里云 OSS）下载参考 SQL 包。是否下载：先查 GitHub Release 附件元数据，与本地 .reference_bundle.meta 中 stamp 比对。
# 约定：Release 更新后同步更新 OSS；附件 id|updated_at 未变则跳过整包 curl。
#
# 本地标记（在 REFERENCE_SQL_DIR 下）：
#   .reference_bundle.meta   文本，含 stamp=（GitHub 附件 id|updated_at）、bundle_sha256=（已下载整包校验）
# 兼容旧版：仅有 .reference_sql_release_stamp 单行时仍可读作 stamp。
#
# 环境变量：
#   REFERENCE_SQL_ARCHIVE_URL   必填
#   REFERENCE_GITHUB_REPO       必填
#   REFERENCE_ASSET_NAME        默认 automata-reference-sql.tar.gz
#   REFERENCE_RELEASE_TAG       默认 latest
#   REFERENCE_GITHUB_TOKEN      可选
#   REFERENCE_SQL_ARCHIVE_NAME  解压用，默认同 REFERENCE_ASSET_NAME
#   REFERENCE_SQL_DIR           默认 ./data/reference_sql
#   FORCE_REFERENCE_SQL_DOWNLOAD  设为 1 强制重下

set -euo pipefail

URL="${REFERENCE_SQL_ARCHIVE_URL:-}"
REPO="${REFERENCE_GITHUB_REPO:-}"
TAG="${REFERENCE_RELEASE_TAG:-latest}"
ASSET="${REFERENCE_ASSET_NAME:-automata-reference-sql.tar.gz}"
NAME="${REFERENCE_SQL_ARCHIVE_NAME:-${ASSET}}"
OUT="${REFERENCE_SQL_DIR:-./data/reference_sql}"
TOKEN="${REFERENCE_GITHUB_TOKEN:-}"
META="${OUT}/.reference_bundle.meta"
LEGACY_STAMP="${OUT}/.reference_sql_release_stamp"

if [[ -z "${URL}" ]]; then
  echo "[reference-data] REFERENCE_SQL_ARCHIVE_URL 未设置，跳过"
  exit 0
fi

if [[ -z "${REPO}" ]]; then
  echo "[reference-data] 错误: 须设置 REFERENCE_GITHUB_REPO 以比对 Release 附件" >&2
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

read_cached_stamp() {
  if [[ -f "${META}" ]]; then
    grep '^stamp=' "${META}" 2>/dev/null | head -1 | sed 's/^stamp=//' | tr -d '\r\n' || true
    return 0
  fi
  if [[ -f "${LEGACY_STAMP}" ]]; then
    tr -d '\n\r' < "${LEGACY_STAMP}" || true
  fi
}

write_meta() {
  local stamp="$1"
  local sha256="$2"
  mkdir -p "${OUT}"
  cat > "${META}" <<EOF
# AutoMATA reference SQL bundle cache; delete this file to force re-download
kind=github_release_asset
source=oss_url
stamp=${stamp}
bundle_sha256=${sha256}
EOF
  rm -f "${LEGACY_STAMP}" 2>/dev/null || true
}

hdr=()
if [[ -n "${TOKEN}" ]]; then
  hdr=( -H "Authorization: token ${TOKEN}" )
fi

if [[ "${TAG}" == "latest" ]]; then
  API_URL="https://api.github.com/repos/${REPO}/releases/latest"
else
  API_URL="https://api.github.com/repos/${REPO}/releases/tags/${TAG}"
fi

echo "[reference-data] 查询 Release 附件元数据: ${API_URL}"
json_file="$(mktemp)"
trap 'rm -f "${json_file}"' EXIT
http_code="$(curl -sSL -o "${json_file}" -w "%{http_code}" "${hdr[@]}" "${API_URL}")" || true

if [[ "${http_code}" == "404" ]]; then
  echo "[reference-data] 无对应 Release（404），跳过 OSS 下载"
  exit 0
fi
if [[ "${http_code}" != "200" ]]; then
  echo "[reference-data] 错误: GitHub API HTTP ${http_code}: ${API_URL}" >&2
  [[ -s "${json_file}" ]] && head -c 600 "${json_file}" >&2 && echo >&2 || true
  exit 1
fi

json="$(cat "${json_file}")"
rm -f "${json_file}"
trap - EXIT

asset_line="$(echo "${json}" | jq -r --arg n "${ASSET}" '.assets[]? | select(.name == $n) | "\(.id)|\(.updated_at)"' | head -1)"
if [[ -z "${asset_line}" || "${asset_line}" == "null|"* ]]; then
  echo "[reference-data] Release 中无附件「${ASSET}」，跳过 OSS 下载"
  exit 0
fi

stamp="${asset_line}"
cached="$(read_cached_stamp)"
if [[ "${FORCE_REFERENCE_SQL_DOWNLOAD:-}" != "1" ]] && [[ -n "${cached}" && "${cached}" == "${stamp}" ]]; then
  echo "[reference-data] .reference_bundle.meta 中 stamp 与 Release 一致，跳过 OSS 下载"
  exit 0
fi

tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT

echo "[reference-data] stamp 变化或首次部署，从 OSS 下载: ${URL}"
curl -fsSL -L "${URL}" -o "${tmp}"

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "[reference-data] 错误: 需要 sha256sum" >&2
  exit 1
fi
bundle_sha256="$(sha256sum "${tmp}" | awk '{print $1}')"

mkdir -p "${OUT}"

lower="$(echo "${NAME}" | tr '[:upper:]' '[:lower:]')"
if [[ "${lower}" == *.tar.gz || "${lower}" == *.tgz ]]; then
  echo "[reference-data] 解压 tar.gz -> ${OUT}"
  tar -xzf "${tmp}" -C "${OUT}"
elif [[ "${lower}" == *.zip ]]; then
  echo "[reference-data] 解压 zip -> ${OUT}"
  unzip -o -q "${tmp}" -d "${OUT}"
elif [[ "${lower}" == *.sql.gz ]]; then
  echo "[reference-data] 复制 ${NAME} -> ${OUT}/"
  cp -f "${tmp}" "${OUT}/${NAME}"
elif [[ "${lower}" == *.sql ]]; then
  echo "[reference-data] 复制 ${NAME} -> ${OUT}/"
  cp -f "${tmp}" "${OUT}/${NAME}"
else
  echo "[reference-data] 错误: 不支持的文件类型: ${NAME}" >&2
  exit 1
fi

write_meta "${stamp}" "${bundle_sha256}"
echo "[reference-data] 已写入 .reference_bundle.meta（stamp + bundle_sha256=${bundle_sha256}）"
echo "[reference-data] 完成。请确认 .env.prod 中 REFERENCE_DATA_SQL_DIR=/app/reference_sql 且 compose 已挂载 ./data/reference_sql"
