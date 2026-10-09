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

1. 确定待推送文本：在对话历史中，找到最后一条包含该指令的 user 消息；取其**之前、最近的一条 assistant 消息的完整文本**作为正文。
   - 这正是"模型刚生成的最新回复"，不要使用本次指令执行中产生的回复。
   - 若之前没有 assistant 回复，告知用户"没有可推送的内容"并停止，不要发空消息。
2. 确定 Webhook 地址（优先级）：用户在指令中直接附带的地址 > 环境变量 WECOM_WEBHOOK > REPO/config.json 的 webhook_url。
3. 把待推送文本写入临时文件，例如 /tmp/wecom_push.txt。
4. 运行命令（把 REPO 替换为真实路径）：
   - 用配置文件地址：python3 REPO/scripts/push.py --text-file /tmp/wecom_push.txt
   - 临时覆盖地址：python3 REPO/scripts/push.py --text-file /tmp/wecom_push.txt --webhook <地址>
5. 解析输出 JSON：errcode==0 表示成功，否则按 errmsg 排查（地址错误/网络/超限）。
6. 向用户简短汇报成功或失败。**严禁在回复中输出 Webhook 地址本身**。

约束：企微文本上限 2048 字节，超长脚本会自动截断；Webhook 是群凭证，不得泄露。
```

## 说明

- 这段指令与 WorkBuddy 的 `SKILL.md` 行为完全一致，只是用自然语言描述，方便非 WorkBuddy 的 Agent 理解执行。
- 把上面"给 Agent 的系统提示词"粘贴进你的自定义 Bot / 系统提示词即可生效。
- 对**不能执行代码**的纯对话产品（如未开放代码能力的豆包网页版），请改用 README 中"方式三 B"部署 HTTP 服务。
