import json
from playwright.sync_api import sync_playwright

def save_cookies():
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 访问B站
        page.goto("https://www.bilibili.com/")
        
        print("请在浏览器中手动登录B站")
        print("登录成功后，按回车键继续...")
        input()
        
        # 保存Cookies
        cookies = context.cookies()
        with open('bilibili_cookies.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f)
        
        print("Cookies已成功保存到 bilibili_cookies.json")
        browser.close()

if __name__ == "__main__":
    save_cookies()