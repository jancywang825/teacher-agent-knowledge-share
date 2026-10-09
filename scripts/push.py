#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企微群机器人推送脚本
===================
把指定文本通过企业微信群机器人 Webhook 推送到群。

Webhook 地址获取优先级：
  1. 命令行参数 --webhook
  2. 环境变量 WECOM_WEBHOOK
  3. 本文件同级上层目录的 config.json 中的 webhook_url

用法：
  python3 push.py --text-file /tmp/msg.txt
  python3 push.py --text-file /tmp/msg.txt --webhook https://qyapi.weixin.qq.com/...
  python3 push.py --text-file /tmp/msg.txt --dry-run      # 仅校验/打印 payload，不发送
  cat msg.txt | python3 push.py                           # 也可从 stdin 读取

输出：一行 JSON，包含 errcode / errmsg。errcode==0 表示成功。

企微限制：text 类型正文上限 2048 字节（UTF-8）。超出自动截断并追加 "…(已截断)"。
扩展：如需 @群成员(mentioned_list)、markdown、图文卡片，可参照下方 build_payload 注释修改。
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

TEXT_BYTE_LIMIT = 2048
TRUNC_SUFFIX = "…(已截断)"


def get_webhook(cli_webhook=None):
    if cli_webhook:
        return cli_webhook.strip()
    env = os.environ.get("WECOM_WEBHOOK")
    if env:
        return env.strip()
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, encoding="utf-8") as f:
                data = json.load(f)
            url = (data.get("webhook_url") or "").strip()
            if url:
                return url
        except Exception:
            pass
    return ""


def build_payload(text):
    """构造企微 webhook 请求体。text 类型，超长按字节安全截断。

    扩展示例：
      # 带 @全体成员
      return {"msgtype": "text", "text": {"content": text, "mentioned_list": ["@all"]}}
      # markdown 类型（上限 4096 字节）
      return {"msgtype": "markdown", "markdown": {"content": text}}
    """
    encoded = text.encode("utf-8")
    if len(encoded) > TEXT_BYTE_LIMIT:
        room = TEXT_BYTE_LIMIT - len(TRUNC_SUFFIX.encode("utf-8"))
        cut = encoded[:room].decode("utf-8", "ignore")
        text = cut + TRUNC_SUFFIX
    return {"msgtype": "text", "text": {"content": text}}


def post(webhook, payload, dry_run=False):
    if dry_run:
        return {"errcode": 0, "errmsg": "dry-run 校验通过（未实际发送）", "payload": payload}
    if not webhook:
        return {"errcode": -1, "errmsg": "未配置 webhook 地址（请填写 config.json 或在指令后附带地址）"}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            try:
                return json.loads(body)
            except Exception:
                return {"errcode": -3, "errmsg": "响应非 JSON: " + body[:200]}
    except urllib.error.HTTPError as e:
        return {"errcode": e.code, "errmsg": "HTTP 错误 %d" % e.code}
    except Exception as e:
        return {"errcode": -2, "errmsg": "请求失败: %s" % str(e)}


def main():
    parser = argparse.ArgumentParser(description="企微群机器人文本推送")
    parser.add_argument("--text-file", help="包含待推送文本的本地文件（推荐，避免 shell 转义问题）")
    parser.add_argument("--webhook", help="临时覆盖 Webhook 地址")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 payload，不实际发送")
    args = parser.parse_args()

    if args.text_file:
        try:
            with open(args.text_file, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(json.dumps({"errcode": -4, "errmsg": "读取文本文件失败: %s" % str(e)}, ensure_ascii=False))
            sys.exit(1)
    else:
        text = sys.stdin.read()

    text = text.strip()
    if not text:
        print(json.dumps({"errcode": -5, "errmsg": "待推送文本为空，已取消发送"}, ensure_ascii=False))
        sys.exit(1)

    webhook = get_webhook(args.webhook)
    payload = build_payload(text)
    result = post(webhook, payload, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("errcode") == 0 else 1)


if __name__ == "__main__":
    main()
