import json
import time
from playwright.sync_api import sync_playwright

def auto_login_with_cookies():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        
        # 加载Cookies
        try:
            with open('bilibili_cookies.json', 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            print("Cookies加载成功")
        except Exception as e:
            print(f"加载Cookies失败: {e}")
            browser.close()
            return
        
        # 打开目标视频页面
        page = context.new_page()
        page.goto("https://www.bilibili.com/video/BV1PMZBYNEpM/")
        
        # 等待页面完全加载
        page.wait_for_load_state("networkidle")
        # 增加短暂延迟确保JS执行完毕
        time.sleep(2)
        
        # 更全面地检查登录状态
        # 尝试多种可能的选择器
        login_selectors = ['.header-avatar', '.v-popover-wrap', '.bili-avatar', 
                          '.user-name', '.vip-icon', '.avatar-icon']
        
        is_logged_in = False
        for selector in login_selectors:
            if page.query_selector(selector):
                is_logged_in = True
                print(f"登录成功! 找到登录元素: {selector}")
                break
        
        if not is_logged_in:
            # 另一种检测方法：检查是否存在登录按钮
            login_button = page.query_selector('span.header-login-entry')
            if login_button:
                print("登录失败，页面上仍有登录按钮")
            else:
                print("可能已登录，但无法确认。请观察浏览器窗口")
        
        print("按回车键关闭浏览器...")
        input()
        browser.close()

if __name__ == "__main__":
    auto_login_with_cookies()