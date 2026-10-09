---
name: teacher-knowledge-share
description: >
  将当前对话中模型刚刚生成/更新并交付的最新成果文件，通过企微（企业微信）群机器人 Webhook 推送到指定的企业微信群，便于教师把 AI 生成的报告/课件/图片等同步到教研群或班级群。
  当用户在对话中输入 @teacher-knowledge-share（可附带可选的新 Webhook 地址）时触发；默认推送"最新生成的文件"，不推送模型文字回复。
agent_created: true
---

# teacher-knowledge-share（企微群成果文件推送）

## 目标
读取**本轮对话里模型刚刚生成 / 更新并交付的最新成果文件**，通过已配置的企微群机器人 Webhook，把该**文件**上传并推送到企业微信群。
**不推送模型的文字回复**——只推送文件本身。

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
1. **确定待推送文件**：扫描对话历史，定位最后一条 `role=user` 且内容包含 `@teacher-knowledge-share` 的消息；
   在该消息**之前**、本次会话中**最近一次由你（assistant）写入 / 生成并交付给用户的成果文件**（如报告、PPT、图片、表格、脚本等），
   取其**绝对路径**作为待推送文件。
   - 若本次会话一次性生成了多个文件，取时间上最新的那一个。
   - **排除项**：`/tmp` 等临时文件、缓存 / 中间产物、以及本 Skill 自身目录下的文件（SKILL.md / push.py / config 等）。
   - 若该指令之前没有任何新生成 / 更新的成果文件，向用户说明"本次没有可推送的文件"并停止，不要发送空消息或推送无关文件。
2. **确定 Webhook 地址**：按上方"配置"优先级取得地址。若最终仍为空，提示用户先配置 `config.json` 或在指令后附带地址，然后停止。
3. **调用推送脚本**：用 Bash 运行本 Skill 目录下的 `scripts/push.py`（`<SKILL_DIR>` 替换为加载本 Skill 时给出的根目录绝对路径），以 `--file` 传入绝对路径：
   - 使用配置文件地址：`python3 <SKILL_DIR>/scripts/push.py --file <待推送文件绝对路径>`
   - 临时覆盖地址：`python3 <SKILL_DIR>/scripts/push.py --file <路径> --webhook <地址>`
   - 仅本地校验、不发真实请求：`python3 <SKILL_DIR>/scripts/push.py --file <路径> --dry-run`
   - 脚本会自动完成两步：① 上传文件到企微获取 `media_id`；② 以 `file` 消息类型发送。无需手动处理。
4. **判定结果**：脚本会打印一行 JSON。若 `errcode == 0` 表示推送成功；否则根据 `errmsg` 排查（地址错误 / 网络不通 / 文件超过 20MB 上限）。
5. **向用户简短汇报**：仅回复"已推送文件：<文件名> 到企微群 ✅"或失败原因。**严禁在回复中输出 Webhook 地址本身**。

## 约束与注意
- 企微文件单次上限 **20MB**，超出时脚本会拒绝发送；`media_id` 有效期 3 天。
- **只推文件、不推模型文字回复**——这是本 Skill 的核心约定。
- Webhook 地址属于群入口凭证，不要明文外泄到聊天 / 日志 / 文件中；脚本默认不回显地址。
- 文本模式（`--text-file` / stdin）仍保留在脚本中仅供手动调试，Skill 自动执行时一律使用文件模式。
