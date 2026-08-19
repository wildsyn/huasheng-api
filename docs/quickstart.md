# 快速入门

> 本项目已停止维护，本文仅保留最后版本的历史操作说明，不建议用于新的生产系统。

## 1. 获取 Cookie

花生需要 B站登录态。在浏览器中：

1. 打开 https://www.huasheng.cn 并登录
2. F12 → Application → Cookies → huasheng.cn
3. 找到 `SESSDATA` 和 `bili_jct`，复制值

## 2. 安装

```bash
cd huasheng-api
pip install -e .
```

## 3. 第一个视频

```python
from huasheng import HuashengClient

client = HuashengClient(cookies={
    "SESSDATA": "你的SESSDATA",
    "bili_jct": "你的bili_jct",
})

# 创建视频
project = client.create_project(
    script="你的视频文案...",
    voice_id="5866601",  # 清亮男声
)

print(f"视频编辑页: https://www.huasheng.cn/video/{project.pid}")
```

## 4. 理解异步流程

花生是异步的 — 创建项目后，AI Agent 需要时间来：
1. 分析文案 → 生成需求文档（约 10-30 秒）
2. 生成分镜方案（约 20-60 秒）
3. 匹配素材 + TTS 配音 + 合成（几分钟）

```python
# 方式 1: 轮询等待
project = client.wait_for_completion(project.pid, timeout=600)
print(f"生成完成! 片段数: {len(project.clips)}")

# 方式 2: 通过 Agent SSE 流监听实时进度
history = client.get_chat_history(project.pid)
for event in client.get_chat_events_sse(history.current_run_id, project.pid):
    print(f"[{event.get('type')}] {event}")
```

## 5. 常见操作

### 查看积分

```python
vip = client.get_vip_info()
print(f"剩余积分: {vip.total_points}")
```

### 切换音色

```python
voices = client.get_tts_voices()
for v in voices:
    print(f"[{v.id}] {v.name} — {v.tags}")
```

### 与 Agent 交互

```python
# 回复选项
client.send_chat_answer(
    pid=project.pid,
    run_id=history.current_run_id,
    batch_id="xxx",
    answers={"q_id": {"text": "B - 素材混合MG动画"}},
)

# 或发送自定义消息
client.send_chat_message(project.pid, "确认，开始制作")
```

## 6. 环境变量方式

方便在脚本和 CI 中使用：

```bash
export HUASHENG_SESSDATA="xxx"
export HUASHENG_CSRF="xxx"
```

```python
import os
client = HuashengClient(cookies={
    "SESSDATA": os.environ["HUASHENG_SESSDATA"],
    "bili_jct": os.environ["HUASHENG_CSRF"],
})
```

## 下一步

- [完整 API 文档](api.md)
- [示例代码](../examples/)
- [参考项目 bilibili-api](https://github.com/Vespa314/bilibili-api)
