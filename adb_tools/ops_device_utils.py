"""
Ops 设备操作公用工具类

为 LLM 代码生成提供统一、稳健的底层设备操作封装。
所有方法均基于 caidao/adb_tools 的成熟实现，避免重复编写底层逻辑。

典型使用场景（Ops 代码块中）:
    # 上传网络图片到设备
    # 注意：OpsDeviceUtils 已由 tool_xpath.py 全局导入，无需写 import
    device_path = OpsDeviceUtils.上传文件到设备(
        "https://example.com/image.png",
        job.device
    )
    
设计原则:
1. 单一职责: 每个函数只做一件事，参数尽量少
2. 容错兜底: 自动处理 56T 内网链接、外网 URL、本地路径等多种输入
3. 零副作用: 不修改传入对象的内部状态，不操作全局变量
4. 可观测: 关键步骤打印日志，便于调试
"""

import os
from typing import Optional, Union

import tool_static


class OpsDeviceUtils:
    """
    Ops 代码块设备操作工具类

    封装文件上传、下载、广播等常用设备操作，内部直接复用 caidao 底层库。
    支持从 Device 模型、SteadyDevice、BaseAdb 实例中提取 ADB 连接。
    """

    @staticmethod
    def _获取adb(device):
        """
        从各种设备对象中提取 BaseAdb 实例。

        支持的 device 类型:
        - tasks.models.Device (Django ORM 模型)
        - adb_tools.tool_xpath.SteadyDevice / SnapShotDevice
        - adb_tools.helper_adb.BaseAdb (直接传入)
        - 任何带有 .adb 属性的对象

        参数:
            device: 设备对象

        返回:
            BaseAdb 实例

        异常:
            ValueError: 无法识别设备类型或提取 ADB 失败
        """
        from adb_tools.helper_adb import BaseAdb

        # 已经是 BaseAdb 实例
        if isinstance(device, BaseAdb):
            return device

        # 带有 .adb 属性的对象 (Device 模型、SteadyDevice 等)
        if hasattr(device, "adb") and isinstance(device.adb, BaseAdb):
            return device.adb

        # 带有 device_id 的对象 (Device 模型裸实例)
        if hasattr(device, "device_id") and device.device_id:
            return BaseAdb({"id": device.device_id})

        # 字典类型 (如 {"ip": "192.168.1.100", "port": 5555})
        if isinstance(device, dict):
            return BaseAdb(device)

        raise ValueError(
            f"无法从 device 提取 ADB 连接，类型: {type(device).__name__}"
        )

    @staticmethod
    def 上传文件到设备(
        url: str,
        device,
        fname: Optional[str] = None,
        clean_temp: bool = True,
    ) -> str:
        """
        将 URL 对应的文件上传至设备下载目录，并触发媒体扫描广播。

        内部自动识别输入类型并选择最优路径:
        - 56T 内网本地文件: 直接 adb push，跳过网络下载
        - 内网/外网 URL: 先下载到临时文件，再 adb push
        - Termux 环境: 使用本地存储路径直接推送

        推送完成后自动调用 `am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE`
        通知系统媒体库刷新，确保相册、微信等应用能立即发现该文件。

        参数:
            url: 文件 URL 或本地路径。支持 http(s)://、file://、/mnt/56T/... 等
            device: 目标设备。支持 Device 模型、SteadyDevice、BaseAdb 实例
            fname: 指定设备端文件名（可选）。
                   不传时，优先从 URL 路径推断；推断失败则使用时间戳
            clean_temp: 推送前是否清理设备临时目录（默认 True）

        返回:
            设备上的完整目标路径，例如:
            - `/sdcard/Download/1715234567.89.png`
            - `/sdcard/Download/my_image.jpg`

        异常:
            requests.RequestException: URL 下载失败
            ValueError: 设备类型无法识别
            RuntimeError: adb push 或广播失败

        典型 Ops 代码示例:
            >>> OpsDeviceUtils.上传文件到设备(
            ...     "https://file.j1.sale/api/file/2024/photo.jpg",
            ...     job.device
            ... )
            '/sdcard/Download/1715234567.89.jpg'

            >>> OpsDeviceUtils.上传文件到设备(
            ...     job.remote_obj.data.get('图片url'),
            ...     job.device,
            ...     fname="uploaded_pic.png"
            ... )
            '/sdcard/Download/uploaded_pic.png'
        """
        adb = OpsDeviceUtils._获取adb(device)

        print(f"[OpsDeviceUtils] 开始上传: url={url}, fname={fname}")

        # 情况1: 56T 内网本地文件 —— 直接 push，无需网络下载
        if tool_static.is_inner() and tool_static.is_56t_url(url):
            fpath = tool_static.链接到路径(url)
            print(f"[OpsDeviceUtils] 识别为 56T 本地文件: {fpath}")
            dst = adb.push_file_to_download(
                src=fpath,
                fname=fname,
                clean_temp=clean_temp,
            )
            print(f"[OpsDeviceUtils] 56T 直推完成: {dst}")
            return dst

        # 情况2: 内网非 56T 链接 或 外网 URL —— 先下载再 push
        # BaseAdb.push_url_to_download 内部已处理:
        #   - Content-Type 推断后缀
        #   - 临时文件清理
        #   - push_file_to_temp → 自动 broadcast
        print(f"[OpsDeviceUtils] 识别为网络 URL，先下载后推送")
        dst = adb.push_url_to_download(
            url=url,
            use_timestamp=(fname is None),
            fname=fname,
        )
        print(f"[OpsDeviceUtils] URL 下载推送完成: {dst}")
        return dst

    @staticmethod
    def 上传本地文件到设备(
        local_path: str,
        device,
        fname: Optional[str] = None,
        target_dir: Optional[str] = None,
    ) -> str:
        """
        将本地文件推送到设备指定目录，并触发媒体扫描广播。

        参数:
            local_path: 本地绝对路径，例如 `/mnt/56T/file/photo.jpg`
            device: 目标设备
            fname: 设备端文件名（可选，默认使用本地文件名）
            target_dir: 设备目标目录（可选，默认 `/sdcard/Download`）

        返回:
            设备上的完整目标路径

        示例:
            >>> OpsDeviceUtils.上传本地文件到设备(
            ...     "/home/user/pic.png",
            ...     job.device,
            ...     target_dir="/sdcard/DCIM/Camera"
            ... )
            '/sdcard/DCIM/Camera/pic.png'
        """
        adb = OpsDeviceUtils._获取adb(device)

        if not os.path.isfile(local_path):
            raise FileNotFoundError(f"本地文件不存在: {local_path}")

        print(f"[OpsDeviceUtils] 推送本地文件: {local_path}")

        if target_dir:
            dst = adb.push_file_to_temp(
                src=local_path,
                base_dir=target_dir,
                fname=fname,
            )
        else:
            dst = adb.push_file_to_download(
                src=local_path,
                fname=fname,
            )

        print(f"[OpsDeviceUtils] 本地推送完成: {dst}")
        return dst

    @staticmethod
    def 发送媒体扫描广播(device, fpath: str) -> str:
        """
        手动发送媒体扫描广播，通知系统媒体库刷新指定文件。

        通常不需要手动调用，因为 `上传文件到设备` 和 `上传本地文件到设备`
        已在推送完成后自动触发广播。

        仅在以下场景需要手动调用:
        - 通过其他方式（如 shell 命令）写入文件后，需要相册/微信发现
        - 文件被重命名或移动后，需要更新媒体库索引

        参数:
            device: 目标设备
            fpath: 设备上的文件完整路径，例如 `/sdcard/Download/photo.jpg`

        返回:
            adb shell 命令输出

        示例:
            >>> OpsDeviceUtils.发送媒体扫描广播(
            ...     job.device,
            ...     "/sdcard/Download/photo.jpg"
            ... )
        """
        adb = OpsDeviceUtils._获取adb(device)
        result = adb.broadcast(fpath)
        print(f"[OpsDeviceUtils] 媒体扫描广播已发送: {fpath}")
        return result
