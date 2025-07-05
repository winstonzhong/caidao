import os
import re
import subprocess
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Union
from tqdm import tqdm  # 新增进度条支持

import sys
from typing import Generator, Tuple
import numpy


class AndroidFileBackup:
    def __init__(self, backup_dir: str, ip_port: str="192.168.1.7:7080"):
        """
        初始化Android文件备份工具
        
        参数:
            backup_dir: 本地备份目录路径
        """
        self.ip_port = ip_port
        self.backup_dir = backup_dir
        self.mapping_table_path = os.path.join(backup_dir, "backup_mapping.csv")
        self.mapping_table = self._load_mapping_table()
        
        # 确保备份目录存在
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # 文件类型定义及对应的MIME类型和扩展名
        self.file_types = {
            'video': {
                'mime_patterns': ['video/'],
                'extensions': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
            },
            'image': {
                'mime_patterns': ['image/'],
                'extensions': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            },
            'audio': {
                'mime_patterns': ['audio/'],
                'extensions': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']
            },
            'document': {
                'mime_patterns': ['application/pdf', 'application/msword', 
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                 'application/vnd.ms-excel', 
                                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                 'application/vnd.ms-powerpoint', 
                                 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                                 'text/plain'],
                'extensions': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']
            }
        }
        
        # 安卓系统目录列表，用于判断是否为系统文件
        self.system_dirs = [
            '/system', '/vendor', '/product', '/odm', '/oem',
            '/data/local', '/data/system'
        ]

    def _run_adb_command(self, command: List[str]) -> str:
        """执行ADB命令并返回输出"""
        return self.execute(' '.join(command[1:] if command[0] == 'shell' else command))


    @property
    def cmd(self):
        return f"adb -s {self.ip_port} shell"

    def execute(self, script, encoding="utf8"):
        # print(f"执行命令：{script}")
        # raise ValueError
        process = subprocess.Popen(
            self.cmd,
            encoding=encoding,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(input=script)
        if stderr:
            raise Exception(f"ADB命令执行失败: {stderr}")
        return stdout.strip()
    
    def run_adb(self, script, encoding="utf8"):
        # print(f"执行命令：{script}")
        # raise ValueError
        script = ' '.join(script) if isinstance(script, list) else script
        process = subprocess.Popen(
            f"adb -s {self.ip_port} {script}",
            encoding=encoding,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        if stderr:
            raise Exception(f"ADB命令执行失败: {stderr}")
        return stdout.strip()



    def _load_mapping_table(self) -> pd.DataFrame:
        """加载或创建备份映射表"""
        if os.path.exists(self.mapping_table_path):
            df = pd.read_csv(self.mapping_table_path)
            # 确保必要的列存在，添加默认值
            required_columns = ['android_path', 'local_path', 'file_type', 
                               'backup_time', 'file_size', 'md5_hash', 
                               'backup_status', 'original_deleted']
            for col in required_columns:
                if col not in df.columns:
                    if col == 'backup_status':
                        df[col] = '未备份'
                    elif col == 'original_deleted':
                        df[col] = False
                    else:
                        df[col] = None
            return df
        else:
            # 创建新的数据框
            return pd.DataFrame(columns=[
                'android_path', 'local_path', 'file_type', 
                'backup_time', 'file_size', 'md5_hash',
                'backup_status', 'original_deleted'
            ])

    def _save_mapping_table(self) -> None:
        """保存备份映射表"""
        self.mapping_table.to_csv(self.mapping_table_path, index=False)

    def is_device_connected(self) -> bool:
        """检查是否有安卓设备通过ADB连接"""
        devices = self._run_adb_command(['devices']).split('\n')[1:]
        # 过滤掉空行并检查是否有设备
        return any(device.strip() and not device.startswith('*') for device in devices)

    def scan_to_mapping(self, file_types: Optional[List[str]] = None, 
                        directory: str = '/sdcard/*', 
                        recursive: bool = True) -> int:
        """
        扫描安卓文件系统并更新映射表
        
        参数:
            file_types: 文件类型列表，可选值为 'video', 'image', 'audio', 'document' 或 None(所有类型)
            directory: 搜索目录，默认为 /sdcard
            recursive: 是否递归搜索，默认为True
            
        返回:
            新增的文件数量
        """
        if file_types is None:
            file_types = list(self.file_types.keys())
            
        for file_type in file_types:
            if file_type not in self.file_types:
                raise ValueError(f"不支持的文件类型: {file_type}")
                
        # 获取所有已存在的安卓文件路径
        existing_paths = set(self.mapping_table['android_path'].dropna())
        
        # 构建find命令
        find_command = ['shell', 'find', directory]
        
        if not recursive:
            find_command.append('-maxdepth')
            find_command.append('1')
            
        # 添加文件类型过滤
        extensions = []
        for file_type in file_types:
            extensions.extend(self.file_types[file_type]['extensions'])
            
        # if extensions:
        #     name_pattern = ' -o '.join([f'-name *{ext}' for ext in extensions])
        #     find_command.extend([name_pattern, '-print'])

        # for ext in extensions:
        #     find_command.extend(['-o', '-name', f'*{ext}'])
        find_command.extend(['\\(',' -o '.join([f'-name "*{ext}"' for ext in extensions]), '\\)'])


        # find_command.extend(['-o', '-name', f'*{ext}'])

        find_command.extend(['-print', '-type f'])

        # 使用更安全的方式构建find命令，避免括号问题
        # name_patterns = []
        # for ext in extensions:
        #     name_patterns.extend(['-name', f'"*{ext}"'])
        #     find_command.extend(['-type', 'f', '('] + name_patterns + [')', '-print'])
        
        # if extensions:
        #     # 使用更安全的方式构建find命令，避免括号问题
        #     name_patterns = []
        #     for ext in extensions:
        #         name_patterns.extend(['-name', f'"*{ext}"'])
        #     find_command.extend(name_patterns + ['-print'])

        # 执行命令
        print(f"正在扫描 {directory} 目录中的文件...")

        # print(' '.join(find_command))

        # return
        # output = self._run_adb_command(find_command)
        output = self._run_adb_command(find_command)

        # print(output)
        
        # 解析输出并更新映射表
        new_files = 0
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for line in tqdm(output.split('\n'), desc="处理文件"):
            file_path = line.strip()
            if not file_path or not os.path.basename(file_path):  # 排除空路径和目录
                continue
                
            if file_path in existing_paths:
                continue
                
            # 确定文件类型
            file_type = None
            for ft, info in self.file_types.items():
                if any(file_path.endswith(ext) for ext in info['extensions']):
                    file_type = ft
                    break
                    
            if file_type is None or file_type not in file_types:
                continue
                
            # 获取文件信息
            try:
                file_size = self._run_adb_command(['shell', 'stat', '-c', '%s', f'"{file_path}"'])
                md5_hash = self._run_adb_command(['shell', 'md5sum', f'"{file_path}"']).split()[0]
            except:
                file_size = numpy.nan
                md5_hash = numpy.nan
                
            # 判断是否为系统文件
            # is_system = self.is_system_file(file_path)
            
            # 更新映射表
            new_entry = pd.DataFrame({
                'android_path': [file_path],
                'local_path': [None],
                'file_type': [file_type],
                # 'is_system': [is_system],
                'backup_time': [None],
                'file_size': [file_size],
                'md5_hash': [md5_hash],
                'backup_status': ['未备份'],
                'original_deleted': [False]
            })
            
            self.mapping_table = pd.concat([self.mapping_table, new_entry], ignore_index=True)
            new_files += 1
            
        # 保存映射表
        self._save_mapping_table()
        print(f"扫描完成，新增 {new_files} 个文件到映射表")
        return new_files

    def backup(self, file_types: Optional[List[str]] = None, 
              overwrite: bool = False, 
              skip_system_files: bool = True) -> int:
        """
        根据映射表备份文件
        
        参数:
            file_types: 文件类型列表，可选值为 'video', 'image', 'audio', 'document' 或 None(所有类型)
            overwrite: 是否覆盖已存在的文件，默认为False
            skip_system_files: 是否跳过系统文件，默认为True
            
        返回:
            成功备份的文件数量
        """
        # 筛选需要备份的文件
        query = 'backup_status == "未备份"'
        
        if file_types is not None:
            file_types_str = "', '".join(file_types)
            query += f' and file_type in ["{file_types_str}"]'
            
        # if skip_system_files:
        #     query += ' and is_system == False'
        # print(query)
            
        files_to_backup = self.mapping_table.query(query)
        
        if files_to_backup.empty:
            print("没有需要备份的文件")
            return 0
            
        print(f"准备备份 {len(files_to_backup)} 个文件...")
        success_count = 0
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for _, row in tqdm(files_to_backup.iterrows(), total=len(files_to_backup), desc="备份文件"):
            android_path = row['android_path']
            file_type = row['file_type']
            
            # 确定本地路径
            file_name = os.path.basename(android_path)
            type_dir = os.path.join(self.backup_dir, file_type)
            
            # 确保类型目录存在
            if not os.path.exists(type_dir):
                os.makedirs(type_dir)
                
            # 构建本地路径
            local_path = os.path.join(type_dir, file_name)
            
            # 处理文件已存在的情况
            if os.path.exists(local_path) and not overwrite:
                # 添加时间戳避免冲突
                base_name, ext = os.path.splitext(file_name)
                local_path = os.path.join(type_dir, f"{base_name}_{current_time}{ext}")
                
            # 执行备份
            try:
                self.run_adb(['pull', f'"{android_path}"', f'"{local_path}"'])
                
                # 更新映射表中的备份状态
                index = row.name
                self.mapping_table.loc[index, 'local_path'] = local_path
                self.mapping_table.loc[index, 'backup_time'] = current_time
                self.mapping_table.loc[index, 'backup_status'] = '已备份'
                
                success_count += 1
                # print(f"已备份: {android_path} -> {local_path}")
            except Exception as e:
                print(f"备份失败: {android_path} - {str(e)}")
                
        # 保存映射表
        self._save_mapping_table()
        print(f"备份完成，成功备份 {success_count} 个文件")
        return success_count

    def remove_backedup(self, file_types: Optional[List[str]] = None, 
                       only_duplicates: bool = False) -> int:
        """
        删除已备份的文件
        
        参数:
            file_types: 文件类型列表，可选值为 'video', 'image', 'audio', 'document' 或 None(所有类型)
            only_duplicates: 是否只删除重复文件，默认为False
            
        返回:
            成功删除的文件数量
        """
        # 筛选需要删除的文件
        query = 'backup_status == "已备份" and original_deleted == False'
        
        if file_types is not None:
            file_types_str = "', '".join(file_types)
            query += f' and file_type in ["{file_types_str}"]'
            
        if only_duplicates:
            # 查找重复文件的MD5
            duplicate_hashes = self.mapping_table.groupby('md5_hash') \
                .filter(lambda x: len(x) > 1)['md5_hash'].unique()
            if duplicate_hashes.size > 0:
                md5_str = "', '".join(duplicate_hashes)
                query += f' and md5_hash in ["{md5_str}"]'
            else:
                print("没有找到重复文件")
                return 0
                
        files_to_remove = self.mapping_table.query(query)
        
        if files_to_remove.empty:
            print("没有需要删除的文件")
            return 0
            
        print(f"准备删除 {len(files_to_remove)} 个已备份文件...")
        success_count = 0
        
        for _, row in tqdm(files_to_remove.iterrows(), total=len(files_to_remove), desc="删除文件"):
            android_path = row['android_path']
            is_system = row['is_system']
            
            # 系统文件不删除
            if is_system:
                continue
                
            # 执行删除
            try:
                self._run_adb_command(['shell', 'rm', f'"{android_path}"'])
                
                # 更新映射表中的删除状态
                index = row.name
                self.mapping_table.loc[index, 'original_deleted'] = True
                
                success_count += 1
                print(f"已删除: {android_path}")
            except Exception as e:
                print(f"删除失败: {android_path} - {str(e)}")
                
        # 保存映射表
        self._save_mapping_table()
        print(f"删除完成，成功删除 {success_count} 个文件")
        return success_count

    def get_backup_stats(self) -> Dict[str, int]:
        """获取备份统计信息"""
        if self.mapping_table.empty:
            return {
                'total_files': 0,
                'video': 0,
                'image': 0,
                'audio': 0,
                'document': 0,
                'system_files': 0,
                'user_files': 0,
                'backed_up': 0,
                'not_backed_up': 0,
                'deleted_files': 0
            }
            
        return {
            'total_files': len(self.mapping_table),
            'video': len(self.mapping_table[self.mapping_table['file_type'] == 'video']),
            'image': len(self.mapping_table[self.mapping_table['file_type'] == 'image']),
            'audio': len(self.mapping_table[self.mapping_table['file_type'] == 'audio']),
            'document': len(self.mapping_table[self.mapping_table['file_type'] == 'document']),
            'system_files': len(self.mapping_table[self.mapping_table['is_system'] == True]),
            'user_files': len(self.mapping_table[self.mapping_table['is_system'] == False]),
            'backed_up': len(self.mapping_table[self.mapping_table['backup_status'] == '已备份']),
            'not_backed_up': len(self.mapping_table[self.mapping_table['backup_status'] == '未备份']),
            'deleted_files': len(self.mapping_table[self.mapping_table['original_deleted'] == True])
        }

    def find_duplicates(self) -> pd.DataFrame:
        """查找备份中的重复文件"""
        if self.mapping_table.empty:
            return pd.DataFrame()
            
        # 按MD5哈希分组并查找重复项
        return self.mapping_table[self.mapping_table['md5_hash'] != 'unknown'] \
            .groupby('md5_hash') \
            .filter(lambda x: len(x) > 1) \
            .sort_values('md5_hash')    