#!/usr/bin/env bash
# 从 GitHub Release 下载参考注释 SQL 压缩包，解压到 data/reference_sql。
#
# 本地标记：REFERENCE_SQL_DIR/.reference_bundle.meta
#   stamp=附件 id|updated_at（与 API 一致则跳过整包下载）
#   bundle_sha256=已下载文件的 sha256
# 兼容旧版：.reference_sql_release_stamp 单行、或 .reference_github_release_asset 仅 id（仅当能拼出当前 stamp 时有效，否则重下）
#
# 环境变量：
#   REFERENCE_GITHUB_REPO   owner/repo
#   REFERENCE_ASSET_NAME    未设置则跳过
#   REFERENCE_RELEASE_TAG   默认 latest
#   REFERENCE_SQL_DIR       默认 ./data/reference_sql
#   REFERENCE_GITHUB_TOKEN  可选
#   FORCE_REFERENCE_SQL_DOWNLOAD  设为 1 强制重下

set -euo pipefail

REPO="${REFERENCE_GITHUB_REPO:-}"
TAG="${REFERENCE_RELEASE_TAG:-latest}"
ASSET="${REFERENCE_ASSET_NAME:-}"
OUT="${REFERENCE_SQL_DIR:-./data/reference_sql}"
TOKEN="${REFERENCE_GITHUB_TOKEN:-}"
META="${OUT}/.reference_bundle.meta"
LEGACY_STAMP="${OUT}/.reference_sql_release_stamp"
LEGACY_ID="${OUT}/.reference_github_release_asset"

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

read_cached_stamp() {
  if [[ -f "${META}" ]]; then
    grep '^stamp=' "${META}" 2>/dev/null | head -1 | sed 's/^stamp=//' | tr -d '\r\n' || true
    return 0
  fi
  if [[ -f "${LEGACY_STAMP}" ]]; then
    tr -d '\n\r' < "${LEGACY_STAMP}" || true
    return 0
  fi
  # 旧脚本只存了 id，无法与 id|updated_at 比较，返回空以触发下载
  if [[ -f "${LEGACY_ID}" ]]; then
    echo ""
    return 0
  fi
}

write_meta() {
  local stamp="$1"
  local sha256="$2"
  mkdir -p "${OUT}"
  cat > "${META}" <<EOF
# AutoMATA reference SQL bundle cache; delete this file to force re-download
kind=github_release_asset
source=github_release
stamp=${stamp}
bundle_sha256=${sha256}
EOF
  rm -f "${LEGACY_STAMP}" "${LEGACY_ID}" 2>/dev/null || true
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

echo "[reference-data] 获取 Release: ${API_URL}"
json_file="$(mktemp)"
trap 'rm -f "${json_file}"' EXIT
http_code="$(curl -sSL -o "${json_file}" -w "%{http_code}" "${hdr[@]}" "${API_URL}")" || true
if [[ "${http_code}" == "404" ]]; then
  echo "[reference-data] 跳过：该 URL 返回 404（通常表示仓库还没有任何 GitHub Release，或标签「${TAG}」不存在）。"
  echo "[reference-data] 需要参考注释 SQL 时：在 ${REPO} 发布 Release，并上传附件「${ASSET}」。私有仓库请确保 PAT（如 Actions Secret GHCR_READ_TOKEN）可读 Release。"
  exit 0
fi
if [[ "${http_code}" != "200" ]]; then
  echo "[reference-data] 错误: GitHub API 返回 HTTP ${http_code}（期望 200）: ${API_URL}" >&2
  [[ -s "${json_file}" ]] && head -c 800 "${json_file}" >&2 && echo >&2 || true
  exit 1
fi
json="$(cat "${json_file}")"
rm -f "${json_file}"
trap - EXIT

stamp="$(echo "${json}" | jq -r --arg n "${ASSET}" '.assets[]? | select(.name == $n) | "\(.id)|\(.updated_at)"' | head -1)"
if [[ -z "${stamp}" || "${stamp}" == "null|"* ]]; then
  echo "[reference-data] 错误: 附件「${ASSET}」不存在于该 Release" >&2
  exit 1
fi

asset_id="${stamp%%|*}"

cached="$(read_cached_stamp)"
if [[ "${FORCE_REFERENCE_SQL_DOWNLOAD:-}" != "1" ]] && [[ -n "${cached}" && "${cached}" == "${stamp}" ]]; then
  echo "[reference-data] .reference_bundle.meta 中 stamp 与 Release 一致，跳过附件下载"
  exit 0
fi

DOWN_URL="https://api.github.com/repos/${REPO}/releases/assets/${asset_id}"
tmp="$(mktemp)"
trap 'rm -f "${tmp}"' EXIT

echo "[reference-data] 下载附件 id=${asset_id} ..."
curl -fsSL "${hdr[@]}" \
  -H "Accept: application/octet-stream" \
  "${DOWN_URL}" \
  -o "${tmp}"

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "[reference-data] 错误: 需要 sha256sum" >&2
  exit 1
fi
bundle_sha256="$(sha256sum "${tmp}" | awk '{print $1}')"

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

write_meta "${stamp}" "${bundle_sha256}"
echo "[reference-data] 已写入 .reference_bundle.meta（bundle_sha256=${bundle_sha256}）"
echo "[reference-data] 完成。请确认 .env.prod 中 REFERENCE_DATA_SQL_DIR=/app/reference_sql 且 compose 已挂载 ./data/reference_sql"
