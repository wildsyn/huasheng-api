# 花生 SDK — Huasheng API (Python)

> 所属伞项目：[WildFlow](../) | 🔓 开源项目

## 定位

B站花生平台非官方 Python API 薄封装。

- **已开源但暂不更新**，未来会有正式发布
- 当前主仓库的活跃开发集中在 `wildflow-huaspider/`（重型生产服务）

## 接入方式

WildFlow 花生视频制作提供三种接入方式：

| 方式 | B站账号 | 浏览器谁跑 | 适合 |
|------|---------|-----------|------|
| **① 平台账号** | WildFlow 提供（注册充值） | WildFlow 服务器 | 不想管账号，直接调 API |
| **② 自有账号** | 用户自己的 B站号（扫码绑定） | WildFlow 服务器 | 想用自己的号，但不想自己运维 |
| **③ 开源 SDK（本项目）** | 用户自己管理 | 用户自己部署 | 完全自控，不依赖 WildFlow 平台 |

> ① 和 ② 通过 WildFlow API 调用（`open.wildflow.cn`），本项目（huasheng-api）是 ③ 的 Python SDK。

## 状态

- ✅ 已发布到 GitHub（`zxdwhda/huasheng-api`）
- ⚠️ 暂不积极更新，接口可能随花生平台变化而失效
- 🔜 未来会在文档、示例、CI 等方面做正式发布

## 参考

- README: [./README.md](./README.md)
- 重型生产服务: [wildflow-huaspider/](../wildflow-huaspider/)
