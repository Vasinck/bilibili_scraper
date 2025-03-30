import json
import time
import re
from playwright.sync_api import sync_playwright

def get_video_url():
    return input("请输入视频链接：").strip().split('?')[0]

def extract_bilibili_comments_with_replies():
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
        
        # 打开目标视频页面，获取视频的oid（视频实际ID）
        print("获取视频oid...")
        page = context.new_page()
        page.goto(get_video_url())
        
        # 等待页面加载
        page.wait_for_load_state("networkidle")
        
        # 从页面中提取oid
        oid = page.evaluate("""() => {
            // 尝试从页面中获取视频aid (oid)
            if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.aid) {
                return window.__INITIAL_STATE__.aid;
            }
            return null;
        }""")
        
        if not oid:
            print("无法获取视频oid，尝试从页面源代码中获取...")
            content = page.content()
            # 尝试从页面源代码中提取aid
            aid_match = re.search(r'"aid":(\d+)', content)
            if aid_match:
                oid = aid_match.group(1)
            else:
                print("无法获取视频oid，无法继续获取评论")
                browser.close()
                return
        
        print(f"获取到视频oid: {oid}")
        
        # 使用B站评论API获取评论
        all_comments = []
        page_num = 1
        max_pages = 200  # 最多获取20页评论
        
        while page_num <= max_pages:
            print(f"获取第 {page_num} 页评论...")
            api_url = f"https://api.bilibili.com/x/v2/reply?pn={page_num}&type=1&oid={oid}&sort=2"
            
            api_page = context.new_page()
            api_page.goto(api_url)
            
            # 获取API响应内容
            api_content = api_page.content()
            api_page.close()
            
            # 提取JSON部分
            json_match = re.search(r'<pre>(.*?)</pre>', api_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                try:
                    data = json.loads(json_str)
                    
                    # 提取评论
                    if data['code'] == 0 and 'data' in data and 'replies' in data['data']:
                        replies = data['data']['replies']
                        
                        if replies is None:
                            print("没有更多评论")
                            break
                            
                        print(f"获取到 {len(replies)} 条一级评论")
                        
                        for reply in replies:
                            rpid = reply['rpid']  # 评论ID，用于获取二级评论
                            username = reply['member']['uname']
                            content = reply['content']['message']
                            like_count = reply.get('like', 0)
                            reply_count = reply.get('count', 0)  # 回复数量
                            
                            # 创建评论对象
                            comment_data = {
                                "comment_id": rpid,
                                "username": username,
                                "content": content,
                                "like_count": like_count,
                                "reply_count": reply_count,
                                "replies": []
                            }
                            
                            print(f"用户: {username} - 评论: {content}")
                            
                            # 如果有回复，获取二级评论
                            if reply_count > 0:
                                print(f"  该评论有 {reply_count} 条回复，正在获取...")
                                
                                # 获取二级评论
                                replies_data = get_comment_replies(context, oid, rpid)
                                comment_data["replies"] = replies_data
                                
                                # 打印二级评论数量
                                print(f"  成功获取 {len(replies_data)} 条回复")
                            
                            all_comments.append(comment_data)
                        
                        # 检查是否有下一页
                        if len(replies) < 20:  # B站每页通常返回20条评论
                            print("没有更多评论")
                            break
                    else:
                        print("API返回异常")
                        break
                except json.JSONDecodeError:
                    print("JSON解析错误")
                    break
            else:
                print("无法提取JSON数据")
                break
            
            page_num += 1
            time.sleep(1)  # 避免请求过于频繁
        
        print(f"共提取到 {len(all_comments)} 条一级评论")
        
        # 计算二级评论总数
        total_replies = sum(len(comment["replies"]) for comment in all_comments)
        print(f"共提取到 {total_replies} 条二级评论")
        
        # 保存评论到文件
        with open('bilibili_comments_with_replies.json', 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=2)
        
        print("评论已保存到 bilibili_comments_with_replies.json")
        browser.close()

def get_comment_replies(context, oid, rpid, max_pages=3):
    """获取指定评论的二级评论"""
    all_replies = []
    page_num = 1
    
    while page_num <= max_pages:
        # B站二级评论API
        api_url = f"https://api.bilibili.com/x/v2/reply/reply?oid={oid}&type=1&root={rpid}&ps=20&pn={page_num}"
        
        api_page = context.new_page()
        api_page.goto(api_url)
        
        # 获取API响应内容
        api_content = api_page.content()
        api_page.close()
        
        # 提取JSON部分
        json_match = re.search(r'<pre>(.*?)</pre>', api_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            try:
                data = json.loads(json_str)
                
                # 提取二级评论
                if data['code'] == 0 and 'data' in data and 'replies' in data['data']:
                    replies = data['data']['replies']
                    
                    if not replies:
                        break
                    
                    for reply in replies:
                        username = reply['member']['uname']
                        content = reply['content']['message']
                        like_count = reply.get('like', 0)
                        
                        # 安全地获取被回复用户名
                        parent_username = None
                        if 'parent' in reply and reply['parent'] != 0:
                            # 尝试不同的字段获取被回复用户名
                            if 'parent_reply_user' in reply and isinstance(reply['parent_reply_user'], dict):
                                # 从parent_reply_user字段获取
                                parent_username = reply['parent_reply_user'].get('uname', None)
                            elif 'reply_control' in reply and 'location' in reply['reply_control']:
                                # 从location字段提取，通常格式为"回复 @用户名"
                                location = reply['reply_control']['location']
                                if "@" in location:
                                    parent_username = location.split("@", 1)[1]
                        
                        reply_data = {
                            "username": username,
                            "content": content,
                            "like_count": like_count,
                            "reply_to": parent_username
                        }
                        
                        all_replies.append(reply_data)
                        
                        # 简短打印日志，避免刷屏
                        print(f"    回复: {username} -> {content[:30]}{'...' if len(content) > 30 else ''}")
                    
                    # 检查是否有下一页
                    if len(replies) < 20:
                        break
                else:
                    break
            except json.JSONDecodeError:
                break
        else:
            break
        
        page_num += 1
        time.sleep(0.5)  # 避免请求过于频繁
    
    return all_replies

if __name__ == "__main__":
    extract_bilibili_comments_with_replies()