# 花生 (Huasheng) API 完整文档

> 基于对 huasheng.cn 网页应用的 API 逆向分析。
> 最后更新: 2026-06-04

## 目录

- [API 域名架构](#api-域名架构)
- [认证流程](#认证流程)
- [用户信息](#用户信息)
- [应用配置](#应用配置)
- [视频项目](#视频项目)
- [Agent 对话](#agent-对话)
- [素材与配音](#素材与配音)
- [数据模型](#数据模型)

---

## API 域名架构

| 域名 | 用途 | 示例 |
|------|------|------|
| `www.huasheng.cn/api/` | 核心业务 API (Next.js) | `/api/huasheng/project/create` |
| `api.huasheng.cn/x/` | B站通用 API 格式 | `/x/web-interface/nav` |
| `passport.huasheng.cn/x/` | 登录认证 | `/x/passport-login/web/qrcode/generate` |
| `sse.huasheng.cn/api/` | SSE 实时流 | `/api/huasheng/chat/events` |
| `data.huasheng.cn/v2/` | 日志上报 (protobuf) | `/v2/log/web` |

### 通用约定

- **CSRF Token**: `bili_jct` cookie 的值，作为 POST 请求的 `csrf` 参数
- **Referer**: 必须设为 `https://www.huasheng.cn/`
- **User-Agent**: 需模拟 Chrome 浏览器
- **序列化**: JSON，UTF-8 编码
- **状态码**: `{"code": 0}` 表示成功，`{"code": -101}` 表示未登录

---

## 认证流程

### 1. 生成登录二维码

```
GET passport.huasheng.cn/x/passport-login/web/qrcode/generate
  ?source=ttv_pc
  &go_url=https://www.huasheng.cn/
  &web_location=333.40121
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "url": "https://...",       // 二维码图片 URL
    "qrcode_key": "041e71ee..."  // 用于轮询的 key
  }
}
```

### 2. 轮询扫码状态

```
GET passport.huasheng.cn/x/passport-login/web/qrcode/poll
  ?qrcode_key=<qrcode_key>
  &source=ttv_pc
```

**响应**:
```json
{
  "code": 0,                    // 0=已扫码未确认, 其他值需查看 message
  "message": "未扫码" | "已扫码" | "已确认"
}
```

### 3. Web Ticket

B站多数接口需要 Web Ticket 防爬，格式：

```
POST api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket
  ?key_id=ec02
  &hexsign=<hex_signature>
  &context[ts]=<timestamp>
  &csrf=<bili_jct>
```

---

## 用户信息

### 获取用户导航信息

```
GET api.huasheng.cn/x/web-interface/nav
```

**响应** (已登录):
```json
{
  "code": 0,
  "message": "OK",
  "data": {
    "isLogin": true,
    "mid": 1615486421,
    "uname": "用户名",
    "face": "https://i2.hdslb.com/bfs/face/....jpg",
    "level_info": {
      "current_level": 5,
      "current_exp": 23516,
      "next_exp": 28800
    },
    "vipStatus": 1,             // 0=非会员, 1=会员
    "vipType": 2,               // 2=年度大会员
    "vipDueDate": 1823443200000, // 到期时间戳(ms)
    "vip_label": {
      "text": "年度大会员",
      "label_theme": "annual_vip"
    },
    "money": 1012.3,
    "moral": 70
  }
}
```

**响应** (未登录):
```json
{
  "code": -101,
  "message": "账号未登录",
  "data": { "isLogin": false }
}
```

### 获取 VIP 及花生积分

```
GET www.huasheng.cn/api/vip/info
```

**响应**:
```json
{
  "uid": "1615486421",
  "is_vip": true,
  "vip_expire_at": 1782403199,
  "trials": 0,                      // 剩余试用次数
  "ttv_example_project_cnt": 1,     // 智能匹配示例数
  "podcast_example_project_cnt": 1, // 播客示例数
  "point_info": {
    "total_remain": "20000",        // 总剩余花生积分
    "package_remain": "20000",      // 套餐积分
    "single_remain": "0"            // 单次积分
  },
  "new_1d": false                   // 是否新用户
}
```

### 获取用户偏好

```
GET www.huasheng.cn/api/huasheng/user/preference/list
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "list": [
      {
        "id": 138745227898883,
        "name": "字幕偏好",
        "content": "每一个字幕后面不要跟对应的逗号和句号..."
      }
    ]
  }
}
```

---

## 应用配置

### 获取应用配置

```
GET www.huasheng.cn/api/innovideo/config
```

**响应**:
```json
{
  "voices": [
    {
      "id": "5",
      "voice": "male-qn-jingying",
      "desc": "生动解说"
    }
    // ...
  ],
  "script_max": "10000",           // 文案最大字数
  "audio_script_max": "50000",     // 音频文案最大
  "user_material_max": "200",      // 用户素材上限
  "content_markup_multiple": "3", // 标记倍数
  "default_voice_id": 6036542,
  "report_tag": [
    {
      "cat_name": "风险",
      "tags": [
        { "tid": "1", "name": "敏感人物或物品" },
        { "tid": "2", "name": "违法违规" },
        { "tid": "3", "name": "色情低俗" },
        { "tid": "5", "name": "侵权" }
      ]
    },
    {
      "cat_name": "匹配",
      "tags": [
        { "tid": "6", "name": "重复出现" },
        { "tid": "7", "name": "素材画风突兀" }
      ]
    }
  ],
  "models": [{ "id": "10", "desc": "Index" }]
}
```

### A/B 测试配置

```
GET www.huasheng.cn/api/innovideo/abtest?ab_var=front_montage
GET www.huasheng.cn/api/innovideo/abtest?ab_var=montage_composite
GET www.huasheng.cn/api/innovideo/abtest?ab_var=podcast_mtq
```

---

## 视频项目

### 创建项目

```
POST www.huasheng.cn/api/huasheng/project/create?csrf=<bili_jct>
Content-Type: application/json

{
  "name": "",                    // 项目名称（可空）
  "is_denoise": 0,              // 是否降噪
  "script": "视频文案内容...",   // 文案（≤10000字）
  "voice_id": 5866601,          // 配音音色 ID (int)
  "voice_type": 0,              // 0=TTS配音, 1=声音克隆
  "audio_url": "",              // 口播音频 URL（音频创建方式）
  "speech_rate": 1,             // 语速倍率
  "speech_rate_change": 1,      // 语速变化
  "project_type": 0,            // 0=智能匹配素材, 1=播客模式
  "is_agree": 0,                // 是否同意协议
  "is_multi": 0,                // 是否多人协作
  "audio_duration": 0           // 音频时长(秒)
}
```

**响应**:
```json
{
  "code": 0,
  "message": "0",
  "data": {
    "pid": 158985403568130       // 项目公开ID（用于URL）
  }
}
```

### 获取项目详情 (轮询)

```
GET www.huasheng.cn/api/innovideo/project/info?pid=<pid>
```

**响应**:
```json
{
  "project": {
    "id": "5065943",              // 内部 ID
    "pid": 158985403568130,        // 公开 PID
    "uid": "1615486421",
    "script": "视频文案...",
    "name": "",
    "stage": "0",
    "state": "0",                  // 0=处理中? 1=完成?
    "state_message": "项目处理完成",
    "progress": "100",             // 进度 0-100
    "loading_status": "1",        // 1=加载完成
    "cover": "",
    "voice_id": "5866601",
    "voice_type": "0",
    "voice_volume": "75",
    "speech_rate": 1,
    "speech_rate_change": 1,
    "tts_running": false,
    "composite_running": false,
    "motion_running": false,
    "project_type": "0",
    "subtitle_state": "1",
    "font_size": "42",
    "font_color": "#FFFFFF",
    "outline_thick": "80",
    "outline_color": "#000000",
    "bgm_id": "0",
    "bgm_volume": "30",
    "is_set_bgm": "1",
    "is_agent": true,             // 是否 Agent 模式
    "created_at": "1780584969",
    "version": "0",
    "estimate_clip_count": "0",   // 预估片段数
    "wait_time": "0",
    "ai_tag": "1",
    "can_add_clip": "1",
    "motion_type": "1",
    "project_hash": ""
  },
  "clips": [],                    // 视频片段列表
  "bgms": [],                     // BGM 列表（已选的）
  "project_update": {
    "window": "0",
    "update_clip": []
  },
  "motions": []                   // 动画列表
}
```

### 获取项目 BGM 列表

```
GET www.huasheng.cn/api/innovideo/project/bgm/list?project_id=<internal_id>
```

**响应**:
```json
{
  "bgmCategories": [
    {
      "category_id": "0",
      "category_name": "全部",
      "category_rank": "0",
      "bgms": [
        {
          "id": "4791684",
          "name": "Eutopia",
          "cover": "http://i0.hdslb.com/bfs/music/....jpg",
          "download_url": "http://upos-sz-staticcos.bilivideo.com/....m4a",
          "duration": "121",            // 秒
          "emo": "平静",                // 情绪标签
          "extra": "{\"bgm_rhythm\":\"偏慢\",\"bgm_adaptation\":\"社会\"}",
          "bgm_rank": "4791684"
        }
      ]
    }
  ]
}
```

---

## Agent 对话

花生提供 Agent 对话式视频创作。创建项目后，AI Agent 会自动分析文案、生成需求文档、制定分镜方案，用户通过对话与 Agent 交互确认每一步。

### 对话流程

```
1. create_project()
2. Agent 自动分析 → 生成需求文档 → 提问（选项或等待确认）
3. 用户 send_chat_answer() 或 send_chat_message() 回复
4. Agent 继续 → 生成分镜方案 → 素材匹配 → 配音 → 合成
5. 每步都通过 SSE 流推送实时状态
```

### 获取对话历史

```
GET www.huasheng.cn/api/huasheng/chat/history
  ?project_id=<pid>
  &limit=20
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "runs": [
      {
        "run_id": "019e9322736d72c3a826ae2b00998da6",
        "input": {
          "extra": {
            "script": "人工智能技术正在改变...",
            "voice_name": "清亮男声",
            "project_type": "智能匹配素材"
          },
          "role": "user"
        },
        "created_at": 1780584969,
        "first_run": true,
        "events": []
      }
    ],
    "current_state": {
      "is_working": true,
      "run_id": "019e9322736d72c3a826ae2b00998da6"
    }
  }
}
```

### 回复 Agent 选项 (选择题)

当 Agent 提出多个选项时（如 "A - xxx / B - xxx"），使用此接口：

```
POST www.huasheng.cn/api/huasheng/chat/answers?csrf=<bili_jct>
Content-Type: application/json

{
  "pid": 158985403568130,
  "run_id": "019e932273...",     // 当前 run_id
  "batch_id": "019e932295...",    // Agent 提问的批次 ID
  "answers": {
    "<question_id>": {
      "text": "B - 素材混合MG动画（适合数据可视化、概念解释，视觉丰富）"
    }
  }
}
```

**响应**:
```json
{"code": 0, "message": "0", "data": {}}
```

### 发送自由文本消息

```
POST www.huasheng.cn/api/huasheng/chat/run?csrf=<bili_jct>
Content-Type: application/json

{
  "pid": 158985403568130,
  "content": [
    {
      "type": "text",
      "text": {
        "content": "确认分镜方案，开始制作视频"
      }
    }
  ]
}
```

**响应**:
```json
{
  "code": 0,
  "data": {
    "run_id": "019e932d6c487a32...",   // 新的 run_id
    "is_working": false,
    "state": 0
  }
}
```

### 监听 SSE 事件流

**这是花生最核心的 API** — 实时推送 Agent 的每一步生成进度：

```
GET sse.huasheng.cn/api/huasheng/chat/events
  ?run_id=<run_id>
  &project_id=<pid>
Accept: text/event-stream
```

SSE 事件格式:
```
data: {"type": "agent_message", "content": "..."}
data: {"type": "progress", "step": "tts", "percent": 50}
data: {"type": "tool_call", "tool": "search_material", "args": {...}}
data: [DONE]
```

### 检查运行效果

```
GET www.huasheng.cn/api/huasheng/chat/running/effects
  ?running_ids=<run_id>
  &project_id=<pid>
```

### 工具调用成本

```
GET www.huasheng.cn/api/huasheng/chat/tool-cost
  ?pid=<pid>
  &run_id=<run_id>
```

---

## 素材与配音

### TTS 音色列表

```
GET www.huasheng.cn/api/innovideo/material/tts/list
  ?pn=1
  &ps=50
  &category_id=0             // 0=全部分类
```

**响应**:
```json
{
  "materials": [
    {
      "id": "6036716",
      "name": "财经小哥",
      "cover": "http://i0.hdslb.com/bfs/creative/....png",
      "extra": "{\"voice_type\":3,\"voice\":\"ai_platform-xxx-xxx\",\"raw_data\":\"示例文案...\"}",
      "state": 0,
      "rank": "1",
      "material_type": "27",
      "pool_extra": "{\"tts_tags\":\"专业深度\",\"preview_url\":\"http://boss.hdslb.com/material/....wav\"}"
    }
  ]
}
```

### 声音克隆列表

```
GET www.huasheng.cn/api/innovideo/voice/clone/list
```

**响应**:
```json
{
  "voices": [],
  "last_used_voice_id": "0",
  "copied_voice_id": "0",
  "newest_engine_voice_id": "0"
}
```

---

## 数据模型

### Project 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `pid` | int | 公开项目 ID，用于 URL |
| `id` | str | 内部项目 ID |
| `script` | str | 视频文案 |
| `state` | str | "0"=初始, "1"=完成 |
| `state_message` | str | 状态描述，如"项目处理完成" |
| `progress` | str | 进度 0-100 |
| `loading_status` | str | "0"=加载中, "1"=加载完成 |
| `tts_running` | bool | TTS 配音是否进行中 |
| `composite_running` | bool | 视频合成是否进行中 |
| `is_agent` | bool | 是否使用 Agent 模式 |
| `voice_id` | str | 配音音色 ID |
| `voice_type` | str | 音色类型 "0"=TTS |
| `project_type` | str | "0"=智能匹配, "1"=播客 |
| `subtitle_state` | str | "1"=开启字幕 |

### ChatRun 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `run_id` | str | 对话运行 ID |
| `input` | ChatInput | 用户输入内容 |
| `created_at` | int | 创建时间戳 |
| `first_run` | bool | 是否首次运行 |
| `events` | list | 事件列表（历史可能为空，实时从 SSE 获取） |

### Voice 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | str | 音色 ID |
| `name` | str | 音色名称 |
| `cover` | str | 封面图 URL |
| `voice_key` | str | 引擎 key (用于 TTS) |
| `tags` | str | 标签 (如"专业深度") |
| `preview_url` | str | 试听音频 URL |
