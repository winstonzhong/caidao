import cv2
import numpy as np

def calculate_horizontal_symmetry_line(image):
    """
    计算BGRA图像中Alpha通道非零区域的水平对称中线
    
    参数:
    image: 输入的BGRA格式图像
    
    返回:
    float: 水平对称中线的Y坐标（相对于图像高度的比例）
    """
    # 提取Alpha通道
    if image.shape[2] != 4:
        raise ValueError("输入图像必须是BGRA格式")
    
    alpha = image[:, :, 3]
    
    # 创建二值掩码（Alpha>0的区域）
    _, mask = cv2.threshold(alpha, 1, 255, cv2.THRESH_BINARY)
    
    # 计算轮廓
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return 0.5  # 如果没有找到轮廓，返回图像中心
    
    # 找到最大轮廓（通常是主体）
    largest_contour = max(contours, key=lambda c: cv2.contourArea(c))
    
    # 计算轮廓的边界框
    x, y, w, h = cv2.boundingRect(largest_contour)
    
    # 提取感兴趣区域(ROI)
    roi = mask[y:y+h, x:x+w]
    
    # 计算每一行的非零像素数量
    row_sums = np.sum(roi, axis=1)
    
    # 找到非零像素的有效范围
    valid_rows = np.where(row_sums > 0)[0]
    
    if len(valid_rows) < 2:
        return (y + h/2) / image.shape[0]  # 如果有效行数太少，返回边界框中心
    
    # 为每行计算左右两边的像素分布
    symmetry_scores = []
    
    for row in valid_rows:
        # 获取当前行的像素分布
        row_data = roi[row, :]
        
        # 找到非零像素的左右边界
        left, right = np.where(row_data > 0)[0][[0, -1]]
        
        # 计算左右边界的中点
        midpoint = (left + right) / 2
        
        # 计算对称性得分（左右两侧的相似度）
        left_half = row_data[left:int(midpoint)+1][::-1]  # 反转左半部分以便比较
        right_half = row_data[int(midpoint):right+1]
        
        # 取较短的一侧长度
        min_len = min(len(left_half), len(right_half))
        
        if min_len > 0:
            # 计算归一化的对称得分
            score = 1.0 - np.mean(np.abs(left_half[:min_len] - right_half[:min_len])) / 255.0
            symmetry_scores.append((score, midpoint, row))
    
    if not symmetry_scores:
        return (y + h/2) / image.shape[0]  # 如果无法计算对称性，返回边界框中心
    
    # 按对称性得分排序，取前30%的行
    symmetry_scores.sort(key=lambda x: x[0], reverse=True)
    top_rows = symmetry_scores[:max(1, int(len(symmetry_scores) * 0.3))]
    
    # 计算前30%行的对称性得分均值
    mean_score = np.mean([score for score, _, _ in top_rows])
    
    # 找到最接近均值的行
    closest_row = min(top_rows, key=lambda x: abs(x[0] - mean_score))
    
    # 获取该行在ROI中的Y坐标
    roi_symmetry_x = closest_row[1]
    
    # 转换为原图中的坐标
    symmetry_x = x + roi_symmetry_x
    
    # 返回相对于图像高度的比例
    # return symmetry_x / image.shape[1]
    return int(symmetry_x), y+h, roi.shape


def show_test(image):
    symmetry_x, bottom_y, shape = calculate_horizontal_symmetry_line(image)
    
    print(f"对应像素坐标 X: {symmetry_x}, 底部坐标 Y: {bottom_y}, 区域尺寸: {shape}", )
    
    result = image.copy()
    result[:, :, 0:3][:,symmetry_x-1:symmetry_x+1, ...] = [0, 0, 255]
    result[:, :, 0:3][bottom_y-1:bottom_y+1, ...] = [0, 255, 0]

    
    # 显示结果
    cv2.imshow("Image with Symmetry Line", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()    
