#!/usr/bin/env python3
"""
花生端到端测试 — 使用真实音频+文稿，测试完整管道到可下载链接

流程: preupload → upload音频 → create项目 → wait完成 → export → CDN URL
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from urllib.parse import quote, urlencode

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

HUASHENG = "https://www.huasheng.cn"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)


def extract_srt_text(srt_path: str) -> str:
    """从 SRT 字幕文件中提取纯文本"""
    with open(srt_path, "r") as f:
        content = f.read()
    lines = content.split("\n")
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line or line.isdigit() or "-->" in line:
            continue
        text_lines.append(line)
    return "".join(text_lines)


class HuashengE2E:
    """花生端到端：上传 + 创建 + 等待 + 导出"""

    def __init__(self, sessdata: str, bili_jct: str):
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": UA,
            "Referer": f"{HUASHENG}/",
            "Origin": HUASHENG,
            "Accept": "application/json",
        })
        self.sess.cookies.set("SESSDATA", sessdata, domain=".huasheng.cn")
        self.sess.cookies.set("SESSDATA", sessdata, domain=".bilibili.com")
        self.sess.cookies.set("bili_jct", bili_jct, domain=".huasheng.cn")
        self.sess.cookies.set("bili_jct", bili_jct, domain=".bilibili.com")
        self.csrf = bili_jct

    def preupload(self, filepath: str) -> dict:
        fsize = os.path.getsize(filepath)
        fname = os.path.basename(filepath)
        params = {
            "name": fname, "size": fsize, "r": "upos",
            "profile": "bilistudio/bup", "ssl": "0",
            "version": "3.0.1", "build": "3000100",
        }
        url = f"{HUASHENG}/api/innovideo/preupload?{urlencode(params)}"
        r = self.sess.get(url)
        r.raise_for_status()
        data = r.json()
        if not data.get("OK"):
            raise RuntimeError(f"preupload 失败: {data}")
        logger.info(f"✅ preupload OK: endpoint={data.get('endpoint', '?')}")
        return data

    def upload_file(self, filepath: str, pre: dict) -> str:
        fsize = os.path.getsize(filepath)
        fname = os.path.basename(filepath)
        endpoint = pre["endpoint"].replace("//", "https://")
        upos_uri = pre["upos_uri"]
        upos_path = upos_uri.split("://", 1)[1]

        init_url = f"{endpoint}/{upos_path}?uploads&output=json"
        r = self.sess.post(init_url)
        r.raise_for_status()
        upload_id = r.json().get("uploadId", "")
        logger.info(f"  upload init: uploadId={upload_id[:16]}...")

        chunk_url = (
            f"{endpoint}/{upos_path}"
            f"?partNumber=1&uploadId={upload_id}&chunk=0&chunks=1"
            f"&size={fsize}&start=0&end={fsize}&total={fsize}"
        )
        with open(filepath, "rb") as f:
            r = self.sess.put(chunk_url, data=f.read())
        r.raise_for_status()

        complete_url = (
            f"{endpoint}/{upos_path}?output=json&name={quote(fname)}"
            f"&profile=bilistudio%2Fbup&uploadId={upload_id}&biz_id="
        )
        r = self.sess.post(complete_url)
        r.raise_for_status()
        logger.info(f"  upload complete: HTTP {r.status_code}")
        return upos_uri

    def create_project(self, upos_url: str, user_script: str, audio_duration: float = 0) -> dict:
        payload = {
            "name": "", "is_denoise": 0, "script": "", "voice_type": 2,
            "audio_url": upos_url, "speech_rate": 1, "speech_rate_change": 1,
            "user_script": user_script, "user_script_type": 1,
            "project_type": 0, "is_agree": 0, "is_multi": 0,
            "audio_duration": audio_duration,
        }
        url = f"{HUASHENG}/api/huasheng/project/create?csrf={self.csrf}"
        r = self.sess.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"创建项目失败: {data}")
        pid = data["data"]["pid"]
        logger.info(f"✅ 项目创建成功: pid={pid}")
        return {"pid": pid}

    def wait_for_ai_and_confirm(self, pid: int) -> str:
        run_id = ""
        logger.info("等待 AI 初始化...")
        for i in range(45):
            time.sleep(2)
            try:
                r = self.sess.get(f"{HUASHENG}/api/huasheng/chat/state", params={"pid": pid})
                d = r.json().get("data", {})
                run_id = d.get("run_id", "")
                state = d.get("state", -1)
                if run_id and state == 0:
                    logger.info(f"AI 就绪: run_id={run_id}")
                    break
            except Exception:
                pass
            if i % 5 == 4:
                logger.info(f"  等待中... ({(i+1)*2}s)")
        else:
            raise RuntimeError("AI 初始化超时（90s）")

        time.sleep(2)
        r = self.sess.post(
            f"{HUASHENG}/api/huasheng/chat/run?csrf={self.csrf}",
            json={"pid": int(pid), "content": [{"type": "text", "text": {"content": "已确认"}}]},
        )
        r.raise_for_status()
        data = r.json()
        if data.get("code") != 0:
            raise RuntimeError(f"确认失败: {data}")
        logger.info(f"✅ 已发送确认")
        return run_id

    def wait_for_completion(self, pid: int, poll_interval: int = 15, timeout: int = 3600) -> dict:
        deadline = time.time() + timeout
        last_progress = -1
        while time.time() < deadline:
            r = self.sess.get(f"{HUASHENG}/api/innovideo/project/info", params={"pid": pid})
            r.raise_for_status()
            raw = r.json()
            proj = raw.get("project", {}) or raw.get("data", {}).get("project", {})
            progress = proj.get("progress", 0)
            state = str(proj.get("state", -1))
            state_msg = proj.get("state_message", "")
            internal_id = proj.get("id", "")

            if progress != last_progress:
                logger.info(f"📹 进度: {progress}% — {state_msg}")
                last_progress = progress

            if state == "0" and "完成" in state_msg:
                logger.info(f"✅ 项目完成! internal_id={internal_id}")
                return {"id": internal_id, "pid": pid}

            if "失败" in state_msg:
                raise RuntimeError(f"项目失败: {state_msg}")

            time.sleep(poll_interval)
        raise TimeoutError(f"等待超时 ({timeout}s)")

    def export_video(self, project_id) -> dict:
        r = self.sess.post(
            f"{HUASHENG}/api/innovideo/project/export/video/task?csrf={self.csrf}",
            json={"id": int(project_id), "watermark": 1, "ai_watermark": 0},
        )
        r.raise_for_status()
        data = r.json()
        task_id = data.get("task_id", "")
        if not task_id and "data" in data:
            task_id = data["data"].get("task_id", "")
        if not task_id:
            raise RuntimeError(f"导出任务创建失败: {data}")
        logger.info(f"✅ 导出任务创建: task_id={task_id}")
        return {"task_id": task_id, "version": data.get("version", "2"), "project_hash": data.get("project_hash", "")}

    def wait_for_export(self, project_id, task_id: str, project_hash: str = "", timeout: int = 600) -> str:
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = self.sess.get(
                f"{HUASHENG}/api/innovideo/project/export/video/info",
                params={"id": str(project_id), "task_id": task_id, "project_hash": project_hash},
            )
            r.raise_for_status()
            data = r.json()
            progress = int(data.get("progress", 0))
            url = data.get("url", "")
            if progress >= 100 and url:
                logger.info(f"✅ 导出完成! CDN URL 已获取")
                return url
            logger.info(f"  导出进度: {progress}%")
            time.sleep(5)
        raise TimeoutError(f"导出超时 ({timeout}s)")

    def run(self, audio_path: str, script: str) -> dict:
        logger.info("=" * 60)
        logger.info("🚀 花生端到端测试开始")
        logger.info(f"   音频: {os.path.basename(audio_path)}")
        logger.info(f"   文稿长度: {len(script)} 字")
        logger.info("=" * 60)

        logger.info("\n📤 Step 1-2: 上传音频到 CDN...")
        pre = self.preupload(audio_path)
        upos_url = self.upload_file(audio_path, pre)
        logger.info(f"   upos_url: {upos_url[:60]}...")

        logger.info("\n📝 Step 3: 创建花生项目...")
        fsize = os.path.getsize(audio_path)
        est_duration = fsize / (128 * 1000 / 8) if fsize > 0 else 0
        create_result = self.create_project(upos_url, script, round(est_duration, 3))
        pid = create_result["pid"]

        logger.info("\n🤖 Step 4-5: AI 初始化 + 确认 + 等待制作...")
        self.wait_for_ai_and_confirm(pid)
        proj_info = self.wait_for_completion(pid)
        internal_id = proj_info.get("id", "")

        logger.info("\n📦 Step 6-7: 导出视频 + 获取 CDN 链接...")
        export = self.export_video(internal_id or pid)
        cdn_url = self.wait_for_export(internal_id or pid, export["task_id"], export.get("project_hash", ""))

        logger.info("\n" + "=" * 60)
        logger.info("🎉 端到端测试完成!")
        logger.info(f"   项目链接: https://www.huasheng.cn/video/{pid}")
        logger.info(f"   PID: {pid}")
        logger.info(f"   CDN 下载链接: {cdn_url}")
        logger.info("=" * 60)

        return {"pid": pid, "project_url": f"https://www.huasheng.cn/video/{pid}", "cdn_download_url": cdn_url, "upos_url": upos_url}


def main():
    audio_path = "/Users/zxdwhda/Downloads/7月11日.mp3"
    srt_path = "/Users/zxdwhda/Downloads/Agent、Skill、Harness啥意思？一次性讲明白AI技术名词！.srt"

    if not Path(audio_path).exists():
        logger.error(f"音频文件不存在: {audio_path}")
        sys.exit(1)
    if not Path(srt_path).exists():
        logger.error(f"字幕文件不存在: {srt_path}")
        sys.exit(1)

    script = extract_srt_text(srt_path)
    logger.info(f"提取文稿: {len(script)} 字")
    logger.info(f"文稿预览: {script[:100]}...")

    sessdata = os.environ.get("HUASHENG_SESSDATA", "")
    bili_jct = os.environ.get("HUASHENG_BILI_JCT", "")

    if not sessdata or not bili_jct:
        logger.error("缺少 HUASHENG_SESSDATA 或 HUASHENG_BILI_JCT")
        sys.exit(1)

    try:
        e2e = HuashengE2E(sessdata=sessdata, bili_jct=bili_jct)
        result = e2e.run(audio_path, script)

        output_path = "/Users/zxdwhda/wildflow/huasheng-api/tests/e2e_result.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        logger.info(f"结果已保存: {output_path}")

        print("\n" + "=" * 60)
        print("📋 最终结果:")
        print(f"   PID: {result['pid']}")
        print(f"   项目链接: {result['project_url']}")
        print(f"   CDN 下载链接: {result['cdn_download_url']}")
        print("=" * 60)

        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
