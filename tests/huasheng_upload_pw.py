#!/usr/bin/env python3
"""花生音频上传 — Playwright headless 浏览器版
用法: python3 huasheng_upload_pw.py <音频文件> <文案> [--sessdata] [--csrf]
输出: {"pid": 159xxx, "upos_url": "upos://..."}

在服务器上直接运行 headless Chromium 完成上传+创建。
"""
import os, sys, json, time, logging, argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
L = logging.getLogger()

HUASHENG = "https://www.huasheng.cn"


def upload_and_create(audio_path: str, script_text: str, sessdata: str, bili_jct: str) -> dict:
    audio_abs = str(Path(audio_path).resolve())

    with sync_playwright() as p:
        L.info("启动 Chromium headless...")
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
            ),
        )

        # 注入 B站 cookies
        for domain in [".bilibili.com", ".huasheng.cn"]:
            context.add_cookies([
                {"name": "SESSDATA", "value": sessdata, "domain": domain, "path": "/"},
                {"name": "bili_jct", "value": bili_jct, "domain": domain, "path": "/"},
            ])

        page = context.new_page()
        upos_url = None
        project_pid = None

        # 拦截 create_project 响应，捕获 PID
        def on_response(resp):
            nonlocal project_pid
            if "project/create" in resp.url and resp.status == 200:
                try:
                    data = resp.json()
                    if data.get("code") == 0:
                        project_pid = data["data"]["pid"]
                        L.info(f"捕获 PID: {project_pid}")
                except Exception:
                    pass

        # 拦截 create_project 请求，捕获 upos_url
        def on_request(req):
            nonlocal upos_url
            if "project/create" in req.url and req.method == "POST":
                try:
                    body = json.loads(req.post_data or "{}")
                    au = body.get("audio_url", "")
                    if au.startswith("upos://"):
                        upos_url = au
                        L.info(f"捕获 upos_url: {upos_url[:60]}...")
                except Exception:
                    pass

        page.on("response", on_response)
        page.on("request", on_request)

        # 1. 打开首页
        L.info("打开 huasheng.cn...")
        page.goto(HUASHENG, wait_until="networkidle")
        page.wait_for_timeout(2000)

        # 2. 切换到上传口播模式
        L.info("切换到上传口播...")
        page.locator("text=上传口播").first.click()
        page.wait_for_timeout(1000)

        # 3. 上传音频文件
        L.info(f"上传音频: {os.path.basename(audio_path)}")
        page.locator("input[type=file]").set_input_files(audio_abs)

        # 等文件名出现在页面上 = 上传完成
        fname = os.path.basename(audio_path)
        page.wait_for_selector(f"text={fname}", timeout=60000)
        page.wait_for_timeout(3000)
        L.info("上传完成")

        # 4. 展开文案输入
        L.info("添加文案...")
        page.locator("text=添加对应文稿").first.click()
        page.wait_for_timeout(1000)

        # 5. 输入文案
        textarea = page.locator("textarea").last
        textarea.fill(script_text)
        page.wait_for_timeout(500)

        # 关闭弹窗
        confirm_btn = page.locator("text=确定").last
        if confirm_btn.is_visible():
            confirm_btn.click()
            page.wait_for_timeout(1000)

        # 6. 点击创建
        L.info("点击创建...")
        page.locator("button:has-text('创建')").first.click()

        # 等待 API 响应
        page.wait_for_timeout(10000)

        browser.close()

        if project_pid:
            L.info(f"SUCCESS: pid={project_pid}")
            return {"pid": project_pid, "upos_url": upos_url or ""}
        else:
            L.error("未捕获到 PID")
            return {"error": "no_pid", "upos_url": upos_url or ""}


def main():
    parser = argparse.ArgumentParser(description="花生浏览器上传")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("script", help="视频文案")
    parser.add_argument("--sessdata", default="")
    parser.add_argument("--csrf", default="")
    args = parser.parse_args()

    sessdata = args.sessdata or os.environ.get("HUASHENG_SESSDATA", "")
    bili_jct = args.csrf or os.environ.get("HUASHENG_BILI_JCT", "")

    if not sessdata or not bili_jct:
        L.error("缺少 SESSDATA 或 bili_jct")
        sys.exit(1)

    audio = Path(args.audio)
    if not audio.exists():
        L.error(f"文件不存在: {audio}")
        sys.exit(1)

    result = upload_and_create(str(audio), args.script, sessdata, bili_jct)
    print(json.dumps(result, ensure_ascii=False))
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
