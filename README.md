# 花生 (Huasheng) Python SDK

B站官方 AI 视频创作工具「[花生](https://www.huasheng.cn)」的非官方 Python API 封装。

本仓库是开源SDK，不等同于WildFlow内部使用的重型花生引擎，也不承担野生云的用户、计费和任务运营。
两者关系见[花生能力规划](https://github.com/wildsyn/wildflow/blob/main/docs/planning/huasheng/README.md)。

## 花生是什么？

花生是 B站于 2025 年底推出的 AI 视频创作工具：
- **输入文案 → AI 自动生成视频** (智能素材匹配 + MG 动画 + TTS 配音)
- **Agent 对话式创作** — 通过自然语言与 AI 交互，调整分镜、素材、风格
- **音色克隆** — 上传 10 秒语音即可克隆个人音色
- **千万级素材库** — 高清视频、GIF、表情包、BGM
- **多语言翻译** — 近 10 种语言实时翻译字幕

> ⚠️ 本项目是社区开发的非官方 SDK，仅供学习和自动化用途。使用前请确认你拥有合法的花生/B站账号。

## 快速开始

### 安装

```bash
pip install -e .
# 或
pip install requests
```

### 获取 Cookie

1. 在浏览器中打开 [huasheng.cn](https://www.huasheng.cn) 并登录
2. 按 F12 → Application → Cookies → huasheng.cn
3. 复制 `SESSDATA` 和 `bili_jct` 的值

### 使用示例

```python
from huasheng import HuashengClient

# 初始化客户端
client = HuashengClient(cookies={
    "SESSDATA": "your_sessdata_here",
    "bili_jct": "your_bili_jct_here",
})

# 检查登录状态
user = client.get_user_info()
print(f"已登录: {user.uname} (Lv.{user.level})")

# 获取 VIP 信息
vip = client.get_vip_info()
print(f"花生积分: {vip.total_points}")

# 获取可用音色
voices = client.get_tts_voices()
for v in voices[:5]:
    print(f"  {v.name} — {v.tags}")

# 创建视频项目
project = client.create_project(
    script="人工智能正在改变我们的生活方式。从智能手机到自动驾驶汽车...",
    voice_id="5866601",  # 配音 ID
)

# 通过 Agent 对话创作
# 查看 Agent 的分析结果
history = client.get_chat_history(project.pid)
print(f"Agent 工作中: {history.is_working}")

# 回复 Agent 的选项
client.send_chat_answer(
    pid=project.pid,
    run_id=history.current_run_id,
    batch_id="...",  # 从 Agent 问题中提取
    answers={"question_id": {"text": "B - 素材混合MG动画"}},
)

# 发送自由文本
client.send_chat_message(project.pid, "确认，开始制作视频")

# 监听 SSE 实时事件流
for event in client.get_chat_events_sse(
    run_id="...",
    pid=project.pid,
):
    print(f"SSE: {event}")
```

## 架构

```
huasheng/
├── __init__.py      # 包入口
├── client.py        # HuashengClient — 主 API 客户端
├── http.py          # HTTP/Cookie/CSRF 管理
├── models.py        # 数据模型 (Project, UserInfo, Voice, BGM, ...)
└── constants.py     # API 端点常量
```

## API 覆盖

### 已封装的 API

| API | 方法 | 说明 |
|-----|------|------|
| 用户信息 | `client.get_user_info()` | 登录态、等级、VIP |
| VIP 积分 | `client.get_vip_info()` | 花生积分、试用次数 |
| 音色列表 | `client.get_tts_voices()` | TTS 配音音色 |
| 克隆音色 | `client.get_clone_voices()` | 声音克隆列表 |
| 应用配置 | `client.get_app_config()` | 音色/限制/标签 |
| 创建项目 | `client.create_project()` | 创建视频项目 |
| 项目详情 | `client.get_project(pid)` | 获取项目信息和进度 |
| 等待完成 | `client.wait_for_completion(pid)` | 轮询等待生成完成 |
| Agent 选项回答 | `client.send_chat_answer()` | 回复 Agent 的多选题 |
| Agent 自由消息 | `client.send_chat_message()` | 发送自定义消息 |
| Agent SSE 流 | `client.get_chat_events_sse()` | 实时监听生成事件 |
| 对话历史 | `client.get_chat_history()` | Agent 对话记录 |
| BGM 列表 | `client.get_project_bgms()` | 配乐选择 |

### 已知但未封装的 API

| API | 说明 |
|-----|------|
| QR 码登录 | 需要交互式流程 |
| 音频上传 | 需要探索文件上传格式 |
| 音色克隆 | 需要探索克隆创建 API |
| 检查点管理 | 版本回退/恢复 |

## 异步生成流程

花生是异步的：创建项目后，AI Agent 通过 SSE 流逐步生成视频。

```
create_project()
    ↓
get_chat_history()  → 查看 Agent 分析/提问
    ↓
send_chat_answer()  → 回复选项
    ↓ (或)
send_chat_message() → 自由文本交互
    ↓
get_chat_events_sse() → 监听实时生成
    ↓
wait_for_completion() → 轮询 project/info 直到完成
```

## 文档

- [API 详细文档](docs/api.md)
- [示例代码](examples/)
- [参考项目结构](https://github.com/Vespa314/bilibili-api) — 本项目参照的 B站 API 封装

## 测试分层

默认测试使用本地临时 HTTP 服务调用真实 `HuashengClient`，验证请求协议、
项目创建、导出轮询和完整字节下载；它不会访问花生生产环境：

```bash
python3 -m pytest -q
```

真实外部验收会创建项目并消耗账号配额，必须由负责人显式开启。测试通过的
标准不是拿到 CDN URL，而是完整下载文件并验证大小、SHA-256，以及 `ffprobe`
报告中的时长、音视频轨道和 MP4 格式：

```bash
HUASHENG_REAL_E2E=1 \
HUASHENG_SESSDATA='<temporary-test-cookie>' \
HUASHENG_BILI_JCT='<temporary-test-csrf>' \
HUASHENG_REAL_SCRIPT='<acceptance-script>' \
python3 -m pytest -q tests/test_e2e_real_files.py
```

不要把真实 Cookie、CSRF、输入媒体路径或下载链接提交到仓库。

## License

MIT
