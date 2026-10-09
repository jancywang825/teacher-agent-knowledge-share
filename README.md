# teacher-knowledge-share — 企微群回复推送

把对话中 AI **刚刚生成 / 更新并交付的最新成果文件**，通过企微（企业微信）群机器人 Webhook 推送到指定群。
原用于教师把 AI 生成的报告 / 课件 / 图片等同步到教研群或班级群，现已做成可跨 Agent 分发的版本。
**只推送文件，不推送模型文字回复。**

## 目录结构

```
teacher-knowledge-share/
├── SKILL.md              # WorkBuddy 技能定义（仅 WorkBuddy 自动加载）
├── PROMPT.md             # 模型无关指令：任意支持运行代码的 Agent 都可粘贴使用
├── README.md             # 本文件
├── config.example.json   # Webhook 配置模板（复制为 config.json 后填地址）
├── .gitignore            # 已忽略真实 config.json，防止泄露 key
└── scripts/
    └── push.py           # 纯 Python 标准库推送脚本，无第三方依赖
```

## 前置：配置 Webhook（必做）

1. 企微群 → 右上角 `...` → 群机器人 → 添加机器人 → 复制 Webhook 地址
   （形如 `https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx`）。
2. 把 `config.example.json` 复制为 `config.json`，填入地址；或设置环境变量 `WECOM_WEBHOOK`；
   或在每次调用时直接附带地址。

> ⚠️ `config.json` 含群入口凭证，**已被 .gitignore 忽略，切勿手动提交或外泄**。

## 方式一：WorkBuddy 用户（最省事，自动触发）

把整个 `teacher-knowledge-share/` 目录复制到本机的：

```
~/.workbuddy/skills/teacher-knowledge-share/
```

重启/刷新 WorkBuddy 后，对话中让模型生成/更新一个成果文件（报告、PPT、图片等），再输入 `@teacher-knowledge-share` 即会自动把**该文件**推送到群。

## 方式二：其他支持运行代码的 Agent（豆包 / Claude / ChatGPT 代码解释器 / 本地 Agent 等）

核心逻辑已拆成「脚本 + 自然语言指令」，与平台无关：

1. 把本仓库文件放到本地某目录（如 `~/tools/teacher-knowledge-share/`），并配置好 Webhook。
2. 把 `PROMPT.md` 的全部内容粘贴进该 Agent 的**系统提示词 / 自定义 Bot 说明**中。
3. 之后在对话里发 `@wecom-push`（或"推送到企微群"），Agent 会按指令执行 `push.py`。

适用条件：宿主 Agent 必须能执行本地 Python 并访问该目录。

## 方式三：纯对话型 Agent / 无代码执行能力的产品（如豆包网页版）

这类产品通常**无法直接运行你机器上的脚本**，因此有两种出路：

- **A. 用支持代码执行的 Agent**：直接用方式二（豆包若开放了代码/插件能力也可接入）。
- **B. 部署一个 HTTP 服务**：把 `push.py` 的逻辑包成一个小型 Web 服务（FastAPI / 云函数），
  暴露一个带鉴权的 `/push?text=...` 接口；任何能发 HTTP 请求的 Agent 或人都能调用。
  这样不依赖本地脚本，但需自行保证接口的访问安全。

## 安全须知

- Webhook key 即群发消息权限，泄露等于任何人可向该群发消息。勿入 git、勿入聊天记录、勿公开。
- 如怀疑泄露，立即在企微群机器人设置里「重置」key，并更新 `config.json`。
- 企微**文件**单次上限 20MB，`media_id` 有效期 3 天；**文本**单条上限 2048 字节（仅手动调试用到）。
- 本 Skill 默认只推送文件、不推送模型文字回复。

## 脚本用法（手动/调试）

Skill 自动执行时一律使用**文件模式**（`--file`）。以下为手动/调试示例：

```bash
# 推送文件（推荐，自动完成 上传+发送 两步）
python3 scripts/push.py --file /path/to/报告.pdf

# 临时覆盖 Webhook 地址
python3 scripts/push.py --file /path/to/报告.pdf --webhook https://qyapi.weixin.qq.com/...

# 仅本地校验，不真实发送（检查文件存在与大小）
python3 scripts/push.py --file /path/to/报告.pdf --dry-run

# 文本模式（仅手动调试用，Skill 自动执行不调用）
python3 scripts/push.py --text-file /tmp/msg.txt --dry-run
echo "要推送的内容" | python3 scripts/push.py
```

输出为单行 JSON：`{"errcode":0,"errmsg":"ok"}` 表示成功。
