#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企微群机器人推送脚本
===================
两种推送模式：
  A. 文件模式（推荐，本 Skill 默认）：把"本轮最新生成/更新的成果文件"上传到企微群。
     企微发文件需两步：先 upload_media 拿到 media_id，再用 file 消息类型发送。
  B. 文本模式（手动/调试用）：把一段文本作为 text 消息发送。

Webhook 地址获取优先级：
  1. 命令行参数 --webhook
  2. 环境变量 WECOM_WEBHOOK
  3. 本文件同级上层目录的 config.json 中的 webhook_url

用法：
  # 文件模式
  python3 push.py --file /绝对路径/报告.pdf
  python3 push.py --file /绝对路径/报告.pdf --webhook https://qyapi.weixin.qq.com/...
  python3 push.py --file /绝对路径/报告.pdf --dry-run      # 仅校验，不真实上传/发送

  # 文本模式（调试）
  python3 push.py --text-file /tmp/msg.txt
  python3 push.py --text-file /tmp/msg.txt --dry-run
  echo "内容" | python3 push.py

输出：一行 JSON，包含 errcode / errmsg。errcode==0 表示成功。

限制：
  - 企微文件单次上限 20MB，media_id 有效期 3 天。
  - 企微 text 正文上限 2048 字节（UTF-8），超出自动截断并追加 "…(已截断)"。
扩展：如需 @群成员(mentioned_list)、markdown、图文卡片，可在 send_payload 处扩展。
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
from urllib.parse import urlparse, parse_qs

TEXT_BYTE_LIMIT = 2048
TRUNC_SUFFIX = "…(已截断)"
FILE_SIZE_LIMIT = 20 * 1024 * 1024  # 20MB
UPLOAD_URL_TPL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/upload_media?key={key}&type=file"


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


def extract_key(webhook_url):
    q = parse_qs(urlparse(webhook_url).query)
    vals = q.get("key")
    return vals[0].strip() if vals else ""


def build_text_payload(text):
    """text 类型，超长按字节安全截断。"""
    encoded = text.encode("utf-8")
    if len(encoded) > TEXT_BYTE_LIMIT:
        room = TEXT_BYTE_LIMIT - len(TRUNC_SUFFIX.encode("utf-8"))
        cut = encoded[:room].decode("utf-8", "ignore")
        text = cut + TRUNC_SUFFIX
    return {"msgtype": "text", "text": {"content": text}}


def post_json(webhook, payload, timeout=10):
    """发送 JSON 消息体到 webhook/send，返回解析后的 dict。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            try:
                return json.loads(body)
            except Exception:
                return {"errcode": -3, "errmsg": "响应非 JSON: " + body[:200]}
    except urllib.error.HTTPError as e:
        return {"errcode": e.code, "errmsg": "HTTP 错误 %d" % e.code}
    except Exception as e:
        return {"errcode": -2, "errmsg": "请求失败: %s" % str(e)}


def upload_media(webhook_url, file_path):
    """上传文件到企微，返回 (media_id, result_dict)。失败返回 (None, result_dict)。"""
    key = extract_key(webhook_url)
    if not key:
        return None, {"errcode": -10, "errmsg": "Webhook 地址中未找到 key 参数，无法上传文件"}
    upload_url = UPLOAD_URL_TPL.format(key=key)
    filename = os.path.basename(file_path)
    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except Exception as e:
        return None, {"errcode": -11, "errmsg": "读取待推送文件失败: %s" % str(e)}
    if len(file_bytes) > FILE_SIZE_LIMIT:
        return None, {"errcode": -12, "errmsg": "文件超过企微 20MB 上限，已取消发送"}
    boundary = "----wecomboundary7Q2k9x"
    crlf = b"\r\n"
    body = b""
    body += ("--%s" % boundary).encode() + crlf
    body += ('Content-Disposition: form-data; name="media"; filename="%s"' % filename).encode("utf-8") + crlf
    body += b"Content-Type: application/octet-stream" + crlf
    body += crlf
    body += file_bytes
    body += crlf
    body += ("--%s--" % boundary).encode() + crlf
    headers = {"Content-Type": "multipart/form-data; boundary=%s" % boundary}
    req = urllib.request.Request(upload_url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return None, {"errcode": e.code, "errmsg": "上传 HTTP 错误 %d" % e.code}
    except Exception as e:
        return None, {"errcode": -13, "errmsg": "上传请求失败: %s" % str(e)}
    if data.get("errcode") != 0:
        return None, data
    return data.get("media_id"), {"errcode": 0, "errmsg": "上传成功", "media_id": data.get("media_id")}


def push_file(webhook_url, file_path, dry_run=False):
    if not os.path.exists(file_path):
        return {"errcode": -14, "errmsg": "文件不存在: %s" % file_path}
    size = os.path.getsize(file_path)
    if size > FILE_SIZE_LIMIT:
        return {"errcode": -12, "errmsg": "文件超过企微 20MB 上限，已取消发送"}
    if dry_run:
        return {
            "errcode": 0,
            "errmsg": "dry-run 校验通过（未真实上传/发送）",
            "file": os.path.basename(file_path),
            "size": size,
        }
    if not webhook_url:
        return {"errcode": -1, "errmsg": "未配置 webhook 地址（请填写 config.json 或在指令后附带地址）"}
    media_id, up = upload_media(webhook_url, file_path)
    if media_id is None:
        return up
    return post_json(webhook_url, {"msgtype": "file", "file": {"media_id": media_id}})


def push_text(webhook_url, text, dry_run=False):
    text = text.strip()
    if not text:
        return {"errcode": -5, "errmsg": "待推送文本为空，已取消发送"}
    payload = build_text_payload(text)
    if dry_run:
        return {"errcode": 0, "errmsg": "dry-run 校验通过（未实际发送）", "payload": payload}
    if not webhook_url:
        return {"errcode": -1, "errmsg": "未配置 webhook 地址（请填写 config.json 或在指令后附带地址）"}
    return post_json(webhook_url, payload)


def main():
    parser = argparse.ArgumentParser(description="企微群机器人推送（文件/文本）")
    parser.add_argument("--file", help="待推送的文件绝对路径（文件模式，推荐）")
    parser.add_argument("--text-file", help="包含待推送文本的本地文件（文本模式，调试用）")
    parser.add_argument("--webhook", help="临时覆盖 Webhook 地址")
    parser.add_argument("--dry-run", action="store_true", help="仅校验/打印 payload，不真实发送")
    args = parser.parse_args()

    webhook = get_webhook(args.webhook)

    if args.file:
        result = push_file(webhook, args.file, dry_run=args.dry_run)
    elif args.text_file:
        try:
            with open(args.text_file, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(json.dumps({"errcode": -4, "errmsg": "读取文本文件失败: %s" % str(e)}, ensure_ascii=False))
            sys.exit(1)
        result = push_text(webhook, text, dry_run=args.dry_run)
    else:
        # 默认从 stdin 读取文本（兼容旧文本用法）
        text = sys.stdin.read()
        result = push_text(webhook, text, dry_run=args.dry_run)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0 if result.get("errcode") == 0 else 1)


if __name__ == "__main__":
    main()
