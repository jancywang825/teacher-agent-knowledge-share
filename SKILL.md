---
name: teacher-knowledge-share
description: >
  将当前对话中模型刚刚生成的最新回复文本，通过企微（企业微信）群机器人 Webhook 推送到指定的企业微信群，便于教师把 AI 答疑/讲解同步到教研群或班级群。
  当用户在对话中输入 @teacher-knowledge-share（可附带可选的新 Webhook 地址）时触发；用于把 AI 的回答同步到团队群。
agent_created: true
---

# teacher-knowledge-share（企微群机器人回复推送）

## 目标
读取**本轮对话里模型刚刚生成的最新回复文本**，通过已配置的企微群机器人 Webhook，把该文本 POST 推送到企业微信群。

## 触发方式
- 用户在对话中输入 `@teacher-knowledge-share` 即触发本 Skill。
- 可选：在指令后直接附带一个 Webhook 地址（`@teacher-knowledge-share https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx`），本次使用该地址，不读取配置文件。

## Webhook 地址配置（参数）
优先级从高到低：
1. 用户在本轮 `@teacher-knowledge-share` 消息中直接给出的 Webhook 地址；
2. 环境变量 `WECOM_WEBHOOK`；
3. 本 Skill 目录下的 `config.json` 中的 `webhook_url` 字段。

首次使用前，请编辑本 Skill 目录下的 `config.json`，把 `webhook_url` 填为你的企微群机器人 Webhook 地址。
（在企微群 → 右上角 `...` → 群机器人 → 添加机器人 → 复制 Webhook 地址。）

## 执行步骤
1. **确定待推送文本**：扫描对话消息列表，定位最后一条 `role=user` 且内容包含 `@teacher-knowledge-share` 的消息；
   取该消息**之前、最近的一条 `role=assistant` 消息的完整文本内容**作为待推送正文。
   - 这正是"模型本轮刚刚生成的最新回复"，**不要**使用本次 Skill 执行过程中产生的回复。
   - 若在此之前不存在 assistant 回复，向用户说明"没有可推送的回复"并停止，不要发送空消息。
   - 剥离该回复中可能附带的多余内部提示词 / 工具调试信息，仅保留面向用户的真实回答正文。
2. **确定 Webhook 地址**：按上方"配置"优先级取得地址。若最终仍为空，提示用户先配置 `config.json` 或在指令后附带地址，然后停止。
3. **调用推送脚本**：把待推送文本写入系统临时目录的一个文本文件（例如 `/tmp/wecom_push_<时间戳>.txt`），
   然后用 Bash 运行本 Skill 目录下的 `scripts/push.py`（`<SKILL_DIR>` 替换为加载本 Skill 时给出的根目录绝对路径）：
   - 使用配置文件地址：`python3 <SKILL_DIR>/scripts/push.py --text-file /tmp/wecom_push_xxx.txt`
   - 临时覆盖地址：`python3 <SKILL_DIR>/scripts/push.py --text-file /tmp/wecom_push_xxx.txt --webhook <地址>`
   - 仅本地校验、不发真实请求：`python3 <SKILL_DIR>/scripts/push.py --text-file /tmp/wecom_push_xxx.txt --dry-run`
4. **判定结果**：脚本会打印一行 JSON。若 `errcode == 0` 表示推送成功；否则根据 `errmsg` 排查（地址错误 / 网络不通 / 内容超限）。
5. **向用户简短汇报**：仅回复"已推送到企微群 ✅"或失败原因。**严禁在回复中输出 Webhook 地址本身**。

## 约束与注意
- 企微文本消息正文上限为 2048 字节（约 680 个汉字）；超出时脚本会自动截断并追加"…(已截断)"。
- Webhook 地址属于群入口凭证，不要明文外泄到聊天 / 日志 / 文件中；脚本默认不回显地址。
- 默认只推送纯文本。如需 @群成员、发送 markdown / 图文卡片，可在 `scripts/push.py` 中扩展（文件内已预留说明）。
- 中文等多字节文本以 UTF-8 字节计长，脚本已按字节安全截断，避免出现半个字符乱码。
