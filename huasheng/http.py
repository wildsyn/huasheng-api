"""
花生 HTTP 工具
============
Session 管理、Cookie 处理、请求封装。
"""

import time
import json
import requests
from typing import Optional, Dict, Any
from . import constants as C


class HuashengHTTP:
    """花生 HTTP 请求封装，管理 Cookie/Session/CSRF"""

    def __init__(
        self,
        cookies: Optional[Dict[str, str]] = None,
        cookie_file: Optional[str] = None,
        timeout: int = 30,
        proxy: Optional[str] = None,
    ):
        self.session = requests.Session()
        self.timeout = timeout

        # 设置 UA（模拟 Chrome）
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/148.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": C.BASE_WWW + "/",
        })

        # 代理
        if proxy:
            self.session.proxies = {
                "http": proxy,
                "https": proxy,
            }

        # Cookie
        if cookie_file:
            self._load_cookies_from_file(cookie_file)
        elif cookies:
            self._set_cookies(cookies)

        # 从 cookie 中提取 CSRF token
        self._csrf = self._extract_csrf()

    # --- Cookie 管理 ---

    def _set_cookies(self, cookies: Dict[str, str]):
        """设置 cookies"""
        for key, value in cookies.items():
            self.session.cookies.set(key, value, domain=".huasheng.cn")
            self.session.cookies.set(key, value, domain=".bilibili.com")

    def _load_cookies_from_file(self, filepath: str):
        """从 JSON 文件加载 cookies"""
        import os
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Cookie 文件不存在: {filepath}")
        with open(filepath, "r") as f:
            cookies = json.load(f)
        self._set_cookies(cookies)

    def save_cookies(self, filepath: str):
        """保存当前 cookies 到 JSON 文件"""
        cookies = {}
        for cookie in self.session.cookies:
            cookies[cookie.name] = cookie.value
        with open(filepath, "w") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

    def _extract_csrf(self) -> str:
        """从 cookie 中提取 bili_jct（即 CSRF token）"""
        for cookie in self.session.cookies:
            if cookie.name == "bili_jct":
                return cookie.value
        return ""

    @property
    def csrf(self) -> str:
        """获取当前 CSRF token"""
        if not self._csrf:
            self._csrf = self._extract_csrf()
        return self._csrf

    # --- HTTP 方法 ---

    def _build_url(self, endpoint: str, **params) -> str:
        """构建 URL，自动附加 csrf"""
        all_params = {k: v for k, v in params.items() if v is not None}
        # 对需要 csrf 的 POST 接口附加 csrf
        if "csrf" not in all_params and not endpoint.startswith("http"):
            pass  # csrf 由具体方法处理
        if all_params:
            from urllib.parse import urlencode
            return f"{endpoint}?{urlencode(all_params)}"
        return endpoint

    def get(self, endpoint: str, **params) -> requests.Response:
        """GET 请求"""
        url = endpoint
        if params:
            from urllib.parse import urlencode
            url = f"{endpoint}?{urlencode({k: v for k, v in params.items() if v is not None})}"
        resp = self.session.get(url, timeout=self.timeout)
        return resp

    def post(self, endpoint: str, data: Optional[Dict] = None, add_csrf: bool = False, **params) -> requests.Response:
        """POST 请求"""
        url = endpoint
        all_params = {k: v for k, v in params.items() if v is not None}
        if add_csrf and self.csrf:
            all_params["csrf"] = self.csrf
        if all_params:
            from urllib.parse import urlencode
            url = f"{endpoint}?{urlencode(all_params)}"
        resp = self.session.post(
            url,
            json=data,
            timeout=self.timeout,
            headers={"Content-Type": "application/json"} if data else {},
        )
        return resp

    def get_json(self, endpoint: str, **params) -> Dict[str, Any]:
        """GET 请求并返回 JSON"""
        resp = self.get(endpoint, **params)
        resp.raise_for_status()
        return resp.json()

    def post_json(self, endpoint: str, data: Optional[Dict] = None, add_csrf: bool = False, **params) -> Dict[str, Any]:
        """POST 请求并返回 JSON"""
        resp = self.post(endpoint, data=data, add_csrf=add_csrf, **params)
        resp.raise_for_status()
        return resp.json()

    # --- 认证检查 ---

    def check_login(self) -> bool:
        """检查是否已登录"""
        try:
            data = self.get_json(C.USER_NAV)
            return data.get("code") == 0 and data.get("data", {}).get("isLogin", False)
        except Exception:
            return False
