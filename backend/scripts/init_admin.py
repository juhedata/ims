#!/usr/bin/env python3
"""初始化管理员账号。若不存在则创建，已存在则跳过（可用 --force 重置密码）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 保证可从 backend/ 根目录直接运行
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.enums import UserRole
from app.models.user import User


def main() -> None:
    parser = argparse.ArgumentParser(description="初始化 IMS 管理员账号")
    parser.add_argument("--username", default="admin", help="管理员用户名")
    parser.add_argument("--password", default="admin123", help="管理员密码")
    parser.add_argument("--nickname", default="管理员", help="显示昵称")
    parser.add_argument("--force", action="store_true", help="已存在时重置密码与角色")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == args.username).first()
        if user and not args.force:
            print(f"管理员「{args.username}」已存在，跳过（使用 --force 可重置密码）")
            return

        if user:
            user.password = hash_password(args.password)
            user.role = UserRole.ADMIN.value
            user.status = 1
            user.nickname = args.nickname
            print(f"已重置管理员「{args.username}」密码")
        else:
            user = User(
                username=args.username,
                password=hash_password(args.password),
                nickname=args.nickname,
                role=UserRole.ADMIN.value,
                status=1,
            )
            db.add(user)
            print(f"已创建管理员「{args.username}」")

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
