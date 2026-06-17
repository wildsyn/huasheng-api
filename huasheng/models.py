"""
花生数据模型
===========
所有 API 返回数据的 dataclass 模型定义。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class UserInfo:
    """用户信息（来自 /x/web-interface/nav）"""
    mid: int = 0
    uname: str = ""
    face: str = ""
    is_login: bool = False
    level: int = 0
    level_exp_current: int = 0
    level_exp_next: int = 0
    vip_status: int = 0           # 0=非会员, 1=会员
    vip_type: int = 0             # 2=年度大会员
    vip_due_date: int = 0         # 到期时间戳(ms)
    vip_label_text: str = ""
    money: float = 0.0
    moral: int = 0
    ip_region: str = ""

    @classmethod
    def from_nav(cls, data: dict) -> "UserInfo":
        """从 /x/web-interface/nav 响应解析"""
        if data.get("code") != 0:
            return cls(is_login=False)
        d = data.get("data", {})
        level_info = d.get("level_info", {})
        vip_label = d.get("vip_label", {})
        return cls(
            mid=d.get("mid", 0),
            uname=d.get("uname", ""),
            face=d.get("face", ""),
            is_login=d.get("isLogin", False),
            level=level_info.get("current_level", 0),
            level_exp_current=level_info.get("current_exp", 0),
            level_exp_next=level_info.get("next_exp", 0),
            vip_status=d.get("vipStatus", 0),
            vip_type=d.get("vipType", 0),
            vip_due_date=d.get("vipDueDate", 0),
            vip_label_text=vip_label.get("text", ""),
            money=d.get("money", 0.0),
            moral=d.get("moral", 0),
            ip_region=d.get("ip_region", ""),
        )


@dataclass
class VipInfo:
    """VIP 及花生积分信息（来自 /api/vip/info）"""
    uid: str = ""
    is_vip: bool = False
    vip_expire_at: int = 0
    trials: int = 0                    # 剩余试用次数
    new_msg_cnt: str = "0"
    ttv_example_project_cnt: int = 0   # 示例项目数（智能匹配）
    podcast_example_project_cnt: int = 0
    total_points: str = "0"            # 总花生积分
    package_points: str = "0"          # 套餐积分
    single_points: str = "0"           # 单次积分
    is_new_user: bool = False

    @classmethod
    def from_response(cls, data: dict) -> "VipInfo":
        """从 /api/vip/info 响应解析"""
        point_info = data.get("point_info", {})
        return cls(
            uid=data.get("uid", ""),
            is_vip=data.get("is_vip", False),
            vip_expire_at=data.get("vip_expire_at", 0),
            trials=data.get("trials", 0),
            new_msg_cnt=data.get("new_msg_cnt", "0"),
            ttv_example_project_cnt=data.get("ttv_example_project_cnt", 0),
            podcast_example_project_cnt=data.get("podcast_example_project_cnt", 0),
            total_points=point_info.get("total_remain", "0"),
            package_points=point_info.get("package_remain", "0"),
            single_points=point_info.get("single_remain", "0"),
            is_new_user=data.get("new_1d", False),
        )


@dataclass
class Voice:
    """配音音色（来自 TTS material list）"""
    id: str = ""
    name: str = ""
    cover: str = ""
    voice_type: int = 0             # 0=TTS, 1=克隆
    voice_key: str = ""             # voice engine key
    tags: str = ""                  # tts_tags, e.g. "专业深度"
    preview_url: str = ""
    raw_data: str = ""              # 示例文案
    material_type: str = ""
    rank: str = ""
    state: int = 0

    @classmethod
    def from_material(cls, item: dict) -> "Voice":
        """从 material/tts/list 条目解析"""
        import json
        extra_str = item.get("extra", "{}")
        try:
            extra = json.loads(extra_str)
        except (json.JSONDecodeError, TypeError):
            extra = {}
        pool_extra_str = item.get("pool_extra", "{}")
        try:
            pool_extra = json.loads(pool_extra_str)
        except (json.JSONDecodeError, TypeError):
            pool_extra = {}

        return cls(
            id=item.get("id", ""),
            name=item.get("name", ""),
            cover=item.get("cover", ""),
            voice_type=extra.get("voice_type", 0),
            voice_key=extra.get("voice", ""),
            tags=pool_extra.get("tts_tags", ""),
            preview_url=pool_extra.get("preview_url", ""),
            raw_data=extra.get("raw_data", ""),
            material_type=item.get("material_type", ""),
            rank=item.get("rank", ""),
            state=item.get("state", 0),
        )


@dataclass
class CloneVoice:
    """克隆音色"""
    voice_id: str = ""
    name: str = ""
    status: int = 0
    preview_url: str = ""

    @classmethod
    def from_response(cls, item: dict) -> "CloneVoice":
        return cls(
            voice_id=item.get("id", item.get("voice_id", "")),
            name=item.get("name", ""),
            status=item.get("status", 0),
            preview_url=item.get("preview_url", ""),
        )


@dataclass
class BGM:
    """背景音乐"""
    id: str = ""
    name: str = ""
    cover: str = ""
    download_url: str = ""
    duration: str = ""              # 秒
    emotion: str = ""               # 情绪标签: 平静/欢快/抒情/治愈
    rhythm: str = ""                # 节奏: 偏慢/适中/偏快
    adaptation: str = ""            # 适配场景: 财经/社会/...
    rank: str = ""

    @classmethod
    def from_bgm_item(cls, item: dict) -> "BGM":
        import json
        extra_str = item.get("extra", "{}")
        try:
            extra = json.loads(extra_str)
        except (json.JSONDecodeError, TypeError):
            extra = {}
        return cls(
            id=item.get("id", ""),
            name=item.get("name", ""),
            cover=item.get("cover", ""),
            download_url=item.get("download_url", ""),
            duration=item.get("duration", ""),
            emotion=item.get("emo", ""),
            rhythm=extra.get("bgm_rhythm", ""),
            adaptation=extra.get("bgm_adaptation", ""),
            rank=item.get("bgm_rank", ""),
        )


@dataclass
class BGMList:
    """BGM 分类列表"""
    categories: List[Dict[str, Any]] = field(default_factory=list)

    def get_all_bgms(self) -> List[BGM]:
        """获取所有 BGM"""
        bgms = []
        for cat in self.categories:
            for item in cat.get("bgms", []):
                bgms.append(BGM.from_bgm_item(item))
        return bgms

    @classmethod
    def from_response(cls, data: dict) -> "BGMList":
        return cls(categories=data.get("bgmCategories", []))


@dataclass
class ChatInput:
    """Agent 对话输入"""
    role: str = "user"
    script: str = ""
    voice_name: str = ""
    project_type: str = "智能匹配素材"

    @classmethod
    def from_dict(cls, d: dict) -> "ChatInput":
        extra = d.get("extra", {})
        return cls(
            role=d.get("role", "user"),
            script=extra.get("script", ""),
            voice_name=extra.get("voice_name", ""),
            project_type=extra.get("project_type", "智能匹配素材"),
        )


@dataclass
class ChatRun:
    """单次 Agent 对话运行记录"""
    run_id: str = ""
    input: Optional[ChatInput] = None
    created_at: int = 0
    is_first_run: bool = False
    events: List[Dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ChatRun":
        return cls(
            run_id=d.get("run_id", ""),
            input=ChatInput.from_dict(d.get("input", {})),
            created_at=d.get("created_at", 0),
            is_first_run=d.get("first_run", False),
            events=d.get("events", []),
        )


@dataclass
class ChatHistory:
    """Agent 对话历史"""
    runs: List[ChatRun] = field(default_factory=list)
    is_working: bool = False
    current_run_id: str = ""

    @classmethod
    def from_response(cls, data: dict) -> "ChatHistory":
        runs_data = data.get("runs", [])
        current_state = data.get("current_state", {})
        return cls(
            runs=[ChatRun.from_dict(r) for r in runs_data],
            is_working=current_state.get("is_working", False),
            current_run_id=current_state.get("run_id", ""),
        )


@dataclass
class ClipVideo:
    """视频片段中的视频轨道"""
    id: str = ""
    url: str = ""
    duration: float = 0.0
    width: str = ""
    height: str = ""
    fps: int = 30
    cover: str = ""
    start_time: float = 0.0
    state: str = "0"
    subtitle_mask: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "ClipVideo":
        return cls(
            id=d.get("id", ""),
            url=d.get("url", ""),
            duration=d.get("duration", 0.0),
            width=d.get("width", ""),
            height=d.get("height", ""),
            fps=d.get("fps", 30),
            cover=d.get("cover", ""),
            start_time=d.get("start_time", 0.0),
            state=d.get("state", "0"),
            subtitle_mask=d.get("subtitle_mask", ""),
        )


@dataclass
class ClipVoice:
    """视频片段中的配音轨道"""
    id: str = ""
    url: str = ""
    duration: float = 0.0
    srt: str = ""          # SRT 字幕内容
    final_srt: str = ""    # 最终 SRT

    @classmethod
    def from_dict(cls, d: dict) -> "ClipVoice":
        return cls(
            id=d.get("id", "0"),
            url=d.get("url", ""),
            duration=d.get("duration", 0.0),
            srt=d.get("srt", ""),
            final_srt=d.get("final_srt", ""),
        )


@dataclass
class ProjectClip:
    """视频片段（一个场景 = 视频轨道 + 配音轨道）"""
    id: str = ""
    content: str = ""      # 字幕/口播文本
    video: Optional[ClipVideo] = None
    voice: Optional[ClipVoice] = None

    @classmethod
    def from_dict(cls, d: dict) -> "ProjectClip":
        return cls(
            id=d.get("id", ""),
            content=d.get("content", ""),
            video=ClipVideo.from_dict(d["video"]) if d.get("video") else None,
            voice=ClipVoice.from_dict(d["voice"]) if d.get("voice") else None,
        )


@dataclass
class Project:
    """视频项目"""
    # 项目 ID
    pid: int = 0                    # 公开 PID（用于 URL）
    id: str = ""                    # 内部 ID

    # 基本信息
    name: str = ""
    script: str = ""
    uid: str = ""

    # 状态
    stage: str = "0"
    state: str = "0"                # 0=处理中, 1=完成
    state_message: str = ""         # "项目处理完成"
    progress: str = "100"           # 进度 0-100
    loading_status: str = "1"       # 加载状态

    # 配音设置
    voice_id: str = ""
    voice_type: str = "0"           # 0=TTS
    voice_volume: str = "75"
    speech_rate: float = 1.0
    speech_rate_change: float = 1.0
    tts_running: bool = False

    # 字幕设置
    subtitle_state: str = "1"       # 1=开启
    font_size: str = "42"
    font_color: str = "#FFFFFF"
    outline_thick: str = "80"
    outline_color: str = "#000000"

    # BGM 设置
    bgm_id: str = "0"
    bgm_volume: str = "30"
    is_set_bgm: str = "1"

    # 其他
    project_type: str = "0"
    cover: str = ""
    created_at: str = ""
    version: str = "0"
    is_agent: bool = False          # 是否 Agent 模式
    composite_running: bool = False
    motion_running: bool = False

    # 子数据
    clips: List[ProjectClip] = field(default_factory=list)
    bgms: List[Dict] = field(default_factory=list)
    motions: List[Dict] = field(default_factory=list)
    # 项目哈希（完成时生成）
    project_hash: str = ""

    @classmethod
    def from_info(cls, data: dict) -> "Project":
        """从 /api/innovideo/project/info 响应解析"""
        proj = data.get("project", {})
        # 解析 clips
        clips = [ProjectClip.from_dict(c) for c in data.get("clips", [])]
        return cls(
            pid=proj.get("pid", 0),
            id=proj.get("id", ""),
            name=proj.get("name", ""),
            script=proj.get("script", ""),
            uid=proj.get("uid", ""),
            stage=proj.get("stage", "0"),
            state=proj.get("state", "0"),
            state_message=proj.get("state_message", ""),
            progress=proj.get("progress", "100"),
            loading_status=proj.get("loading_status", "1"),
            voice_id=proj.get("voice_id", ""),
            voice_type=proj.get("voice_type", "0"),
            voice_volume=proj.get("voice_volume", "75"),
            speech_rate=proj.get("speech_rate", 1.0),
            speech_rate_change=proj.get("speech_rate_change", 1.0),
            tts_running=proj.get("tts_running", False),
            subtitle_state=proj.get("subtitle_state", "1"),
            font_size=proj.get("font_size", "42"),
            font_color=proj.get("font_color", "#FFFFFF"),
            outline_thick=proj.get("outline_thick", "80"),
            outline_color=proj.get("outline_color", "#000000"),
            bgm_id=proj.get("bgm_id", "0"),
            bgm_volume=proj.get("bgm_volume", "30"),
            is_set_bgm=proj.get("is_set_bgm", "1"),
            project_type=proj.get("project_type", "0"),
            cover=proj.get("cover", ""),
            created_at=proj.get("created_at", ""),
            version=proj.get("version", "0"),
            is_agent=proj.get("is_agent", False),
            composite_running=proj.get("composite_running", False),
            motion_running=proj.get("motion_running", False),
            clips=clips,
            bgms=data.get("bgms", []),
            motions=data.get("motions", []),
            project_hash=proj.get("project_hash", ""),
        )

    @classmethod
    def from_list_item(cls, proj: dict) -> "Project":
        """从 /api/innovideo/project/list 条目解析（精简版，无 clips）"""
        return cls(
            pid=proj.get("pid", 0),
            id=proj.get("id", ""),
            name=proj.get("name", ""),
            script=proj.get("script", ""),
            uid=proj.get("uid", ""),
            stage=proj.get("stage", "0"),
            state=proj.get("state", "0"),
            state_message=proj.get("state_message", ""),
            progress=proj.get("progress", "100"),
            loading_status=proj.get("loading_status", "1"),
            voice_id=proj.get("voice_id", ""),
            voice_type=proj.get("voice_type", "0"),
            project_type=proj.get("project_type", "0"),
            cover=proj.get("cover", ""),
            created_at=proj.get("created_at", ""),
            is_agent=proj.get("is_agent", False),
            project_hash=proj.get("project_hash", ""),
        )

    @property
    def is_finished(self) -> bool:
        """是否生成完成 — state=0 且 loading_status=1 且 state_message='项目处理完成'"""
        return (
            self.loading_status == "1"
            and self.state_message == "项目处理完成"
            and len(self.clips) > 0
        )

    @property
    def is_processing(self) -> bool:
        """是否正在处理 — state=-1 或 loading_status=0"""
        return self.state == "-1" or self.loading_status == "0"

    @property
    def total_duration(self) -> float:
        """视频总时长（所有 clips 的 video duration 之和）"""
        return sum(
            (c.video.duration if c.video else 0)
            for c in self.clips
        )
