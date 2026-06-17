#!/usr/bin/env python3
"""
花生云端连通性测试

测试完整流程：上传音频 + 文案 → 创建项目 → 输出 PID

用法：
  python tests/test_cloud_flow.py <音频文件路径> <文案文本> [--cookie SESSDATA] [--csrf bili_jct]

环境变量：
  HUASHENG_SESSDATA  — B站 SESSDATA cookie
  HUASHENG_BILI_JCT  — B站 bili_jct (CSRF token)

示例：
  python tests/test_cloud_flow.py ~/Downloads/荆轲.mp3 "荆轲刺秦王..."
"""

import os
import sys
import json
import time
import hashlib
import logging
import argparse
from pathlib import Path
from urllib.parse import quote, urlencode

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── 常量 ─────────────────────────────────────────────
HUASHENG = "https://www.huasheng.cn"
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
)


class HuashengUploader:
    """花生音频上传 + 项目创建"""

    def __init__(self, sessdata: str, bili_jct: str):
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": UA,
            "Referer": f"{HUASHENG}/",
            "Origin": HUASHENG,
        })
        self.sess.cookies.set("SESSDATA", sessdata, domain=".huasheng.cn")
        self.sess.cookies.set("SESSDATA", sessdata, domain=".bilibili.com")
        self.sess.cookies.set("bili_jct", bili_jct, domain=".huasheng.cn")
        self.sess.cookies.set("bili_jct", bili_jct, domain=".bilibili.com")
        self.csrf = bili_jct

    # ── 步骤 1: 预上传（获取 upos CDN 地址）─────────────────

    def preupload(self, filepath: str) -> dict:
        """获取 B站 upos 上传 URL"""
        fsize = os.path.getsize(filepath)
        fname = os.path.basename(filepath)
        params = {
            "name": fname,
            "size": fsize,
            "r": "upos",
            "profile": "bilistudio/bup",
            "ssl": "0",
            "version": "3.0.1",
            "build": "3000100",
        }
        url = f"{HUASHENG}/api/innovideo/preupload?{urlencode(params)}"
        r = self.sess.get(url)
        r.raise_for_status()
        data = r.json()
        if not data.get("OK"):
            raise RuntimeError(f"preupload 失败: {data}")
        logger.info(f"preupload OK: endpoint={data.get('endpoint', '?')}")
        return data

    def upload_file(self, filepath: str, pre: dict) -> str:
        """上传音频到 upos CDN，返回 upos:// URI"""
        fsize = os.path.getsize(filepath)
        fname = os.path.basename(filepath)
        endpoint = pre["endpoint"].replace("//", "https://")
        upos_uri = pre["upos_uri"]
        put_query = pre.get("put_query", "os=upos")

        # Step A: init upload
        init_url = f"{endpoint}/{upos_uri.split('://', 1)[1]}?uploads&output=json"
        r = self.sess.post(init_url)
        r.raise_for_status()
        init_data = r.json()
        upload_id = init_data.get("uploadId", "")
        logger.info(f"upload init: uploadId={upload_id[:16]}...")

        # Step B: upload chunk (single chunk for <10MB files)
        chunk_url = (
            f"{endpoint}/{upos_uri.split('://', 1)[1]}"
            f"?partNumber=1&uploadId={upload_id}&chunk=0&chunks=1"
            f"&size={fsize}&start=0&end={fsize}&total={fsize}"
        )
        with open(filepath, "rb") as f:
            r = self.sess.put(chunk_url, data=f.read())
        r.raise_for_status()
        logger.info(f"upload chunk: HTTP {r.status_code}")

        # Step C: complete upload
        complete_url = (
            f"{endpoint}/{upos_uri.split('://', 1)[1]}"
            f"?output=json&name={quote(fname)}&profile=bilistudio%2Fbup"
            f"&uploadId={upload_id}&biz_id="
        )
        r = self.sess.post(complete_url)
        r.raise_for_status()
        logger.info(f"upload complete: HTTP {r.status_code}")

        return upos_uri

    # ── 步骤 2: 创建项目 ──────────────────────────────────

    def create_project(
        self,
        upos_url: str,
        user_script: str,
        audio_duration: float = 0,
        user_script_type: int = 1,
    ) -> dict:
        """创建花生项目，返回 {pid, project_id}"""
        payload = {
            "name": "",
            "is_denoise": 0,
            "script": "",
            "voice_type": 2,
            "audio_url": upos_url,
            "speech_rate": 1,
            "speech_rate_change": 1,
            "user_script": user_script,
            "user_script_type": user_script_type,
            "project_type": 0,
            "is_agree": 0,
            "is_multi": 0,
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

    # ── 完整流程 ──────────────────────────────────────────

    def run(self, audio_path: str, script: str) -> dict:
        """完整流程：上传 → 创建 → 返回 PID"""
        # 1. Preupload
        logger.info("=" * 50)
        logger.info("步骤 1/4: 预上传（获取 CDN 地址）...")
        pre = self.preupload(audio_path)

        # 2. Upload
        logger.info("步骤 2/4: 上传音频...")
        upos_url = self.upload_file(audio_path, pre)

        # 3. Create
        logger.info("步骤 3/4: 创建花生项目...")
        fsize = os.path.getsize(audio_path)
        # 粗略估算时长（128kbps MP3）
        est_duration = fsize / (128 * 1000 / 8) if fsize > 0 else 0
        result = self.create_project(
            upos_url=upos_url,
            user_script=script,
            audio_duration=round(est_duration, 3),
        )

        # 4. Done
        pid = result["pid"]
        logger.info("=" * 50)
        logger.info(f"🎉 完成！项目链接: https://www.huasheng.cn/video/{pid}")
        logger.info(f"   PID: {pid}")
        logger.info("=" * 50)
        return result


def main():
    parser = argparse.ArgumentParser(description="花生云端连通性测试")
    parser.add_argument("audio", help="音频文件路径 (.mp3)")
    parser.add_argument("script", help="视频文案文本")
    parser.add_argument("--sessdata", help="B站 SESSDATA cookie", default=None)
    parser.add_argument("--csrf", help="B站 bili_jct", default=None)
    parser.add_argument("--output", help="输出 JSON 结果文件", default=None)
    args = parser.parse_args()

    # 读取 cookie
    sessdata = args.sessdata or os.environ.get("HUASHENG_SESSDATA")
    bili_jct = args.csrf or os.environ.get("HUASHENG_BILI_JCT")

    if not sessdata or not bili_jct:
        logger.error("请设置 SESSDATA 和 CSRF")
        logger.error("  环境变量: HUASHENG_SESSDATA, HUASHENG_BILI_JCT")
        logger.error("  或参数: --sessdata xxx --csrf xxx")
        sys.exit(1)

    # 检查音频文件
    audio_path = Path(args.audio)
    if not audio_path.exists():
        logger.error(f"音频文件不存在: {audio_path}")
        sys.exit(1)

    script_text = args.script
    if len(script_text) < 10:
        logger.warning("⚠️  文案太短（<10字），可能影响生成质量")

    logger.info(f"音频: {audio_path.name} ({audio_path.stat().st_size} bytes)")
    logger.info(f"文案: {script_text[:50]}...")
    logger.info(f"Cookie: SESSDATA={sessdata[:5]}... bili_jct={bili_jct[:5]}...")

    try:
        uploader = HuashengUploader(sessdata=sessdata, bili_jct=bili_jct)
        result = uploader.run(str(audio_path), script_text)

        if args.output:
            with open(args.output, "w") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            logger.info(f"结果已保存到: {args.output}")

        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
