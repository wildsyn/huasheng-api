"""
花生 (Huasheng) Python SDK
==========================
B站官方 AI 视频创作工具「花生」的非官方 Python API 封装。

基于对 huasheng.cn 网页应用的 API 逆向分析，
提供视频自动化创作的完整能力。

Usage::

    from huasheng import HuashengClient

    client = HuashengClient(cookies={"SESSDATA": "your_sessdata"})
    # 创建视频项目
    project = client.create_project(script="你的视频文案...")
    # 等待生成完成
    result = client.wait_for_completion(project.pid)
"""

__version__ = "0.1.0"
__author__ = "huasheng-api contributors"

from .client import HuashengClient
from .models import Project, UserInfo, VipInfo, Voice, BGM, ChatRun
