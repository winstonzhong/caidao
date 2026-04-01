#!/usr/bin/env python3
"""
docker-mailserver 客户端工具
支持：发送、接收、标记已读、删除、移动邮件
"""

import smtplib
import imaplib
import email
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from pathlib import Path

import yaml

CAIDAO_CONFIG_DIR = Path(__file__).resolve().parent / 'caidao_config'
print('CAIDAO_CONFIG_DIR', CAIDAO_CONFIG_DIR)

with open(f"{CAIDAO_CONFIG_DIR}/email.yml", "r", encoding="utf-8") as f:
    email_config = yaml.load(f.read(), yaml.Loader)
{'user_1': {'name': 'zhangwei'}}
class MailClient:
    """邮件客户端"""

    def __init__(self, server, username, password, smtp_port=587):
        """
        初始化
        :param server: 邮件服务器地址 (如 'mail.j1.sale')
        :param username: 邮箱账号
        :param password: 密码
        :param smtp_port: SMTP端口 (465=SSL, 587=STARTTLS)
        """
        self.server = server
        self.username = username
        self.password = password
        self.smtp_port = smtp_port
        self.ctx = ssl._create_unverified_context()

    # ==================== 发送邮件 ====================

    def send_text(self, to_addr, subject, body):
        """
        发送纯文本邮件
        :param to_addr: 收件人地址
        :param subject: 主题
        :param body: 正文
        :return: 是否成功
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # 根据端口选择连接方式
            if self.smtp_port == 465:
                # SSL 直连
                with smtplib.SMTP_SSL(self.server, 465, context=self.ctx) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                # STARTTLS (587端口)
                with smtplib.SMTP(self.server, self.smtp_port) as server:
                    server.starttls(context=self.ctx)
                    server.login(self.username, self.password)
                    server.send_message(msg)

            print(f"✅ 发送成功 -> {to_addr}")
            return True

        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False

    def send_html(self, to_addr, subject, html_body, text_body=None):
        """
        发送 HTML 邮件
        :param to_addr: 收件人地址
        :param subject: 主题
        :param html_body: HTML 正文
        :param text_body: 纯文本正文（可选）
        :return: 是否成功
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = to_addr
            msg['Subject'] = subject

            # 纯文本版本
            if text_body:
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))

            # HTML 版本
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # 根据端口选择连接方式
            if self.smtp_port == 465:
                with smtplib.SMTP_SSL(self.server, 465, context=self.ctx) as server:
                    server.login(self.username, self.password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.server, self.smtp_port) as server:
                    server.starttls(context=self.ctx)
                    server.login(self.username, self.password)
                    server.send_message(msg)

            print(f"✅ HTML 邮件发送成功 -> {to_addr}")
            return True

        except Exception as e:
            print(f"❌ 发送失败: {e}")
            return False

    # ==================== IMAP 连接管理 ====================

    def _imap_connect(self):
        """连接 IMAP 服务器"""
        mail = imaplib.IMAP4_SSL(self.server, 993, ssl_context=self.ctx)
        mail.login(self.username, self.password)
        return mail

    # ==================== 收件箱操作 ====================

    def list_unread(self, folder='inbox', limit=10):
        """
        列出未读邮件
        :param folder: 文件夹名
        :param limit: 最多返回数量
        :return: 邮件列表 [(id, subject, from, date), ...]
        """
        mail = self._imap_connect()
        try:
            mail.select(folder)
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()

            results = []
            for eid in email_ids[-limit:]:
                _, msg_data = mail.fetch(eid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])

                subject = self._decode_header(msg['subject'])
                from_addr = self._decode_header(msg['from'])
                date = msg['date']

                results.append({
                    'id': eid.decode(),
                    'subject': subject,
                    'from': from_addr,
                    'date': date
                })

            print(f"📧 未读邮件: {len(results)} 封")
            for item in results:
                print(f"  [{item['id']}] {item['subject']} | From: {item['from']}")

            return results

        finally:
            mail.close()
            mail.logout()

    def list_all(self, folder='inbox', limit=20):
        """
        列出所有邮件
        :param folder: 文件夹名
        :param limit: 最多返回数量
        :return: 邮件列表
        """
        mail = self._imap_connect()
        try:
            mail.select(folder)
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()

            results = []
            for eid in email_ids[-limit:]:
                _, msg_data = mail.fetch(eid, '(RFC822)')
                msg = email.message_from_bytes(msg_data[0][1])

                # 检查是否已读
                _, flags = mail.fetch(eid, '(FLAGS)')
                is_read = b'\\Seen' in flags[0]

                results.append({
                    'id': eid.decode(),
                    'subject': self._decode_header(msg['subject']),
                    'from': self._decode_header(msg['from']),
                    'date': msg['date'],
                    'read': is_read
                })

            print(f"📧 共 {len(results)} 封邮件:")
            for item in results:
                status = '✓' if item['read'] else '✗'
                print(f"  [{status}] [{item['id']}] {item['subject']}")

            return results

        finally:
            mail.close()
            mail.logout()

    def get_email_content(self, email_id, folder='inbox'):
        """
        获取邮件详细内容
        :param email_id: 邮件 ID
        :param folder: 文件夹名
        :return: 邮件内容字典
        """
        mail = self._imap_connect()
        try:
            mail.select(folder)
            # 确保 email_id 是字符串
            if isinstance(email_id, int):
                email_id = str(email_id)
            _, msg_data = mail.fetch(email_id, '(RFC822)')
            msg = email.message_from_bytes(msg_data[0][1])

            # 提取正文
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')

            return {
                'id': email_id,
                'subject': self._decode_header(msg['subject']),
                'from': self._decode_header(msg['from']),
                'to': self._decode_header(msg['to']),
                'date': msg['date'],
                'body': body
            }

        finally:
            mail.close()
            mail.logout()

    # ==================== 邮件处理 ====================

    def mark_as_read(self, email_id, folder='inbox'):
        """
        标记邮件为已读
        :param email_id: 邮件 ID
        :param folder: 文件夹名
        :return: 是否成功
        """
        mail = self._imap_connect()
        try:
            mail.select(folder)
            if isinstance(email_id, int):
                email_id = str(email_id)
            mail.store(email_id, '+FLAGS', '\\Seen')
            print(f"✅ 已标记为已读: {email_id}")
            return True
        except Exception as e:
            print(f"❌ 标记失败: {e}")
            return False
        finally:
            mail.close()
            mail.logout()

    def mark_as_unread(self, email_id, folder='inbox'):
        """
        标记邮件为未读
        :param email_id: 邮件 ID
        :param folder: 文件夹名
        :return: 是否成功
        """
        mail = self._imap_connect()
        try:
            mail.select(folder)
            if isinstance(email_id, int):
                email_id = str(email_id)
            mail.store(email_id, '-FLAGS', '\\Seen')
            print(f"✅ 已标记为未读: {email_id}")
            return True
        except Exception as e:
            print(f"❌ 标记失败: {e}")
            return False
        finally:
            mail.close()
            mail.logout()

    def delete_email(self, email_id, folder='inbox'):
        """
        删除邮件
        :param email_id: 邮件 ID
        :param folder: 文件夹名
        :return: 是否成功
        """
        mail = self._imap_connect()
        try:
            mail.select(folder)
            if isinstance(email_id, int):
                email_id = str(email_id)
            mail.store(email_id, '+FLAGS', '\\Deleted')
            mail.expunge()
            print(f"✅ 已删除: {email_id}")
            return True
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False
        finally:
            mail.close()
            mail.logout()

    def move_to_folder(self, email_id, target_folder, source_folder='inbox'):
        """
        移动邮件到指定文件夹
        :param email_id: 邮件 ID
        :param target_folder: 目标文件夹
        :param source_folder: 源文件夹
        :return: 是否成功
        """
        mail = self._imap_connect()
        try:
            mail.select(source_folder)

            if isinstance(email_id, int):
                email_id = str(email_id)

            # 创建目标文件夹（如果不存在）
            mail.create(target_folder)

            # 复制到目标
            mail.copy(email_id, target_folder)

            # 删除原邮件
            mail.store(email_id, '+FLAGS', '\\Deleted')
            mail.expunge()

            print(f"✅ 已移动到 {target_folder}: {email_id}")
            return True
        except Exception as e:
            print(f"❌ 移动失败: {e}")
            return False
        finally:
            mail.close()
            mail.logout()

    # ==================== 文件夹管理 ====================

    def list_folders(self):
        """列出所有文件夹"""
        mail = self._imap_connect()
        try:
            _, folders = mail.list()
            results = []
            for folder in folders:
                # 解析文件夹名
                parts = folder.decode().split(' "/" ')
                if len(parts) == 2:
                    results.append(parts[1].strip('"'))

            print(f"📁 文件夹: {', '.join(results)}")
            return results
        finally:
            mail.logout()

    def create_folder(self, folder_name):
        """创建文件夹"""
        mail = self._imap_connect()
        try:
            mail.create(folder_name)
            print(f"✅ 创建文件夹: {folder_name}")
            return True
        except Exception as e:
            print(f"❌ 创建失败: {e}")
            return False
        finally:
            mail.logout()

    # ==================== 工具方法 ====================

    def _decode_header(self, header):
        """解码邮件头"""
        if not header:
            return ""
        try:
            decoded, charset = decode_header(header)[0]
            if isinstance(decoded, bytes):
                return decoded.decode(charset or 'utf-8', errors='ignore')
            return decoded
        except:
            return str(header)


# ==================== 测试代码 ====================

if __name__ == "__main__":
    pass
    # 测试配置
    # SERVER = "mail.j1.sale"
    # USERNAME = "test@j1.sale"
    # PASSWORD = "xxx"
    #
    # # 初始化客户端（使用域名连接，587端口STARTTLS）
    # client = MailClient(SERVER, USERNAME, PASSWORD, smtp_port=587)
    # l = client.list_all(limit=5)
    # print("=" * 50)
    # print("测试 1: 发送文本邮件")
    # print("=" * 50)
    # client.send_text(
    #     to_addr="liqiang239@qq.com",
    #     subject="测试邮件 - 文本",
    #     body="这是一封测试邮件，来自 Python MailClient。"
    # )
    #
    # print("\n" + "=" * 50)
    # print("测试 2: 发送 HTML 邮件")
    # print("=" * 50)
    # client.send_html(
    #     to_addr="liqiang239@qq.com",
    #     subject="测试邮件 - HTML",
    #     html_body="<h2>测试邮件</h2><p>这是一封 <b>HTML</b> 测试邮件。</p>",
    #     text_body="这是一封 HTML 测试邮件的纯文本版本。"
    # )
    #
    # print("\n" + "=" * 50)
    # print("测试 3: 列出未读邮件")
    # print("=" * 50)
    # unread = client.list_unread(limit=5)
    #
    # print("\n" + "=" * 50)
    # print("测试 4: 列出所有邮件")
    # print("=" * 50)
    # all_mails = client.list_all(limit=5)
    #
    # # 如果有未读邮件，测试标记已读
    # if unread:
    #     first_id = unread[0]['id']
    #
    #     print("\n" + "=" * 50)
    #     print(f"测试 5: 标记邮件 {first_id} 为已读")
    #     print("=" * 50)
    #     client.mark_as_read(first_id)
    #
    #     # 创建已处理文件夹并移动
    #     print("\n" + "=" * 50)
    #     print("测试 6: 创建 'Processed' 文件夹")
    #     print("=" * 50)
    #     client.create_folder("Processed")
    #
    #     print("\n" + "=" * 50)
    #     print(f"测试 7: 移动邮件 {first_id} 到 Processed")
    #     print("=" * 50)
    #     client.move_to_folder(first_id, "Processed")
    #
    # print("\n" + "=" * 50)
    # print("测试 8: 列出所有文件夹")
    # print("=" * 50)
    # client.list_folders()
    #
    # print("\n" + "=" * 50)
    # print("所有测试完成！")
    # print("=" * 50)
