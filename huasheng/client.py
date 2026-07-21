"""
花生主客户端
===========
HuashengClient — 花生 AI 视频创作工具的主要 API 入口。
"""

import hashlib
import time
import json
import logging
from typing import Optional, List, Dict, Any, Iterator, Union

from .http import HuashengHTTP
from .models import (
    UserInfo, VipInfo, Voice, CloneVoice,
    BGM, BGMList, Project, ChatHistory,
)
from . import constants as C

logger = logging.getLogger(__name__)


class HuashengClient:
    """花生 AI 视频创作工具 Python SDK

    使用示例::

        client = HuashengClient(cookies={"SESSDATA": "xxx", "bili_jct": "xxx"})

        # 检查登录
        user = client.get_user_info()

        # 获取可用音色
        voices = client.get_tts_voices()

        # 创建视频
        project = client.create_project(script="视频文案...", voice_id="5866601")

        # 等待生成完成
        project = client.wait_for_completion(project.pid)

        # 获取聊天历史
        history = client.get_chat_history(project.pid)
    """

    def __init__(
        self,
        cookies: Optional[Dict[str, str]] = None,
        cookie_file: Optional[str] = None,
        timeout: int = 30,
        proxy: Optional[str] = None,
        poll_interval: float = 2.0,
        poll_timeout: float = 600.0,
    ):
        """
        Args:
            cookies: 字典形式的 cookies（至少需要 SESSDATA 和 bili_jct）
            cookie_file: Cookie JSON 文件路径
            timeout: HTTP 请求超时（秒）
            proxy: 代理地址
            poll_interval: 轮询项目状态间隔（秒）
            poll_timeout: 轮询超时总时间（秒）
        """
        self.http = HuashengHTTP(
            cookies=cookies,
            cookie_file=cookie_file,
            timeout=timeout,
            proxy=proxy,
        )
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout
        self.last_download_evidence: Optional[Dict[str, Any]] = None

    # === 用户 ===

    def get_user_info(self) -> UserInfo:
        """获取当前登录用户信息"""
        data = self.http.get_json(C.USER_NAV)
        return UserInfo.from_nav(data)

    def get_vip_info(self) -> VipInfo:
        """获取 VIP 及花生积分信息"""
        data = self.http.get_json(C.VIP_INFO)
        return VipInfo.from_response(data)

    def check_login(self) -> bool:
        """检查是否已登录"""
        return self.http.check_login()

    # === 应用配置 ===

    def get_app_config(self) -> Dict[str, Any]:
        """获取花生应用配置（音色、限制、标签等）"""
        return self.http.get_json(C.APP_CONFIG)

    def get_tts_voices(self, page: int = 1, page_size: int = 50, category_id: int = 0) -> List[Voice]:
        """获取 TTS 配音音色列表

        Args:
            page: 页码
            page_size: 每页数量
            category_id: 音色分类 ID（0=全部）
        """
        data = self.http.get_json(
            C.TTS_MATERIAL_LIST,
            pn=page,
            ps=page_size,
            category_id=category_id,
        )
        materials = data.get("materials", [])
        return [Voice.from_material(m) for m in materials]

    def get_clone_voices(self) -> List[CloneVoice]:
        """获取克隆音色列表"""
        data = self.http.get_json(C.VOICE_CLONE_LIST)
        voices = data.get("voices", [])
        return [CloneVoice.from_response(v) for v in voices]

    # === 视频项目 ===

    def create_project(
        self,
        script: str = "",
        voice_id: str = "5866601",
        voice_type: int = 0,
        project_type: int = 0,
        name: str = "",
        audio_url: str = "",
        is_denoise: int = 0,
        speech_rate: float = 1.0,
        speech_rate_change: float = 1.0,
        is_agree: int = 0,
        is_multi: int = 0,
        audio_duration: float = 0,
        user_script: str = "",
        user_script_type: int = 1,
    ) -> Project:
        """创建视频项目

        支持三种模式：

        1. 文稿模式 (voice_type=0):
           提供 script 文案，AI TTS 配音 + 匹配素材
           client.create_project(script="视频文案...", voice_id="5866601")

        2. 音频模式 (voice_type=2):
           上传口播音频，AI 转写 + 匹配素材
           client.create_project(audio_url="upos://...", voice_type=2,
                                 audio_duration=441.5)

        3. 音频+文案模式 (voice_type=2, user_script="..."):
           上传口播音频 + 附带文案，大幅提升字幕识别准确度
           user_script_type=1: 大纲/草稿/关键词（辅助识别）
           user_script_type=2: 逐字稿（直接作为字幕）

           client.create_project(audio_url="upos://...", voice_type=2,
                                 user_script="荆轲刺秦王的完整文案...",
                                 user_script_type=1, audio_duration=441.5)

        Args:
            script: 视频文案（文稿模式，≤10000字）
            voice_id: 配音音色 ID（文稿模式）
            voice_type: 0=TTS文稿, 2=口播音频
            project_type: 0=智能匹配素材, 1=播客
            name: 项目名称（可空）
            audio_url: upos:// 音频地址 — 音频模式
            is_denoise: 降噪
            speech_rate: 语速倍率
            speech_rate_change: 语速变化
            audio_duration: 音频时长（秒）
            user_script: 音频对应的文案 — 提升字幕准确度
            user_script_type: 1=大纲/草稿/关键词, 2=逐字稿

        Returns:
            Project 对象
        """
        payload = {
            "name": name,
            "is_denoise": is_denoise,
            "script": script,
            "voice_id": int(voice_id) if voice_type == 0 else 0,
            "voice_type": voice_type,
            "audio_url": audio_url,
            "speech_rate": speech_rate,
            "speech_rate_change": speech_rate_change,
            "project_type": project_type,
            "is_agree": is_agree,
            "is_multi": is_multi,
            "audio_duration": audio_duration,
        }
        # 音频模式的额外字段
        if voice_type == 2:
            payload["user_script"] = user_script
            payload["user_script_type"] = user_script_type

        data = self.http.post_json(C.PROJECT_CREATE, data=payload, add_csrf=True)
        if data.get("code") != 0:
            raise RuntimeError(f"创建项目失败: {data.get('message', data)}")

        pid = data["data"]["pid"]
        logger.info(f"项目创建成功: pid={pid}")

        return self.get_project(pid)

    def get_project(self, pid: int) -> Project:
        """获取项目详情

        Args:
            pid: 项目公开 ID（从 create_project 返回）
        """
        data = self.http.get_json(C.PROJECT_INFO, pid=pid)
        return Project.from_info(data)

    def list_projects(self, page: int = 1, page_size: int = 20) -> List[Project]:
        """获取项目列表

        Args:
            page: 页码（从 1 开始）
            page_size: 每页数量
        """
        data = self.http.get_json(C.PROJECT_LIST, pn=page, ps=page_size)
        projects = data.get("projects", [])
        return [Project.from_list_item(p) for p in projects]

    def get_project_bgms(self, project_id: str) -> BGMList:
        """获取项目可用的 BGM 列表"""
        data = self.http.get_json(C.PROJECT_BGM_LIST, project_id=project_id)
        return BGMList.from_response(data)

    def wait_for_completion(
        self,
        pid: int,
        interval: Optional[float] = None,
        timeout: Optional[float] = None,
    ) -> Project:
        """轮询等待视频项目生成完成

        花生是异步生成的——创建项目后，AI 需要时间进行：
        1. 文案分析
        2. 素材匹配
        3. TTS 配音
        4. 视频合成

        此方法会定期轮询项目状态直到完成或超时。

        Args:
            pid: 项目公开 ID
            interval: 轮询间隔（秒），默认使用 client 实例设置
            timeout: 超时时间（秒），默认使用 client 实例设置

        Returns:
            生成完成后的 Project 对象

        Raises:
            TimeoutError: 超过超时时间仍未完成
        """
        interval = interval or self.poll_interval
        timeout = timeout or self.poll_timeout

        start = time.time()
        last_progress = -1

        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                raise TimeoutError(
                    f"等待项目 {pid} 完成超时 ({timeout}s)，"
                    f"当前进度: {getattr(project, 'progress', 'unknown')}%"
                )

            project = self.get_project(pid)

            # 进度变化时打印日志
            if project.progress != last_progress:
                logger.info(
                    f"项目 {pid}: 进度 {project.progress}%, "
                    f"状态={project.state_message}, "
                    f"已等待 {elapsed:.0f}s"
                )
                last_progress = project.progress

            if project.is_finished:
                logger.info(f"项目 {pid} 生成完成！耗时 {elapsed:.0f}s")
                return project

            time.sleep(interval)

    # === Agent 对话 ===

    def get_chat_history(self, pid: int, limit: int = 20) -> ChatHistory:
        """获取项目的 Agent 对话历史"""
        data = self.http.get_json(C.CHAT_HISTORY, project_id=pid, limit=limit)
        if data.get("code") != 0:
            raise RuntimeError(f"获取对话历史失败: {data.get('message', data)}")
        return ChatHistory.from_response(data["data"])

    # === 视频导出与下载 ===

    def export_video(self, project_id: Union[int, str]) -> Dict[str, Any]:
        """创建视频导出任务

        Args:
            project_id: 项目内部 ID（不是 pid！从 project.id 获取）

        Returns:
            {"task_id": "...", "version": "2", "project_hash": "..."}
        """
        data = self.http.post_json(
            C.EXPORT_TASK,
            data={"id": int(project_id)},
            add_csrf=True,
        )
        task_id = data.get("task_id", "") or data.get("data", {}).get("task_id", "")
        if not task_id:
            raise RuntimeError(f"导出任务创建失败: {data}")
        logger.info(f"视频导出任务已创建: task_id={task_id}")
        return {
            "task_id": task_id,
            "version": data.get("version", "2"),
            "project_hash": data.get("project_hash", ""),
        }

    def get_export_info(
        self,
        project_id: Union[int, str],
        task_id: str,
        project_hash: str = "",
    ) -> Dict[str, Any]:
        """查询导出进度

        Returns:
            {"url": "CDN下载链接", "progress": "0-100", "cover": "封面URL"}
            CDN 链接公开可访问，~24小时有效，无需 cookie。
        """
        params = {"id": str(project_id), "task_id": task_id}
        if project_hash:
            params["project_hash"] = project_hash
        data = self.http.get_json(C.EXPORT_INFO, **params)
        return {
            "url": data.get("url", ""),
            "progress": data.get("progress", "0"),
            "cover": data.get("cover", ""),
        }

    def wait_for_export(
        self,
        project_id: Union[int, str],
        task_id: str,
        project_hash: str = "",
        poll_interval: float = 5,
        timeout: float = 600,
    ) -> str:
        """轮询等待视频导出完成，返回 CDN 下载 URL

        CDN 链接公开可访问，~24小时有效，无需 cookie。

        Args:
            project_id: 项目内部 ID（project.id，不是 pid）
            task_id: 导出任务 ID
            poll_interval: 轮询间隔（秒）
            timeout: 超时（秒）

        Returns:
            CDN 视频下载 URL
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = self.get_export_info(project_id, task_id, project_hash)
            progress = int(info.get("progress", 0))
            url = info.get("url", "")
            if progress >= 100 and url:
                logger.info(f"视频导出完成: {url[:80]}...")
                return url
            logger.info(f"视频导出中: {progress}%")
            time.sleep(poll_interval)
        raise TimeoutError(f"视频导出超时 ({timeout}s)")

    def download_video(self, cdn_url: str, output_path: str) -> str:
        """从 CDN URL 下载视频到本地文件

        CDN 链接需要 Referer 头但不需要 Cookie。
        CDN URL 有效期约 24 小时（通过 URL 中 deadline 参数控制）。
        过期后需重新调用 export_video() + wait_for_export() 刷新。

        Args:
            cdn_url: CDN 视频 URL（从 wait_for_export 获取）
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        import os
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # CDN 需要 Referer 但不需 Cookie（实测验证）
        headers = {
            "Referer": "https://www.huasheng.cn/",
            "User-Agent": self.http.session.headers.get("User-Agent", ""),
        }
        resp = self.http.session.get(
            cdn_url,
            headers=headers,
            timeout=600,
            stream=True,
        )
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if not content_type.startswith("video/"):
            raise RuntimeError(f"下载响应不是视频: content-type={content_type or 'missing'}")
        content_length_header = resp.headers.get("Content-Length")
        try:
            content_length = int(content_length_header) if content_length_header else None
        except ValueError as exc:
            raise RuntimeError("下载响应 Content-Length 无效") from exc

        total = 0
        digest = hashlib.sha256()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                f.write(chunk)
                total += len(chunk)
                digest.update(chunk)
        if total == 0:
            raise RuntimeError("下载响应为空")
        if content_length is not None and total != content_length:
            raise RuntimeError(
                f"下载不完整: expected={content_length} bytes, received={total} bytes"
            )
        self.last_download_evidence = {
            "content_type": content_type,
            "content_length": content_length,
            "bytes_downloaded": total,
            "sha256": digest.hexdigest(),
        }
        logger.info(f"视频已下载: {output_path} ({total} bytes)")
        return output_path

    def export_and_download(
        self,
        project_id: Union[int, str],
        output_path: str,
        project_hash: str = "",
    ) -> str:
        """一键导出并下载视频到本地

        完整流程: export_video → wait_for_export → download_video

        Args:
            project_id: 项目内部 ID（project.id，不是 pid）
            output_path: 输出文件路径 (.mp4)
            project_hash: 项目哈希（可选，从 get_project 获取）

        Returns:
            本地文件路径
        """
        export = self.export_video(project_id)
        cdn_url = self.wait_for_export(
            project_id,
            export["task_id"],
            project_hash or export.get("project_hash", ""),
            poll_interval=self.poll_interval,
            timeout=self.poll_timeout,
        )
        return self.download_video(cdn_url, output_path)

    # === Agent 对话状态 ===

    def get_chat_state(self, pid: int) -> Dict[str, Any]:
        """获取 Agent 对话状态

        Returns:
            {\"state\": -1, \"run_id\": \"\"}  — state=-1 表示空闲，>0 表示活跃
        """
        data = self.http.get_json(C.CHAT_STATE, pid=pid)
        return data.get("data", {})

    def get_chat_events_sse(self, run_id: str, pid: int) -> Iterator[Dict[str, Any]]:
        """获取 Agent 对话的 SSE 实时事件流

        这是一个生成器，实时 yield 每个 SSE 事件。
        花生 Agent 通过 SSE 推送视频生成过程的每一步：
        - 文案分析结果
        - 分镜匹配
        - 配音进度
        - 合成状态

        Args:
            run_id: 运行 ID（从 create_project 后的 chat_history 获取）
            pid: 项目公开 ID

        Yields:
            每个 SSE 事件解析后的 dict
        """
        url = C.CHAT_EVENTS
        params = {"run_id": run_id, "project_id": pid}

        with self.http.session.get(
            url,
            params=params,
            stream=True,
            timeout=self.poll_timeout,
            headers={"Accept": "text/event-stream"},
        ) as resp:
            resp.raise_for_status()

            buffer = ""
            for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
                if chunk is None:
                    continue
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8")
                buffer += chunk

                # SSE 格式: "data: {...}\\n\\n"
                while "\n\n" in buffer:
                    line, buffer = buffer.split("\n\n", 1)
                    for event_line in line.split("\n"):
                        if event_line.startswith("data: "):
                            try:
                                event_data = json.loads(event_line[6:])
                                yield event_data
                            except json.JSONDecodeError:
                                pass

    def get_checkpoints(self, pid: int) -> Dict[str, Any]:
        """获取项目的检查点/版本列表"""
        data = self.http.get_json(C.PROJECT_CHECKPOINT_LIST, project_id=pid)
        return data.get("data", {})

    # === 偏好设置 ===

    def get_user_preferences(self) -> List[Dict[str, Any]]:
        """获取用户偏好设置"""
        data = self.http.get_json(C.USER_PREFERENCE_LIST)
        if data.get("code") != 0:
            return []
        return data.get("data", {}).get("list", [])

    # === Cookie 导出 ===

    def send_chat_answer(
        self,
        pid: int,
        run_id: str,
        batch_id: str,
        answers: Dict[str, Dict[str, str]],
    ) -> Dict[str, Any]:
        """向 Agent 发送对话答案

        当 Agent 提出选项式问题时，通过此方法回复。

        Args:
            pid: 项目公开 ID
            run_id: 当前运行 ID（从 chat_history 获取）
            batch_id: 批次 ID（Agent 提问的标识）
            answers: 答案映射 {\"question_id\": {\"text\": \"回答内容\"}}

        Example:
            client.send_chat_answer(
                pid=123456789,
                run_id="019e9322...",
                batch_id="019e9322...",
                answers={"019e9322...": {"text": "B - 素材混合MG动画"}},
            )
        """
        payload = {
            "pid": int(pid),
            "run_id": run_id,
            "batch_id": batch_id,
            "answers": answers,
        }
        data = self.http.post_json(C.CHAT_ANSWERS, data=payload, add_csrf=True)
        if data.get("code") != 0:
            raise RuntimeError(f"发送对话答案失败: {data.get('message', data)}")
        logger.info(f"已回复 Agent: run_id={run_id}")
        return data

    def send_chat_message(
        self,
        pid: int,
        message: str,
    ) -> Dict[str, Any]:
        """向 Agent 发送自由文本消息

        Args:
            pid: 项目公开 ID
            message: 消息文本

        Returns:
            {\"code\": 0, \"data\": {\"run_id\": \"...\", \"is_working\": false, \"state\": 0}}
            其中 run_id 可用于后续 listen_sse_events()
        """
        payload = {
            "pid": int(pid),
            "content": [
                {"type": "text", "text": {"content": message}},
            ],
        }
        data = self.http.post_json(C.CHAT_RUN, data=payload, add_csrf=True)
        if data.get("code") != 0:
            raise RuntimeError(f"发送消息失败: {data.get('message', data)}")
        run_id = data.get("data", {}).get("run_id", "")
        logger.info(f"消息已发送: run_id={run_id}")
        return data

    # === 便捷方法 ===

    def confirm_plan(self, pid: int, run_id: str) -> Dict[str, Any]:
        """确认费用计划"""
        data = self.http.post_json(
            C.PROJECT_PLAN_CONFIRM,
            data={"pid": int(pid), "run_id": run_id},
            add_csrf=True,
        )
        if data.get("code") != 0:
            raise RuntimeError(f"确认计划失败: {data}")
        return data

    def create_and_wait(
        self,
        script: str = "",
        audio_url: str = "",
        voice_id: str = "5866601",
        voice_type: int = 0,
        poll_interval: float = 15,
        timeout: float = 3600,
    ) -> Project:
        """一键创建项目并等待视频生成完成

        自动处理 Agent 交互（如果使用 Agent 模式）：
        1. 创建项目
        2. 等待 AI 初始化
        3. 自动确认
        4. 轮询等待完成

        Args:
            script: 视频文案（文稿模式）或素材匹配文案（音频模式）
            audio_url: 音频 URL（HTTP 公网 URL 或 upos://）
            voice_id: TTS 配音 ID（文稿模式）
            voice_type: 0=TTS文稿, 2=口播音频
            poll_interval: 轮询间隔（秒，建议 15s）
            timeout: 总超时（秒）

        Returns:
            完成后的 Project 对象（含 clips）
        """
        # 1. 创建
        project = self.create_project(
            script=script if voice_type == 0 else "",
            voice_id=voice_id,
            voice_type=voice_type,
            audio_url=audio_url,
            user_script=script if voice_type == 2 else "",
        )
        pid = project.pid
        logger.info(f"项目创建: pid={pid}, 等待 AI 初始化...")

        # 2. 等待 AI 就绪
        run_id = ""
        for _ in range(45):
            time.sleep(2)
            try:
                state = self.get_chat_state(pid)
                run_id = state.get("run_id", "")
                chat_state = state.get("state", -1)
                if run_id and chat_state == 0:
                    logger.info(f"AI 就绪: run_id={run_id}")
                    break
            except Exception:
                pass
        else:
            logger.warning("AI 初始化超时，继续尝试...")

        # 3. 自动确认
        time.sleep(2)
        if run_id:
            try:
                self.send_chat_message(pid, "已确认")
                logger.info("已发送自动确认")
            except Exception as e:
                logger.warning(f"自动确认失败（可忽略）: {e}")
        else:
            # 尝试直接确认
            try:
                self.send_chat_message(pid, "已确认")
            except Exception:
                pass

        # 4. 等待完成
        return self.wait_for_completion(pid, interval=poll_interval, timeout=timeout)

    # === 分镜编辑 ===

    def get_clip_candidates(
        self, clip_id: str, page: int = 1, page_size: int = 12
    ) -> Dict[str, Any]:
        """获取分镜的备选素材（替换素材时使用）

        Args:
            clip_id: 分镜 ID（从 project.clips[].id 获取）
            page: 页码
            page_size: 每页数量

        Returns:
            {
                "query": "素材检索词",
                "page": {"total": 60, "pn": 1, "ps": 12},
                "candidates": [{"id", "url", "duration", "width", "height", "fps", "cover", "is_fav"}]
            }
        """
        data = self.http.get_json(C.CLIP_CANDIDATES, clip_id=clip_id, ps=page_size, pn=page)
        if data.get("code") != 0:
            raise RuntimeError(f"获取备选素材失败: {data.get('message', data)}")
        return data.get("data", data)

    def get_clip_render(self, project_id: Union[int, str], clip_id: str) -> Dict[str, Any]:
        """获取分镜渲染后的视频 URL

        返回剪辑后的单个分镜视频，可用于预览。

        Args:
            project_id: 项目 PID
            clip_id: 分镜 ID

        Returns:
            {"composite_video": {"url": "CDN URL", "duration": 0, "state": 2, ...}, "status": 2}
        """
        data = self.http.get_json(
            C.CLIP_RENDER_QUERY,
            project_id=project_id,
            clip_id=clip_id,
        )
        if data.get("code") != 0:
            raise RuntimeError(f"获取分镜渲染失败: {data.get('message', data)}")
        return data.get("data", data)

    def replace_clip_material(
        self,
        clip_id: str,
        clip_video: str,
        start_time: str = "0.000",
        local_duration: float = 0,
        clip_from: int = 0,
    ) -> Dict[str, Any]:
        """替换分镜的素材视频

        从 get_clip_candidates() 中选择一个 candidate uuid，
        调用此方法将其替换为分镜的新素材。

        Args:
            clip_id: 分镜 ID
            clip_video: 候选素材 UUID（从 candidates 的 id 字段获取）
            start_time: 起始时间偏移
            local_duration: 候选素材时长
            clip_from: 素材来源（0=正常）

        Returns:
            空 dict {} 表示成功
        """
        payload = {
            "clip_id": str(clip_id),
            "clip_video": clip_video,
            "clip_from": clip_from,
            "start_time": start_time,
            "local_video_duration": local_duration,
        }
        data = self.http.post_json(C.CLIP_VIDEO_EDIT, data=payload, add_csrf=True)
        logger.info(f"分镜素材已替换: clip={clip_id}, video={clip_video}")
        return data

    def get_savepoints(
        self, pid: int, page: int = 1, page_size: int = 10
    ) -> Dict[str, Any]:
        """获取项目的保存点（书签/版本）列表

        与 checkpoint（undo/redo 历史版本）不同，savepoint 是用户主动标记的版本。

        Args:
            pid: 项目 PID
            page: 页码
            page_size: 每页数量
        """
        data = self.http.get_json(
            C.PROJECT_SAVEPOINT_LIST,
            project_id=pid,
            page=page,
            page_size=page_size,
        )
        return data.get("data", {})

    # === 用户偏好 ===

    def create_preference(self, name: str, content: str) -> Dict[str, Any]:
        """创建创作偏好

        Args:
            name: 偏好名称
            content: 偏好内容描述（素材倾向、MG动画风格、字幕偏好等）

        Returns:
            {"id": 159014067441730} — 新偏好 ID
        """
        payload = {"name": name, "content": content}
        data = self.http.post_json(C.USER_PREFERENCE_CREATE, data=payload, add_csrf=True)
        if data.get("code") != 0:
            raise RuntimeError(f"创建偏好失败: {data.get('message', data)}")
        pref_id = data.get("data", {}).get("id", "")
        logger.info(f"偏好已创建: id={pref_id}, name={name}")
        return data

    def save_cookies(self, filepath: str = "huasheng_cookies.json"):
        """保存当前 cookies 到文件（方便下次复用）"""
        self.http.save_cookies(filepath)
        logger.info(f"Cookies 已保存到 {filepath}")
