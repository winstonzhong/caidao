import os
from typing import Optional
from Crypto.Cipher import DES
from Crypto.Util.Padding import pad, unpad
import base64
import tool_static
import requests
from tool_enc import StrSecret
from pathlib import Path
import json

class EncryptedAutoRoutingFilePersistence:
    def __init__(self, fname: str,
                 project_name: str,
                 net_token: str,
                 ):
        self.fname = fname
        self.project_name = project_name
        self.net_token = net_token
        self.secret = self._format_secret(''.join(sorted(list(self.net_token))))

    @property
    def url(self) -> str:
        return f'{tool_static.BASE_URL_56T}/{self.project_name}/{self.fname}'

    def _format_secret(self, secret: str) -> bytes:
        """确保密钥是8字节长度"""
        # 如果密钥长度不足8字节，用填充字符补足
        # 如果超过8字节，截取前8字节
        secret_bytes = secret.encode('utf-8')
        if len(secret_bytes) < 8:
            return secret_bytes.ljust(8, b'\0')
        return secret_bytes[:8]

    @property
    def file_path(self) -> str:
        """获取本地文件路径"""
        return tool_static.链接到路径(self.url)
    
    def 是否可访问挂载点(self) -> bool:
        fpath = Path(self.file_path).resolve()
        if fpath.parent.parent.exists():
            fpath.parent.mkdir(parents=True, exist_ok=True)
            return True
        else:
            return False

    def save(self, content: str) -> None:
        """保存内容到文件或上传到服务器"""
        encrypted_content = self._encrypt(content)
        if self.是否可访问挂载点():
            # 文件存在，加密后写入本地
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(encrypted_content)
        else:
            # 文件不存在，上传到服务器
            tool_static.upload_file(encrypted_content, self.net_token, self.fname, self.project_name)
        return self

    def download_file(self) -> str:
        headers = {"Cache-Control": "no-cache", "Pragma": "no-cache"}
        try:
            return requests.get(self.url, headers=headers).content
        except Exception as e:
            print(e)


    def read(self) -> Optional[str]:
        """从本地读取文件或从服务器下载并解密"""
        file_path = self.file_path
        if os.path.exists(file_path):
            # 文件存在，读取并解密
            with open(file_path, 'r', encoding='utf-8') as f:
                encrypted_content = f.read()
            return self._decrypt(encrypted_content)
        else:
            # 文件不存在，从服务器下载
            return self._decrypt(self.download_file())

    def _encrypt(self, content: str) -> str:
        """使用DES算法加密内容"""
        # 创建DES cipher对象
        cipher = DES.new(self.secret, DES.MODE_ECB)
        # 对内容进行填充并加密
        padded_data = pad(content.encode('utf-8'), DES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        # 转换为Base64字符串以便存储
        return base64.b64encode(encrypted_data).decode('utf-8')

    def _decrypt(self, encrypted_content: str) -> str:
        """使用DES算法解密内容"""
        # 从Base64字符串转换回字节
        encrypted_data = base64.b64decode(encrypted_content)
        # 创建DES cipher对象
        cipher = DES.new(self.secret, DES.MODE_ECB)
        # 解密并去除填充
        decrypted_data = cipher.decrypt(encrypted_data)
        unpadded_data = unpad(decrypted_data, DES.block_size)
        return unpadded_data.decode('utf-8')

class JobFilePersistence(EncryptedAutoRoutingFilePersistence):
    @classmethod
    def from_job(cls, job, net_token):
        obj = cls(fname=f'{job.id}_{job.name}.json', project_name='jobs', net_token=net_token)
        obj.job = job
        return obj

    @classmethod
    def from_job_name(cls, job_name: str, net_token:str):
        return cls(fname=f'{job_name}.json', project_name='jobs', net_token=net_token)

    def save(self):
        return super().save(json.dumps(self.job.pack_list))

    def read(self):
        return json.loads(super().read())