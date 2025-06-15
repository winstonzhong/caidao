import cv2
import numpy as np
from helper_scale_bgra_image import scale_bgra_image, scale_bgra_image_without_alpha_processing

def preprocess_image(image, input_x, input_y, scale_factor=1):
    if scale_factor != 1:
        image = scale_bgra_image_without_alpha_processing(image, scale_factor)
        input_x *= scale_factor
        input_y *= scale_factor
    return image, input_x, input_y


def align_image(image, input_x, input_y, width, height, scale_factor=1):
    """
    将输入的BGRA图像按指定坐标对齐到新的输出图像中
    
    参数:
    image: 输入的BGRA格式图像
    input_x: 输入图像中用于对齐的X坐标
    input_y: 输入图像中用于对齐的底部Y坐标
    width: 输出图像的宽度
    height: 输出图像的高度
    
    返回:
    numpy.ndarray: 对齐后的BGRA格式图像
    """
    image, input_x, input_y = preprocess_image(image, input_x, input_y, scale_factor)

    bottom_margin = 20
    # 创建一个透明的输出图像
    output = np.zeros((height, width, 4), dtype=np.uint8)
    
    # 计算输出图像的中心X坐标和底部Y坐标
    center_x = width // 2
    bottom_y = height - 1 - bottom_margin
    
    # 计算输入图像需要放置的位置
    # 水平方向：input_x对齐到center_x
    # 垂直方向：input_y对齐到bottom_y
    x_offset = int(center_x - input_x)
    y_offset = int(bottom_y - input_y)
    
    # 计算输入图像在输出图像中的边界
    input_height, input_width = image.shape[:2]
    x_start = max(0, x_offset)
    y_start = max(0, y_offset)
    x_end = min(width, x_offset + input_width)
    y_end = min(height, y_offset + input_height)
    
    # 计算需要从输入图像中提取的区域
    input_x_start = max(0, -x_offset)
    input_y_start = max(0, -y_offset)
    input_x_end = input_x_start + (x_end - x_start)
    input_y_end = input_y_start + (y_end - y_start)
    
    # 将输入图像的有效区域复制到输出图像中
    if (x_end > x_start) and (y_end > y_start):
        output[y_start:y_end, x_start:x_end] = image[input_y_start:input_y_end, input_x_start:input_x_end]
    else:
        raise ValueError("输入图像与输出图像不重叠")
    
    return output

# 使用示例
if __name__ == "__main__":
    # 加载一个带透明背景的图像
    image = cv2.imread("input.png", cv2.IMREAD_UNCHANGED)
    
    if image is None:
        print("无法读取图像")
    else:
        # 假设我们要将图像的中心X坐标和底部Y坐标对齐到输出图像的中心和底部
        input_x = image.shape[1] // 2  # 输入图像的中心X
        input_y = image.shape[0] - 1   # 输入图像的底部Y
        
        # 输出图像的尺寸
        output_width = 800
        output_height = 600
        
        # 执行对齐
        aligned_image = align_image(image, input_x, input_y, output_width, output_height)
        
        # 保存结果
        cv2.imwrite("aligned_output.png", aligned_image)
        
        print("图像对齐完成")
