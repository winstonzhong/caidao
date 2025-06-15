import cv2
import numpy as np

def scale_bgra_image(image, scale):
    """
    高质量缩放BGRA图像，保持Alpha通道为二值(0或255)
    
    参数:
    image: 输入的BGRA格式图像
    scale: 缩放比例(float)
    
    返回:
    numpy.ndarray: 缩放后的BGRA图像，Alpha通道为二值(0或255)
    """
    # 确保输入图像是BGRA格式
    if image.shape[2] != 4:
        raise ValueError("输入图像必须是BGRA格式")
    
    # 分离通道
    b, g, r, a = cv2.split(image)
    
    # 缩放RGB通道，使用高质量插值方法
    new_size = (int(image.shape[1] * scale), int(image.shape[0] * scale))
    rgb = cv2.merge([b, g, r])
    rgb_scaled = cv2.resize(rgb, new_size, interpolation=cv2.INTER_CUBIC)
    
    # 缩放Alpha通道，使用最近邻插值以保持二值特性
    a_scaled = cv2.resize(a, new_size, interpolation=cv2.INTER_NEAREST)
    
    # 确保Alpha通道严格二值化(0或255)
    _, a_scaled = cv2.threshold(a_scaled, 127, 255, cv2.THRESH_BINARY)
    
    # 合并处理后的通道
    b_scaled, g_scaled, r_scaled = cv2.split(rgb_scaled)
    result = cv2.merge([b_scaled, g_scaled, r_scaled, a_scaled])
    
    return result

def scale_bgra_image_without_alpha_processing(image, scale):
    """不单独处理Alpha通道的缩放函数"""
    if image.shape[2] != 4:
        raise ValueError("输入图像必须是BGRA格式")
    
    new_size = (int(image.shape[1] * scale), int(image.shape[0] * scale))
    # 直接缩放整个图像（包括Alpha通道）
    return cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)

# 使用示例
if __name__ == "__main__":
    # 加载带Alpha通道的图像
    image = cv2.imread("input.png", cv2.IMREAD_UNCHANGED)
    
    if image is None:
        print("无法读取图像")
    else:
        # 缩放比例
        scale = 0.5
        
        # 执行缩放
        scaled_image = scale_bgra_image(image, scale)
        
        # 保存结果
        cv2.imwrite("scaled_output.png", scaled_image)
        
        print(f"图像已成功缩放至原尺寸的{scale*100}%")
