#!/usr/bin/env python3
"""
花生 SDK 基础使用示例

演示：
1. 初始化客户端（从环境变量读取 Cookie）
2. 检查登录状态
3. 获取音色列表
4. 创建视频项目
5. 与 Agent 交互
6. 监听生成进度

使用前设置环境变量:
  export HUASHENG_SESSDATA="your_sessdata"
  export HUASHENG_CSRF="your_bili_jct"

运行:
  python examples/basic_usage.py
"""

import os
import sys
import json
import logging

# 添加父目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from huasheng import HuashengClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)


def main():
    # === 1. 初始化 ===
    sessdata = os.environ.get("HUASHENG_SESSDATA")
    csrf = os.environ.get("HUASHENG_CSRF")

    if not sessdata or not csrf:
        print("❌ 请设置环境变量:")
        print("   export HUASHENG_SESSDATA='your_sessdata'")
        print("   export HUASHENG_CSRF='your_bili_jct'")
        print("\n获取方法: 浏览器 F12 → Application → Cookies → huasheng.cn")
        sys.exit(1)

    client = HuashengClient(cookies={
        "SESSDATA": sessdata,
        "bili_jct": csrf,
    })

    # === 2. 检查登录 ===
    if not client.check_login():
        print("❌ Cookie 无效或已过期，请重新获取")
        sys.exit(1)

    user = client.get_user_info()
    print(f"✅ 已登录: {user.uname} (Lv.{user.level})")
    print(f"   大会员: {'是' if user.vip_status else '否'} — {user.vip_label_text}")

    # === 3. VIP 积分 ===
    vip = client.get_vip_info()
    print(f"\n💰 花生积分: {vip.total_points}")
    print(f"   套餐积分: {vip.package_points}")
    print(f"   试用次数: {vip.trials}")

    # === 4. 音色列表 ===
    print("\n🎙️ 可用 TTS 音色:")
    voices = client.get_tts_voices()
    for v in voices[:10]:
        print(f"   [{v.id}] {v.name} — {v.tags or '无标签'}")

    # === 5. 应用配置 ===
    config = client.get_app_config()
    print(f"\n⚙️ 文案最大字数: {config.get('script_max', 'N/A')}")
    print(f"   音频文案最大: {config.get('audio_script_max', 'N/A')}")

    # === 6. 创建视频项目 ===
    script = """
人工智能技术正在改变我们的生活方式。
从智能手机到自动驾驶汽车，AI的应用越来越广泛。
未来十年，我们将会看到更多令人惊叹的技术突破。
无论面对什么样的技术，我们都要问一句：
数字化发展到底是为了谁？
数字化的发展，出发点和立足点都应当是人的全面发展。
""".strip()

    print(f"\n🎬 创建视频项目...")
    print(f"   文案: {script[:50]}...")

    project = client.create_project(
        script=script,
        voice_id="5866601",  # 清亮男声 - 默认 ID
    )
    print(f"   ✅ 项目已创建: pid={project.pid}")
    print(f"   🔗 编辑链接: https://www.huasheng.cn/video/{project.pid}")
    print(f"   📊 初始状态: {project.state_message}")

    # === 7. 查看 Agent 分析 ===
    print(f"\n🤖 Agent 分析中...")
    history = client.get_chat_history(project.pid)
    print(f"   is_working: {history.is_working}")
    print(f"   对话轮次: {len(history.runs)}")

    for i, run in enumerate(history.runs):
        inp = run.input
        if inp:
            print(f"   第 {i+1} 轮: {inp.script[:40] if inp.script else '(无文案)'}...")

    # === 8. 如果需要回复 Agent ===
    if history.is_working and history.current_run_id:
        print(f"\n💬 Agent 等待回复，当前 run_id: {history.current_run_id}")
        print(f"   使用以下方法回复:")
        print(f"   - client.send_chat_answer()  回复选项")
        print(f"   - client.send_chat_message() 发送文本")

        # 示例: 发送确认消息
        # result = client.send_chat_message(project.pid, "确认，开始制作")
        # run_id = result["data"]["run_id"]
        #
        # # 监听 SSE 实时事件
        # for event in client.get_chat_events_sse(run_id, project.pid):
        #     print(f"   SSE: {json.dumps(event, ensure_ascii=False)[:200]}")

    # === 9. 轮询等待完成 ===
    print(f"\n⏳ 轮询等待项目完成 (最多 300 秒)...")
    try:
        project = client.wait_for_completion(project.pid, timeout=300)
        print(f"   ✅ 项目完成!")
        print(f"   片段数: {len(project.clips)}")
        print(f"   状态: {project.state_message}")
    except TimeoutError:
        print(f"   ⚠️ 超时，项目可能仍在处理中")
        print(f"   可稍后手动检查: client.get_project({project.pid})")

    # === 10. 保存 Cookie (方便下次复用) ===
    client.save_cookies("huasheng_cookies.json")
    print(f"\n💾 Cookies 已保存到 huasheng_cookies.json")


if __name__ == "__main__":
    main()
