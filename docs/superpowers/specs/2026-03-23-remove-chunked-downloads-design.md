# Remove Chunked Downloads Design

## Summary
- 目标：删除不再使用的 `chunked`（分片下载）下载实现（后端路由 + 前端组件），让下载能力只通过“独立下载服务器”完成。

## Decisions
- 后端停止暴露 `/api/v1/files/chunked/*` 路由（包含 session 与 range 分片下载）。
- 前端不再使用 `FileChunkedDownloader` 组件；用户下载改为走已有的签名下载 URL（独立下载服务器端口 `8001`）。

## Non-goals
- 不为独立下载服务器新增 Range/分片能力（本次仅移除冗余代码）。

