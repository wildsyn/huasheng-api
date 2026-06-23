# 花生 (Huasheng) API 逆向工程 & SDK 封装 — 完整报告

> 日期: 2026-06-04 ~ 2026-06-05
> 项目: huasheng-api (Python SDK) + ink-history-engine (云端部署)

---

## 一、成果总览

### 1.1 huasheng-api Python SDK

```
huasheng-api/
├── huasheng/              # SDK 核心包
│   ├── __init__.py        # 包入口, v0.1.0
│   ├── client.py          # HuashengClient — 31 个方法
│   ├── http.py            # Cookie/CSRF/Session 管理
│   ├── models.py          # 14 个数据模型
│   └── constants.py       # 50+ API 端点常量
├── docs/
│   ├── api.md             # 完整 API 参考 (~600 行)
│   ├── quickstart.md      # 快速入门
│   └── SUMMARY.md         # 本文件
├── tests/
│   ├── test_cloud_flow.py  # 纯 HTTP 测试 (preupload 已废弃)
│   └── huasheng_upload_pw.py # Playwright 浏览器上传
├── examples/
│   ├── basic_usage.py     # 全流程示例
│   └── agent_chat.py      # Agent 对话示例
├── pyproject.toml
└── README.md
```

### 1.2 全部 31 个 SDK 方法

| 分类 | 方法 | 说明 |
|------|------|------|
| 认证 | `check_login()` | Cookie 有效性检查 |
| 用户 | `get_user_info()` | 用户信息 (mid, uname, VIP, 等级) |
| | `get_vip_info()` | VIP 状态 + 花生积分 |
| | `get_user_preferences()` | 创作偏好列表 |
| | `create_preference()` | 创建创作偏好 |
| 配置 | `get_app_config()` | 音色列表/字数限制/举报标签 |
| | `get_tts_voices()` | TTS 配音音色 (分页) |
| | `get_clone_voices()` | 声音克隆列表 |
| 项目 | `create_project()` | 创建项目 (文稿/音频/音频+文案) |
| | `get_project()` | 项目详情 (含 clips) |
| | `list_projects()` | 项目列表 (分页) |
| | `wait_for_completion()` | 轮询等待生成完成 |
| 导出 | `export_video()` | 创建视频导出任务 |
| | `get_export_info()` | 查询导出进度 |
| | `wait_for_export()` | 轮询等待导出完成 |
| | `download_video()` | 下载 CDN 视频 (带 Referer) |
| | `export_and_download()` | 一键导出+下载 |
| 分镜 | `get_clip_candidates()` | 备选素材列表 |
| | `get_clip_render()` | 分镜渲染视频 URL |
| | `replace_clip_material()` | 替换分镜素材 |
| | `get_savepoints()` | 保存点/书签列表 |
| Agent | `get_chat_history()` | 对话历史 |
| | `get_chat_state()` | 对话状态 |
| | `get_chat_events_sse()` | SSE 实时事件流 |
| | `send_chat_answer()` | 回复 Agent 选项 |
| | `send_chat_message()` | 发送自由文本 |
| 便捷 | `create_and_wait()` | 一键创建+等待完成 |
| | `confirm_plan()` | 确认费用计划 |
| | `get_checkpoints()` | 检查点/版本列表 |
| | `get_project_bgms()` | 项目 BGM 列表 |
| | `save_cookies()` | Cookie 持久化 |

---

## 二、API 探索完整清单

### 2.1 全部 API 端点

| 域名 | 端点 | 方法 | 说明 |
|------|------|------|------|
| `www.huasheng.cn` | `/api/huasheng/project/create` | POST | 创建视频项目 |
| | `/api/innovideo/project/info` | GET | 项目详情 (含 clips) |
| | `/api/innovideo/project/list` | GET | 项目列表 (分页) |
| | `/api/innovideo/project/bgm/list` | GET | BGM 分类列表 |
| | `/api/innovideo/project/export/video/task` | POST | 创建视频导出 |
| | `/api/innovideo/project/export/video/info` | GET | 导出进度 + CDN URL |
| | `/api/innovideo/config` | GET | 应用全局配置 |
| | `/api/innovideo/abtest` | GET | A/B 测试配置 |
| | `/api/innovideo/material/tts/list` | GET | TTS 音色素材 |
| | `/api/innovideo/voice/clone/list` | GET | 克隆音色列表 |
| | `/api/innovideo/preupload` | GET | ⚠️ 已废弃 (500) |
| | `/api/innovideo/clip/video/edit` | POST | 替换分镜素材 |
| | `/api/innovideo/clip/similar/candidates` | GET | 相似素材候选 |
| | `/api/innovideo/clip/samesource/candidates` | GET | 同源素材候选 |
| | `/api/innovideo/clip/candidate/info` | GET | 候选素材详情 |
| | `/api/vip/info` | GET | VIP + 花生积分 |
| | `/api/huasheng/chat/run` | POST | Agent 自由文本消息 |
| | `/api/huasheng/chat/answers` | POST | Agent 选项回答 |
| | `/api/huasheng/chat/history` | GET | 对话历史 |
| | `/api/huasheng/chat/state` | GET | 对话状态 (-1=空闲) |
| | `/api/huasheng/chat/tool-cost` | GET | 工具调用成本 |
| | `/api/huasheng/chat/running/effects` | GET | 运行中效果 |
| | `/api/huasheng/clip/candidates/list` | GET | 分镜备选素材 |
| | `/api/huasheng/clip/render/query` | GET | 分镜渲染查询 |
| | `/api/huasheng/project/checkpoint/list` | GET | 检查点列表 |
| | `/api/huasheng/project/savepoint/list` | GET | 保存点列表 |
| | `/api/huasheng/project_plan/confirm` | POST | 确认费用计划 |
| | `/api/huasheng/user/preference/list` | GET | 创作偏好列表 |
| | `/api/huasheng/user/preference/create` | POST | 创建创作偏好 |
| `api.huasheng.cn` | `/x/web-interface/nav` | GET | 用户信息 + 登录态 |
| | `/x/activity_components/eva_operation/list` | GET | 运营活动/灵感 |
| `passport.huasheng.cn` | `/x/passport-login/web/qrcode/generate` | GET | 生成登录二维码 |
| | `/x/passport-login/web/qrcode/poll` | GET | 轮询扫码状态 |
| `sse.huasheng.cn` | `/api/huasheng/chat/events` | GET | SSE 实时生成流 |
| `data.huasheng.cn` | `/v2/log/web` | POST | 日志上报 (protobuf) |

### 2.2 create_project 三种模式

```python
# 模式 1: 文稿模式 (voice_type=0)
client.create_project(
    script="视频文案...",
    voice_id="5866601",       # TTS 配音 ID
)

# 模式 2: 音频模式 (voice_type=2)
client.create_project(
    audio_url="upos://bilistudioboss/xxx.mp3",
    voice_type=2,
    audio_duration=441.5,     # 音频时长 (秒)
)

# 模式 3: 音频+文案 (voice_type=2, user_script_type=1)
client.create_project(
    audio_url="upos://bilistudioboss/xxx.mp3",
    voice_type=2,
    user_script="荆轲刺秦王的完整文案...",  # 辅助转写 + 素材匹配
    user_script_type=1,       # 1=大纲/草稿, 2=逐字稿
    audio_duration=441.5,
)
```

### 2.3 视频导出 & CDN 下载

```
POST /api/innovideo/project/export/video/task
  {"id": <project_internal_id>}  → {task_id, project_hash}

GET  /api/innovideo/project/export/video/info
  ?id=&task_id=&project_hash=  → {url: "CDN URL", progress: 100}

CDN URL 特性:
  - 域名: upos-sz-mirrorcos.bilivideo.com
  - 有效期: ~24h (URL 中 deadline 参数控制)
  - 需要 Referer: https://www.huasheng.cn/
  - 不需要 Cookie
  - 过期后重新调用 export_video + wait_for_export 刷新
```

### 2.4 Agent 对话流程

```
create_project() → Agent 分析文案
    ↓
get_chat_state() → 等待 run_id 就绪
    ↓
send_chat_answer() → 回复选项 (A/B)
    或
send_chat_message() → 自由文本
    ↓
get_chat_events_sse() → 监听 SSE 实时进度
    ↓
wait_for_completion() → 轮询直到 state="项目处理完成"
```

---

## 三、云端部署方案

### 3.1 问题诊断

| 测试环境 | preupload | 上传 CDN | 创建项目 | 结果 |
|---------|-----------|---------|---------|------|
| 本地 (browser-act) | ✅ | ✅ | ✅ | 成功 |
| 云端 (纯 HTTP) | ⚠️ 500 | ❌ 403 | — | **失败** |
| 云端 (Playwright) | — | ✅ | ✅ | **成功** |

**根因**: 花生的 `preupload` API 已废弃 (返回 500)，音频上传必须通过真实浏览器完成。Alibaba Cloud 从服务器直接请求 upos CDN 会被 403 拒绝。

### 3.2 解决方案

在 Alibaba Cloud 服务器上运行 **Playwright + Chromium headless**，模拟真实浏览器上传：

```bash
# 安装（一次性）
yum install -y chromium-headless
pip install playwright

# 使用
cd /opt/wildflow/runtime/web/backend
.venv_311/bin/python3 /opt/wildflow/runtime/scripts/huasheng_upload_pw.py \
  /path/to/audio.mp3 \
  "视频文案..." \
  --sessdata "$SESSDATA" \
  --csrf "$BILI_JCT"

# 输出: {"pid": 159021072093233, "upos_url": "upos://..."}
```

### 3.3 服务器配置

| 项目 | 值 |
|------|-----|
| IP | 123.56.118.130 |
| OS | Alibaba Cloud Linux 8 (x86_64) |
| 内存 | 1.8 GB |
| Chromium | 133.0.6943.141 (yum 安装) |
| Python | 3.11 (`.venv_311`) |
| Chromium 启动参数 | `--no-sandbox --disable-dev-shm-usage --single-process` |
| 一次上传耗时 | ~28 秒 |

### 3.4 实测结果

```
时间: 2026-06-05 00:06:44
账号: B (DedeUserID: 3706947538782550)
音频: 荆轲_风萧萧兮易水寒.mp3 (2.5MB)
文案: 荆轲刺秦王 (290 字)
PID: 159021072093233
链接: https://www.huasheng.cn/video/159021072093233
耗时: 28 秒
```

---

## 四、ink-history-engine 集成建议

### 4.1 替换本地上传服务

当前 `job_manager.py` 依赖 `127.0.0.1:18720` 本地上传服务：

```python
# 旧方案 (需要本地机器运行上传服务)
local_result = await loop.run_in_executor(None, _call_local_service, ...)

# 新方案 (服务器直接跑 Playwright)
def upload_via_playwright(audio_path, script, sessdata, csrf):
    """直接调用服务器上的 Chromium 完成上传"""
    result = subprocess.run([
        sys.executable,
        "/opt/wildflow/runtime/scripts/huasheng_upload_pw.py",
        audio_path, script,
        "--sessdata", sessdata,
        "--csrf", csrf,
    ], capture_output=True, text=True, timeout=120)
    return json.loads(result.stdout)
```

### 4.2 Cookie 轮换

B 账号目前设为 `active`，A 账号 `disabled`。如需多账号轮换，在 `huasheng_bili_accounts` 表激活更多账号即可。FIFO 调度器会自动按 `daily_count` 最小优先选择。

### 4.3 每天 6 条限制

花生每天限制约 6 个项目。建议在 `job_manager.py` 中添加每日配额检查：

```python
async def check_daily_limit(db, sub_code):
    today = datetime.now(timezone.utc).date()
    count = await db.scalar(
        select(func.count()).where(
            HuashengJob.sub_code == sub_code,
            HuashengJob.created_at >= today,
        )
    )
    return count < 6  # 每天最多 6 条
```

---

## 五、文件清单

### SDK 文件

| 文件 | 说明 |
|------|------|
| `huasheng/__init__.py` | 包入口 |
| `huasheng/client.py` | 31 个 API 方法 |
| `huasheng/http.py` | HTTP/Cookie/CSRF 封装 |
| `huasheng/models.py` | Project, Clip, Voice, UserInfo 等 14 个 dataclass |
| `huasheng/constants.py` | 50+ API 端点 + 枚举常量 |
| `docs/api.md` | 完整 API 参考文档 |
| `docs/quickstart.md` | 快速入门 |
| `docs/SUMMARY.md` | 本文件 |
| `examples/basic_usage.py` | 全流程示例 |
| `examples/agent_chat.py` | Agent 交互示例 |
| `tests/test_cloud_flow.py` | 云端连通性测试 (纯 HTTP) |
| `tests/huasheng_upload_pw.py` | Playwright 浏览器上传脚本 |
| `README.md` | 项目说明 |
| `pyproject.toml` | 包配置 |
| `requirements.txt` | 依赖 |

### 服务器文件

| 路径 | 说明 |
|------|------|
| `/opt/wildflow/runtime/scripts/huasheng_upload_pw.py` | Playwright 上传脚本 |
| `/opt/wildflow/runtime/web/backend/app/services/huasheng/api_client.py` | 已有 HTTP 客户端 |
| `/opt/wildflow/runtime/web/backend/app/services/huasheng/job_manager.py` | 任务管理器 |
| `/opt/wildflow/runtime/web/backend/app/routers/huasheng.py` | 花生 API 路由 |

---

## 六、已知限制

| 限制 | 说明 |
|------|------|
| preupload 已废弃 | 必须用浏览器上传音频 |
| 每天 ~6 条 | 花生平台限制 |
| CDN URL 24h | 过期后需刷新 |
| CDN 需要 Referer | 下载时必须带 `Referer: https://www.huasheng.cn/` |
| 音色克隆未测试 | 按用户要求跳过 |
| 检查点回退未测试 | API 存在但未发现回退接口 |
| 服务器 1.8G 内存 | Chromium `--single-process` 模式 |

---

## 七、B站官方花生说明书要点

从官方说明书提取的关键功能:

- **双模成片**: 文稿生成视频 / 音频生成视频
- **Agent 对话式剪辑**: 自然语言修改分镜、素材、MG 动画
- **MG 动画**: 自动识别数据生成图表和递进动画
- **音色克隆**: 10 秒录音生成专属音色
- **多语言**: 近 10 种语言实时翻译字幕
- **不支持**: 精确控制时长、修改字幕位置、控制扣费金额
