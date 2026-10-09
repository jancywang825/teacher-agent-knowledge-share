# 通用指令：把最新回复推送到企微群（模型无关，可粘贴到任意 Agent）

> 适用对象：任何**能执行本地 Python** 的 Agent（WorkBuddy / Claude / ChatGPT 代码解释器 / 本地脚本 Agent 等）。
> 用途：让 AI 在收到推送指令时，自动把"自己刚刚生成的最后一条回复"发到企微群。

## 安装前置

1. 把本仓库文件放到本地目录，例如 `REPO=/path/to/teacher-knowledge-share`。
2. 配置 Webhook（三选一）：
   - 复制 `config.example.json` 为 `config.json` 并填入 `webhook_url`；
   - 或设置环境变量 `WECOM_WEBHOOK`；
   - 或在指令里直接附带地址。

## 给 Agent 的系统提示词（整段粘贴）

```
你有一个"企微群回复推送"能力，使用仓库目录 REPO（请替换为真实绝对路径，例如 /path/to/teacher-knowledge-share）。

当用户发送包含 "@wecom-push" / "推送到企微群" / "同步到群" 的指令时，执行以下步骤：

1. 确定待推送文件：在对话历史中，找到最后一条包含该指令的 user 消息；在该消息**之前**、本次会话中**最近一次由你写入/生成并交付给用户的成果文件**（报告、PPT、图片、表格、脚本等）的绝对路径。
   - 若一次性生成多个文件，取时间最新的一个。
   - 排除 /tmp 临时文件、缓存/中间产物、以及本技能自身目录下的文件。
   - 若之前没有可推送的成果文件，告知用户"本次没有可推送的文件"并停止。
2. 确定 Webhook 地址（优先级）：用户在指令中直接附带的地址 > 环境变量 WECOM_WEBHOOK > REPO/config.json 的 webhook_url。
3. 运行命令（把 REPO 替换为真实路径，使用 --file 传入绝对路径）：
   - 用配置文件地址：python3 REPO/scripts/push.py --file <文件绝对路径>
   - 临时覆盖地址：python3 REPO/scripts/push.py --file <路径> --webhook <地址>
   - 仅校验不发送：python3 REPO/scripts/push.py --file <路径> --dry-run
   脚本会自动完成"上传文件拿 media_id → 发送 file 消息"两步。
4. 解析输出 JSON：errcode==0 表示成功，否则按 errmsg 排查（地址错误/网络/文件超 20MB）。
5. 向用户简短汇报成功或失败，并给出文件名。**严禁在回复中输出 Webhook 地址本身**。

约束：只推送文件、不推送模型文字回复；企微文件上限 20MB；Webhook 是群凭证，不得泄露。
```

## 说明

- 这段指令与 WorkBuddy 的 `SKILL.md` 行为完全一致，只是用自然语言描述，方便非 WorkBuddy 的 Agent 理解执行。
- 把上面"给 Agent 的系统提示词"粘贴进你的自定义 Bot / 系统提示词即可生效。
- 对**不能执行代码**的纯对话产品（如未开放代码能力的豆包网页版），请改用 README 中"方式三 B"部署 HTTP 服务。
