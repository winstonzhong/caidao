"""
媒体分析服务客户端工具
用于访问 localhost:8002 上的 media_fenxi 服务
"""

import requests
import os
from typing import Union, Dict, Any


# 服务配置
DEFAULT_BASE_URL = "http://localhost:8002"


class MediaFenxiClient:
    """媒体分析服务客户端"""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        """
        初始化客户端
        
        Args:
            base_url: 服务基础URL，默认 http://localhost:8002
        """
        self.base_url = base_url.rstrip("/")
        self.analyze_url = f"{self.base_url}/analyze"
        self.health_url = f"{self.base_url}/health"
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            服务状态信息
        """
        try:
            response = requests.get(self.health_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"健康检查失败: {str(e)}"
            }
    
    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        分析图片
        
        Args:
            image_path: 图片文件路径
        
        Returns:
            分析结果
            {
                "success": bool,
                "file_path": str,
                "file_type": "image",
                "result": str,
                "message": str
            }
        """
        if not os.path.exists(image_path):
            return {
                "success": False,
                "file_path": image_path,
                "file_type": "image",
                "result": "",
                "message": f"文件不存在: {image_path}"
            }
        
        try:
            response = requests.post(
                self.analyze_url,
                json={"file_path": image_path},
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "file_path": image_path,
                "file_type": "image",
                "result": "",
                "message": f"请求失败: {str(e)}"
            }
    
    def analyze_video(self, video_path: str) -> Dict[str, Any]:
        """
        分析视频（抽取3帧），将多帧结果合并为整体描述
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            分析结果
            {
                "success": bool,
                "file_path": str,
                "file_type": "video",
                "result": str,  # 合并后的整体描述
                "frames": [     # 原始帧分析结果（可选）
                    {"frame_index": 1, "frame_path": str, "description": str},
                    {"frame_index": 2, "frame_path": str, "description": str},
                    {"frame_index": 3, "frame_path": str, "description": str}
                ],
                "message": str
            }
        """
        if not os.path.exists(video_path):
            return {
                "success": False,
                "file_path": video_path,
                "file_type": "video",
                "result": "",
                "message": f"文件不存在: {video_path}"
            }
        
        try:
            response = requests.post(
                self.analyze_url,
                json={"file_path": video_path},
                timeout=120  # 视频分析可能需要更长时间
            )
            response.raise_for_status()
            data = response.json()
            
            # 如果请求成功，合并多帧结果
            if data.get("success") and data.get("file_type") == "video":
                frames = data.get("result", [])
                
                if frames:
                    # 提取所有帧的描述
                    descriptions = []
                    for frame in frames:
                        desc = frame.get("description", "")
                        if desc and not desc.startswith("Error"):
                            descriptions.append(desc)
                    
                    # 合并描述（去重并整合）
                    if descriptions:
                        # 简单合并：用分号连接各帧描述
                        merged_result = "; ".join(descriptions)
                        
                        # 保存原始帧数据到 frames 字段
                        data["frames"] = frames
                        # 用合并后的结果替换原来的列表
                        data["result"] = merged_result
                    else:
                        data["result"] = "无法获取视频描述"
                else:
                    data["result"] = "视频分析结果为空"
            
            return data
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "file_path": video_path,
                "file_type": "video",
                "result": "",
                "message": f"请求失败: {str(e)}"
            }
    
    def analyze(self, file_path: str) -> Dict[str, Any]:
        """
        自动识别文件类型并分析
        
        Args:
            file_path: 媒体文件路径（图片或视频）
        
        Returns:
            分析结果
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "file_path": file_path,
                "file_type": "unknown",
                "result": "",
                "message": f"文件不存在: {file_path}"
            }
        
        # 根据扩展名判断文件类型
        ext = os.path.splitext(file_path)[1].lower()
        image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}
        video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        
        if ext in image_exts:
            return self.analyze_image(file_path)
        elif ext in video_exts:
            return self.analyze_video(video_path)
        else:
            return {
                "success": False,
                "file_path": file_path,
                "file_type": "unknown",
                "result": "",
                "message": f"不支持的文件类型: {ext}"
            }


# 便捷函数
def analyze_image(image_path: str, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    分析图片（便捷函数）
    
    Args:
        image_path: 图片文件路径
        base_url: 服务基础URL
    
    Returns:
        图片描述文本
    """
    client = MediaFenxiClient(base_url)
    result = client.analyze_image(image_path)
    
    if result.get("success"):
        return result.get("result", "")
    else:
        return f"分析失败: {result.get('message', '未知错误')}"


def analyze_video(video_path: str, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    分析视频（便捷函数）
    
    Args:
        video_path: 视频文件路径
        base_url: 服务基础URL
    
    Returns:
        视频整体描述文本（多帧合并结果）
    """
    client = MediaFenxiClient(base_url)
    result = client.analyze_video(video_path)
    
    if result.get("success"):
        return result.get("result", "")
    else:
        return f"分析失败: {result.get('message', '未知错误')}"


def analyze(file_path: str, base_url: str = DEFAULT_BASE_URL) -> str:
    """
    自动识别文件类型并分析（便捷函数）
    
    Args:
        file_path: 媒体文件路径
        base_url: 服务基础URL
    
    Returns:
        媒体描述文本（图片或视频都返回字符串）
    """
    client = MediaFenxiClient(base_url)
    result = client.analyze(file_path)
    
    if not result.get("success"):
        return f"分析失败: {result.get('message', '未知错误')}"
    
    return result.get("result", "")


# 测试函数
def test_client():
    """测试客户端"""
    print("=" * 60)
    print("媒体分析服务客户端测试")
    print("=" * 60)
    
    client = MediaFenxiClient()
    
    # 测试1: 健康检查
    print("\n【测试1】健康检查")
    health = client.health_check()
    print(f"结果: {health}")
    
    if health.get("status") != "healthy":
        print("✗ 服务未就绪，跳过后续测试")
        return
    print("✓ 服务健康")
    
    # 测试2: 分析图片（需要实际图片文件）
    print("\n【测试2】分析图片")
    # 使用一个测试图片路径（如果不存在会返回错误）
    test_image = "/mnt/56T/download/Screenshot_20260121_155522_com.ss.android.ugc.aweme.jpg"
    
    if os.path.exists(test_image):
        result = client.analyze_image(test_image)
        print(f"成功: {result.get('success')}")
        print(f"文件类型: {result.get('file_type')}")
        print(f"结果: {result.get('result', '')}")
        print(f"消息: {result.get('message')}")
    else:
        print(f"跳过（测试图片不存在: {test_image}）")
        print("如需测试，请准备一张图片并修改 test_image 变量")
    
    # 测试3: 分析视频（需要实际视频文件）
    print("\n【测试3】分析视频")
    test_video = "/mnt/56T/backup/UJN0221118004154/Media/Videos/致敬伟人_ee23d8c2.mp4"
    
    if os.path.exists(test_video):
        result = client.analyze_video(test_video)
        print(f"成功: {result.get('success')}")
        print(f"文件类型: {result.get('file_type')}")
        print(f"帧数: {len(result.get('frames', []))}")
        print(f"结果: {result.get('result', '')}")
        print(f"消息: {result.get('message')}")
        
    else:
        print(f"跳过（测试视频不存在: {test_video}）")
        print("如需测试，请准备一个视频并修改 test_video 变量")
    
    # 测试4: 便捷函数
    print("\n【测试4】便捷函数")
    print(f"analyze_image 函数可用: {analyze_image}")
    print(f"analyze_video 函数可用: {analyze_video}")
    print(f"analyze 函数可用: {analyze}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_client()
