"""
资源路径查找工具模块
提供开发环境和 PyInstaller 打包环境的兼容支持
"""

import sys
import os
from pathlib import Path
from typing import Union, List, Optional


def get_resource_path(
        relative_path: Union[str, Path],
        search_dirs: Optional[List[Union[str, Path]]] = None,
        check_exists: bool = True
) -> Path:
    """
    获取资源文件的绝对路径，兼容开发环境和 PyInstaller 打包环境

    搜索顺序：
    1. 打包环境：exe 同级目录
    2. 打包环境：exe/_internal/ 目录
    3. 打包环境：sys._MEIPASS（PyInstaller 临时解压目录）
    4. 开发环境：当前工作目录
    5. 开发环境：当前文件所在目录
    6. 用户自定义搜索目录

    Args:
        relative_path: 资源的相对路径（如 'cn_stopwords.txt' 或 'mobans/template.html'）
        search_dirs: 额外的搜索目录列表（可选）
        check_exists: 是否检查文件存在性，为 True 时找不到会抛出异常

    Returns:
        Path: 资源的绝对路径

    Raises:
        FileNotFoundError: 当 check_exists=True 且找不到文件时

    Examples:
        >>> # 查找停用词文件
        >>> path = get_resource_path('cn_stopwords.txt')
        >>> 
        >>> # 查找模板文件
        >>> path = get_resource_path('mobans/template.html')
        >>> 
        >>> # 不检查存在性
        >>> path = get_resource_path('config/my.ini', check_exists=False)
    """
    relative_path = Path(relative_path)

    # 构建搜索路径列表
    search_paths = []

    # 1. 打包环境：exe 同级目录
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        search_paths.append(exe_dir / relative_path)
        search_paths.append(exe_dir / '_internal' / relative_path)

        # 2. PyInstaller 临时解压目录
        if hasattr(sys, '_MEIPASS'):
            search_paths.append(Path(sys._MEIPASS) / relative_path)

    # 3. 当前工作目录
    search_paths.append(Path.cwd() / relative_path)

    # 4. 当前文件所在目录（向上查找，最多3层）
    try:
        current_file_dir = Path(__file__).resolve().parent
        for level in range(4):  # 当前目录 + 向上3层
            search_paths.append(current_file_dir / relative_path)
            current_file_dir = current_file_dir.parent
    except NameError:
        pass  # __file__ 不可用（如交互式环境）

    # 5. 用户自定义搜索目录
    if search_dirs:
        for dir_path in search_dirs:
            search_paths.append(Path(dir_path) / relative_path)

    # 查找第一个存在的路径
    for path in search_paths:
        if not check_exists or path.exists():
            return path.resolve()

    # 找不到且需要检查存在性，抛出异常
    if check_exists:
        error_msg = (
                f"找不到资源文件: {relative_path}\n"
                f"搜索路径:\n" +
                '\n'.join([f"  - {p}" for p in search_paths[:5]]) +  # 只显示前5个
                "\n请确保文件已正确打包或放置在正确位置"
        )
        raise FileNotFoundError(error_msg)

    # 不检查存在性，返回第一个候选路径（打包环境优先）
    return search_paths[0] if search_paths else Path(relative_path)


def get_resource_dir(
        dir_name: str,
        check_exists: bool = True
) -> Path:
    """
    获取资源目录的绝对路径

    Args:
        dir_name: 目录名称（如 'mobans', 'prompt', 'templates'）
        check_exists: 是否检查目录存在性

    Returns:
        Path: 目录的绝对路径

    Examples:
        >>> mobans_dir = get_resource_dir('mobans')
        >>> prompt_dir = get_resource_dir('prompt')
    """
    return get_resource_path(dir_name, check_exists=check_exists)


def is_frozen() -> bool:
    """
    判断是否处于 PyInstaller 打包环境

    Returns:
        bool: True 表示打包环境，False 表示开发环境
    """
    return getattr(sys, 'frozen', False)


def get_base_dir() -> Path:
    """
    获取项目根目录

    打包环境：exe 所在目录
    开发环境：当前文件所在目录（caidao目录）

    Returns:
        Path: 项目根目录
    """
    if is_frozen():
        return Path(sys.executable).parent / '_internal'
    else:
        # 开发环境：caidao/tool_resource.py -> caidao/
        return Path(__file__).resolve().parent


# 兼容性别名
get_path = get_resource_path  # 短名称别名

if __name__ == '__main__':
    # 测试代码
    print(f"是否打包环境: {is_frozen()}")
    print(f"基础目录: {get_base_dir()}")

    try:
        path = get_resource_path('cn_stopwords.txt')
        print(f"找到停用词文件: {path}")
    except FileNotFoundError as e:
        print(f"未找到: {e}")