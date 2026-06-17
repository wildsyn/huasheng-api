#!/usr/bin/env python3
"""
花生 Agent 对话交互示例

演示完整的 Agent 对话流程：
1. 创建项目
2. 查看 Agent 提问
3. 回复选项
4. 发送自定义消息
5. 监听 SSE 事件流

运行:
  python examples/agent_chat.py
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from huasheng import HuashengClient

logging.basicConfig(level=logging.INFO)


class AgentInteractiveDemo:
    """演示与花生 Agent 的交互式对话"""

    def __init__(self):
        sessdata = os.environ.get("HUASHENG_SESSDATA")
        csrf = os.environ.get("HUASHENG_CSRF")

        if not sessdata or not csrf:
            raise RuntimeError("请设置 HUASHENG_SESSDATA 和 HUASHENG_CSRF 环境变量")

        self.client = HuashengClient(cookies={
            "SESSDATA": sessdata,
            "bili_jct": csrf,
        })
        self.project = None

    def step1_create_project(self, script: str, voice_id: str = "5866601"):
        """步骤 1: 创建视频项目"""
        print(f"📝 创建项目: {script[:50]}...")
        self.project = self.client.create_project(script=script, voice_id=voice_id)
        print(f"   pid={self.project.pid}")
        print(f"   链接: https://www.huasheng.cn/video/{self.project.pid}")
        return self.project

    def step2_check_agent(self):
        """步骤 2: 查看 Agent 的分析结果"""
        print("\n🤖 查看 Agent 分析...")
        history = self.client.get_chat_history(self.project.pid)

        if history.is_working:
            print(f"   Agent 工作中, run_id={history.current_run_id}")
        else:
            print(f"   Agent 空闲")

        for i, run in enumerate(history.runs):
            print(f"   第 {i+1} 轮 run_id={run.run_id}")
            if run.input:
                print(f"      script={run.input.script[:60]}...")
                print(f"      voice={run.input.voice_name}")

        return history

    def step3_answer_option(self, run_id: str, batch_id: str, question_id: str, answer: str):
        """步骤 3: 回复 Agent 的选项"""
        print(f"\n✏️ 回复 Agent 选项: {answer[:60]}...")
        result = self.client.send_chat_answer(
            pid=self.project.pid,
            run_id=run_id,
            batch_id=batch_id,
            answers={question_id: {"text": answer}},
        )
        print(f"   ✅ 已发送")

    def step4_send_message(self, message: str):
        """步骤 4: 发送自由文本消息"""
        print(f"\n💬 发送消息: {message}")
        result = self.client.send_chat_message(self.project.pid, message)
        run_id = result.get("data", {}).get("run_id", "")
        print(f"   ✅ run_id={run_id}")
        return run_id

    def step5_listen_sse(self, run_id: str, max_events: int = 20):
        """步骤 5: 监听 SSE 实时事件流"""
        print(f"\n📡 监听 SSE 事件流 (最多 {max_events} 个事件)...")
        count = 0
        try:
            for event in self.client.get_chat_events_sse(run_id, self.project.pid):
                count += 1
                event_type = event.get("type", "unknown")

                # 打印事件摘要
                if event_type == "agent_message":
                    content = event.get("content", "")
                    print(f"   [{count}] Agent: {content[:80]}...")
                elif event_type == "tool_call":
                    tool = event.get("tool", "")
                    print(f"   [{count}] Tool: {tool}")
                elif event_type == "progress":
                    step = event.get("step", "")
                    pct = event.get("percent", 0)
                    print(f"   [{count}] Progress: {step} — {pct}%")
                else:
                    print(f"   [{count}] {json.dumps(event, ensure_ascii=False)[:150]}")

                if count >= max_events:
                    print(f"   ⏸ 已达到最大事件数 {max_events}，停止监听")
                    break
        except Exception as e:
            print(f"   ⚠️ SSE 中断: {e}")

        print(f"   共收到 {count} 个事件")


def main():
    demo = AgentInteractiveDemo()

    # 创建项目
    script = """
人工智能技术正在改变我们的生活方式。
从智能手机到自动驾驶汽车，AI的应用越来越广泛。
未来十年，我们将会看到更多令人惊叹的技术突破。
""".strip()
    demo.step1_create_project(script)

    # 查看 Agent 分析
    history = demo.step2_check_agent()
    print(f"\n👉 Agent 正在分析文案并可能提问")
    print(f"   查看 https://www.huasheng.cn/video/{demo.project.pid} 可以看到完整对话")


if __name__ == "__main__":
    main()
