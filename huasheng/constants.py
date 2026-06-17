"""
花生 API 端点常量
===============
所有已知的 huasheng.cn API 端点，按功能分组。
"""

# === 域名 ===
BASE_WWW = "https://www.huasheng.cn"
BASE_API = "https://api.huasheng.cn"
BASE_PASSPORT = "https://passport.huasheng.cn"
BASE_SSE = "https://sse.huasheng.cn"
BASE_DATA = "https://data.huasheng.cn"
BASE_PASSPORT_BILI = "https://passport.bilibili.com"

# === 认证 ===
# 生成登录二维码
LOGIN_QRCODE_GENERATE = f"{BASE_PASSPORT}/x/passport-login/web/qrcode/generate"
# 轮询扫码状态
LOGIN_QRCODE_POLL = f"{BASE_PASSPORT}/x/passport-login/web/qrcode/poll"
# SSO 登录信息获取
LOGIN_SSO_LIST = f"{BASE_PASSPORT}/x/passport-login/web/sso/list"
# SSO 登录设置
LOGIN_SSO_SET = f"{BASE_PASSPORT_BILI}/x/passport-login/web/sso/set"
# Web Ticket（防爬）
TICKET_GEN = "https://api.bilibili.com/bapis/bilibili.api.ticket.v1.Ticket/GenWebTicket"

# === 用户 ===
# 用户导航信息（含登录态、VIP等）
USER_NAV = f"{BASE_API}/x/web-interface/nav"
# VIP 信息（含花生积分）
VIP_INFO = f"{BASE_WWW}/api/vip/info"
# 用户偏好设置
USER_PREFERENCE_LIST = f"{BASE_WWW}/api/huasheng/user/preference/list"

# === 应用配置 ===
# 花生应用配置（音色列表、限制、举报标签）
APP_CONFIG = f"{BASE_WWW}/api/innovideo/config"
# A/B 测试配置
ABTEST = f"{BASE_WWW}/api/innovideo/abtest"
# TTS 音色素材列表
TTS_MATERIAL_LIST = f"{BASE_WWW}/api/innovideo/material/tts/list"
# 声音克隆列表
VOICE_CLONE_LIST = f"{BASE_WWW}/api/innovideo/voice/clone/list"

# === 视频项目 ===
# 创建视频项目
PROJECT_CREATE = f"{BASE_WWW}/api/huasheng/project/create"
# 项目详情（轮询用）
PROJECT_INFO = f"{BASE_WWW}/api/innovideo/project/info"
# 项目列表
PROJECT_LIST = f"{BASE_WWW}/api/innovideo/project/list"
# 项目 BGM 列表
PROJECT_BGM_LIST = f"{BASE_WWW}/api/innovideo/project/bgm/list"
# 音频/文件预上传（获取 upos 上传 URL）
PREUPLOAD = f"{BASE_WWW}/api/innovideo/preupload"
# 视频导出（创建导出任务）
EXPORT_TASK = f"{BASE_WWW}/api/innovideo/project/export/video/task"
# 视频导出信息（查询导出进度 + CDN URL）
EXPORT_INFO = f"{BASE_WWW}/api/innovideo/project/export/video/info"
# 确认费用计划
PROJECT_PLAN_CONFIRM = f"{BASE_WWW}/api/huasheng/project_plan/confirm"

# === Agent 对话 ===
# 对话状态
CHAT_STATE = f"{BASE_WWW}/api/huasheng/chat/state"
# 聊天历史
CHAT_HISTORY = f"{BASE_WWW}/api/huasheng/chat/history"
# 聊天 SSE 事件流（实时生成）
CHAT_EVENTS = f"{BASE_SSE}/api/huasheng/chat/events"
# 运行中效果
CHAT_RUNNING_EFFECTS = f"{BASE_WWW}/api/huasheng/chat/running/effects"
# 项目检查点
PROJECT_CHECKPOINT_LIST = f"{BASE_WWW}/api/huasheng/project/checkpoint/list"

# Agent 对话答案
CHAT_ANSWERS = f"{BASE_WWW}/api/huasheng/chat/answers"
# Agent 自由文本消息
CHAT_RUN = f"{BASE_WWW}/api/huasheng/chat/run"
# Agent 工具调用成本
CHAT_TOOL_COST = f"{BASE_WWW}/api/huasheng/chat/tool-cost"

# === 分镜编辑 ===
# 分镜素材替换候选
CLIP_CANDIDATES = f"{BASE_WWW}/api/huasheng/clip/candidates/list"
# 分镜渲染查询（获取渲染后的视频 URL）
CLIP_RENDER_QUERY = f"{BASE_WWW}/api/huasheng/clip/render/query"
# 替换分镜素材
CLIP_VIDEO_EDIT = f"{BASE_WWW}/api/innovideo/clip/video/edit"
# 相似素材候选
CLIP_SIMILAR_CANDIDATES = f"{BASE_WWW}/api/innovideo/clip/similar/candidates"
# 同源素材候选
CLIP_SAMESOURCE_CANDIDATES = f"{BASE_WWW}/api/innovideo/clip/samesource/candidates"
# 候选素材信息
CLIP_CANDIDATE_INFO = f"{BASE_WWW}/api/innovideo/clip/candidate/info"

# === 用户偏好 ===
# 创建偏好
USER_PREFERENCE_CREATE = f"{BASE_WWW}/api/huasheng/user/preference/create"

# === 项目保存点 ===
# 项目保存点（书签/版本管理）
PROJECT_SAVEPOINT_LIST = f"{BASE_WWW}/api/huasheng/project/savepoint/list"

# === 日志（protobuf） ===
LOG_WEB = f"{BASE_DATA}/v2/log/web"

# === 活动/运营 ===
ACTIVITY_LIST = f"{BASE_API}/x/activity_components/eva_operation/list"

# === 项目类型 ===
PROJECT_TYPE_SMART_MATCH = 0   # 智能匹配素材
PROJECT_TYPE_PODCAST = 1       # 播客模式

# === 音色类型 ===
VOICE_TYPE_TTS = 0             # TTS 配音（文稿模式）
VOICE_TYPE_AUDIO = 2           # 口播音频模式

# === 文案类型（音频模式用） ===
SCRIPT_TYPE_OUTLINE = 1        # 大纲、草稿、关键词等 — 辅助字幕识别准确度
SCRIPT_TYPE_TRANSCRIPT = 2     # 逐字稿 — 直接作为视频字幕

# === 项目状态 ===
PROJECT_STATE_PROCESSING = "0"    # 处理中
PROJECT_STATE_FINISHED = "1"     # 已完成
