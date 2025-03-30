# Bilibili 评论爬虫

这是一个用于爬取 Bilibili 视频评论（包括一级评论和二级回复）的 Python 脚本工具集。

## 功能特性

- 自动保存 Bilibili 登录 cookies
- 使用 Playwright 自动化浏览器获取视频评论
- 支持加载 cookies 以维持登录状态
- 自动提取视频 oid (aid)
- 获取一级评论及其所有二级回复
- 保存评论数据到 JSON 文件
- 包含丰富的评论信息：
  - 用户名
  - 评论内容
  - 点赞数
  - 回复数量
  - 二级回复详情（包括回复关系）

## 依赖安装

在运行此脚本前，请确保安装以下依赖：

```bash
pip install playwright
python -m playwright install
```

## 使用步骤

### 1. 保存 Bilibili 登录 Cookies

运行 `save_bilibili_cookies.py` 脚本：

```bash
python save_bilibili_cookies.py
```

脚本会：
1. 打开浏览器访问 Bilibili
2. 提示你手动登录
3. 登录成功后按回车键自动保存 cookies 到 `bilibili_cookies.json` 文件

### 2. 获取视频评论

运行 `demo.py` 脚本：

```bash
python demo.py
```

脚本会：
1. 自动加载之前保存的 cookies
2. 获取默认视频（可修改）的评论数据
3. 将评论保存到 `bilibili_comments_with_replies.json` 文件

## 配置选项

### 对于 `demo.py`：

- 修改目标视频 URL：编辑 `page.goto()` 中的 URL
- `max_pages`：控制最多获取多少页一级评论（默认20页）
- `get_comment_replies` 函数中的 `max_pages`：控制每条评论最多获取多少页二级回复（默认3页）

### 对于 `save_bilibili_cookies.py`：

- 默认保存到 `bilibili_cookies.json`，如需修改文件名请更改代码中的文件名

## 输出格式

评论数据 JSON 文件包含以下结构：

```json
[
  {
    "comment_id": "评论ID",
    "username": "用户名",
    "content": "评论内容",
    "like_count": 点赞数,
    "reply_count": 回复数量,
    "replies": [
      {
        "username": "回复用户名",
        "content": "回复内容",
        "like_count": 点赞数,
        "reply_to": "被回复的用户名"
      },
      ...
    ]
  },
  ...
]
```

## 注意事项

1. 请合理使用此脚本，避免对 Bilibili 服务器造成过大压力
2. 脚本中设置了适当的延迟（`time.sleep`）以防止请求过于频繁
3. cookies 有效期为登录状态保持时间，过期后需要重新运行 `save_bilibili_cookies.py` 获取新 cookies
4. 评论获取可能会受到 Bilibili API 限制
5. 建议在非高峰时段运行爬虫