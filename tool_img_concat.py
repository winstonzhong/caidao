import cv2
import numpy as np

import pathlib



def get_path(save_path):
    base_dir = pathlib.Path(__file__).parent
    return base_dir / "ut" / save_path


# ========== 提取为全局函数 ==========
def 生成模拟手机截屏(是否上半部分: bool, save_path: str = None) -> np.ndarray:
    """
    生成模拟手机截屏图片（含状态栏、标题栏、重合内容），可选保存为文件

    Args:
        是否上半部分: True=生成上半截屏，False=生成下半截屏
        save_path: 保存图片的路径（如"up_img.png"），None则不保存

    Returns:
        cv2格式的图片数组
    """
    # base_dir = pathlib.Path(__file__).parent
    # save_path = base_dir / "ut" / save_path
    save_path = get_path(save_path)

    if save_path.exists():
        img = cv2.imread(str(save_path))
    else:
        # 模拟手机截屏尺寸：1080x2400（宽x高），3通道RGB（cv2默认BGR）
        img = np.ones((2400, 1080, 3), dtype=np.uint8) * 255  # 白色背景
        # 1. 顶部状态栏（红色，高度40px）- 固定区域
        img[0:40, :] = [0, 0, 255]  # BGR格式，红色
        # 2. APP标题栏（蓝色，高度60px）- 固定区域
        img[40:100, :] = [255, 0, 0]  # 蓝色
        # 3. 中间内容区域（模拟重合/非重合内容）
        font = cv2.FONT_HERSHEY_SIMPLEX
        if 是否上半部分:
            # 上半部分：包含重合区域+上半独有内容
            cv2.putText(img, "APP-up", (50, 200), font, 2, (0, 0, 0), 3)
            cv2.putText(
                img, "overlapping-123456", (50, 800), font, 3, (0, 128, 0), 5
            )  # 重合文字
        else:
            # 下半部分：开头是重合区域+下半独有内容
            cv2.putText(
                img, "overlapping-123456", (50, 200), font, 3, (0, 128, 0), 5
            )  # 重合文字
            cv2.putText(img, "APP-down", (50, 800), font, 2, (0, 0, 0), 3)

        # 保存图片到文件（方便调试）
        if save_path is not None:
            cv2.imwrite(str(save_path), img)
    return img


def 生成无重合图片(save_path: str = "test_no_overlap.png") -> np.ndarray:
    # base_dir = pathlib.Path(__file__).parent
    # save_path = base_dir / "ut" / save_path
    save_path = get_path(save_path)

    if save_path.exists():
        img_no_overlap = cv2.imread(str(save_path))
    else:
        img_no_overlap = np.ones((2400, 1080, 3), dtype=np.uint8) * 255
        cv2.putText(
            img_no_overlap,
            "test_no_overlap",
            (50, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            2,
            (0, 0, 0),
            3,
        )
        cv2.imwrite(save_path, img_no_overlap)
    return img_no_overlap


def 上下截屏图片无缝拼接(
    img_up: np.ndarray, img_down: np.ndarray, save_path: str = None
) -> np.ndarray:
    """
    无缝拼接上下两张手机截屏图片，核心逻辑：
    1. 验证输入图片有效性（尺寸、通道数一致）
    2. 避开状态栏/APP标题栏等固定区域，仅从中部区域检测重合接缝
    3. 用模板匹配找到最佳重合位置，无有效重合则抛异常
    4. 裁剪重复区域，拼接图片并返回

    单元测试示例（基于实际图片文件，方便调试）:
    >>> # 第一步：生成测试用图片文件（全局函数生成）
    >>> img_up = 生成模拟手机截屏(True, "test_up.png")   # 生成上半截屏文件
    >>> img_down = 生成模拟手机截屏(False, "test_down.png") # 生成下半截屏文件
    >>> img_no_overlap = 生成无重合图片()
    >>> # 第二步：读取图片文件测试拼接功能
    >>> result = 上下截屏图片无缝拼接(img_up, img_down)
    >>> # 验证拼接结果
    >>> isinstance(result, np.ndarray)
    True
    >>> result.shape[0] > 0 and result.shape[1] == 1080  # 宽度不变，高度有效
    True
    """
    # ========== 步骤1：输入有效性校验 ==========
    # 检查图片是否为空
    if img_up is None or img_down is None:
        raise ValueError("输入图片不能为空")
    # 检查图片通道数一致（均为灰度/均为彩色）
    if len(img_up.shape) != len(img_down.shape):
        raise ValueError("上下图片的通道数不一致（一张灰度/一张彩色）")
    # 检查宽度一致（手机截屏宽度相同）
    if img_up.shape[1] != img_down.shape[1]:
        raise ValueError(
            f"上下图片宽度不一致：上{img_up.shape[1]}px，下{img_down.shape[1]}px"
        )

    # ========== 步骤2：定义固定区域，提取有效匹配区域 ==========
    # 手机截屏固定区域高度（可根据实际情况调整）
    status_bar_h = 40  # 状态栏高度（顶部）
    title_bar_h = 60  # APP标题栏高度（状态栏下）
    # 有效匹配区域：避开固定区域，仅取中间内容区
    # 上图片：取底部20%的区域作为模板（避开顶部固定区）
    template_h = int(img_up.shape[0] * 0.2)  # 模板高度（匹配用）
    template = img_up[-template_h:, :]  # 上图片的底部区域（待匹配模板）
    # 下图片：取顶部30%的区域作为待匹配区域（比模板大，确保能匹配到）
    search_h = int(img_down.shape[0] * 0.3)
    search_area = img_down[:search_h, :]  # 下图片的顶部区域

    # ========== 步骤3：模板匹配找重合接缝 ==========
    # 使用归一化相关系数匹配（抗亮度变化，适合截屏匹配）
    result = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
    # 找到最佳匹配位置（最大值为最佳匹配）
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    # 匹配置信度阈值（低于则认为无有效重合）
    match_threshold = 0.8
    if max_val < match_threshold:
        raise ValueError("两张图片未检测到有效重合的接缝，无法无缝拼接")

    # ========== 步骤4：计算重合区域，无缝拼接 ==========
    # max_loc[1]是下图片中模板匹配到的y坐标（重合起始位置）
    overlap_y = max_loc[1]
    # 拼接逻辑：上图片全部 + 下图片从（重合起始+模板高度）开始的部分
    # （裁剪掉下图片中与上图片重合的区域）
    img_down_cropped = img_down[overlap_y + template_h :, :]
    # 垂直拼接图片
    merged_img = cv2.vconcat([img_up, img_down_cropped])

    return merged_img




def 上下截屏图片无缝拼接_v2(img_up, img_down):
    """
    改进版：增加纯色区域和边缘固定UI检测
    
    新增防护：
    1. 水平分布验证：确保匹配点不在同一垂直线
    2. 内容复杂度检查: 计算重合区域方差，拒绝低复杂度
    3. 左右边缘固定元素检测
    
    Examples:
        >>> # 测试场景：纯白背景聊天界面
        >>> h, w = 1920, 1080
        >>> 
        >>> # 创建上半部分（含白底）
        >>> img_up = np.full((h, w, 3), 255, dtype=np.uint8)
        >>> # 状态栏
        >>> cv2.rectangle(img_up, (0, 0), (w, 80), (200, 200, 200), -1)
        >>> # 消息气泡
        >>> cv2.rectangle(img_up, (100, 300), (w-100, 500), (230, 230, 230), -1)
        >>> cv2.putText(img_up, "消息1", (120, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 3)
        >>> # 大白块区域（无特征）
        >>> cv2.rectangle(img_up, (0, 600), (w, 1100), (255, 255, 255), -1)
        >>> 
        >>> # 创建下半部分（相似但白底偏移）
        >>> img_down = np.full((h, w, 3), 255, dtype=np.uint8)
        >>> # 同样状态栏
        >>> cv2.rectangle(img_down, (0, 0), (w, 80), (200, 200, 200), -1)
        >>> # 大白块区域
        >>> cv2.rectangle(img_down, (0, 200), (w, 700), (255, 255, 255), -1)
        >>> # 消息气泡2
        >>> cv2.rectangle(img_down, (100, 800), (w-100, 1000), (230, 230, 230), -1)
        >>> cv2.putText(img_down, "消息2", (120, 900), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,0,0), 3)
        >>> 
        >>> # 测试：应该能正确识别拼接位置
        >>> result = 上下截屏图片无缝拼接_v2(img_up, img_down)
        >>> result.shape[0] > h  # 高度增加
        True
        >>> result.shape[1] == w  # 宽度不变
        True
    """
    if img_up is None or img_down is None:
        raise ValueError("输入图片不能为None")
    
    if img_up.shape != img_down.shape:
        raise ValueError("两张图片尺寸和通道数必须相同")
    
    h, w = img_up.shape[:2]
    
    # 1. ORB特征检测
    orb = cv2.ORB_create(nfeatures=2000)
    kp1, des1 = orb.detectAndCompute(img_up, None)
    kp2, des2 = orb.detectAndCompute(img_down, None)
    
    if des1 is None or des2 is None or len(des1) < 10 or len(des2) < 10:
        raise ValueError("无法检测足够的特征点，可能是纯色内容过多")
    
    # 2. 暴力匹配
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    matches = sorted(matches, key=lambda x: x.distance)
    
    if len(matches) < 10:
        raise ValueError(f"匹配点过少({len(matches)}<10)，可能重叠区域不足或无有效内容")
    
    # 3. 提取匹配点
    src_pts = np.float32([kp1[m.queryIdx].pt for m in matches])
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches])
    
    # 4. RANSAC估计垂直偏移
    y_diffs = dst_pts[:, 1] - src_pts[:, 1]
    
    best_offset = 0
    max_inliers = 0
    
    for _ in range(100):
        idx = np.random.randint(0, len(y_diffs))
        offset = y_diffs[idx]
        inliers = np.sum(np.abs(y_diffs - offset) < 30)
        
        if inliers > max_inliers:
            max_inliers = inliers
            best_offset = offset
    
    if max_inliers < 5:
        raise ValueError("无法找到可靠的拼接共识，匹配点过于分散")
    
    offset_y = int(round(best_offset))
    
    # 5. 三重防护检查
    
    # 防护1: 水平分布验证（防止垂直线误匹配）
    valid_matches = np.where(np.abs(y_diffs - best_offset) < 30)[0]
    x_positions = src_pts[valid_matches, 0]
    x_variance = np.var(x_positions)
    
    if x_variance < (w * 0.05) ** 2:  # 水平方差过小
        raise ValueError("匹配点过于集中，可能是纯色区域或垂直边缘误匹配")
    
    # 防护2: 内容复杂度检查（计算重叠区域方差）
    overlap_h = h - abs(offset_y)
    if overlap_h > 50:  # 重叠区域足够大
        # 提取重叠区域
        if offset_y > 0:
            overlap_up = img_up[-overlap_h:, :]
            overlap_down = img_down[:overlap_h, :]
        else:
            overlap_up = img_down[-overlap_h:, :]
            overlap_down = img_up[:overlap_h, :]
        
        # 计算灰度方差（衡量内容复杂度）
        gray_up = cv2.cvtColor(overlap_up, cv2.COLOR_BGR2GRAY)
        gray_down = cv2.cvtColor(overlap_down, cv2.COLOR_BGR2GRAY)
        
        # 差异图
        diff = cv2.absdiff(gray_up, gray_down)
        variance = np.var(diff)
        
        if variance < 100:  # 阈值100经验值
            raise ValueError("重叠区域内容复杂度低，可能是纯色或重复背景")
    
    # 防护3: 防止仅在固定UI区域匹配
    avg_y_pos = np.mean(src_pts[valid_matches, 1])
    if avg_y_pos < h * 0.3:
        lower_matches = np.where((src_pts[:, 1] > h * 0.3) & 
                                 (np.abs(y_diffs - best_offset) < 30))[0]
        if len(lower_matches) < 5:
            raise ValueError("主要匹配点在顶部固定UI区域")
    
    # 6. 最终偏移范围验证
    if abs(offset_y) < h * 0.15:
        raise ValueError(f"重叠区域过小(重叠{overlap_h}px，需>{h*0.15}px)")
    
    # 7. 执行拼接
    if offset_y > 0:
        crop_h = h - offset_y
        img_up_cropped = img_up[:crop_h, :]
        result = np.vstack([img_up_cropped, img_down])
    else:
        offset_y = abs(offset_y)
        crop_h = h - offset_y
        img_down_cropped = img_down[:crop_h, :]
        result = np.vstack([img_down_cropped, img_up])
    
    return result

# 执行单元测试
if __name__ == "__main__":
    import doctest

    img_up = 生成模拟手机截屏(True, "test_up.png")
    img_down = 生成模拟手机截屏(False, "test_down.png")
    # verbose=True 显示详细测试过程，方便调试
    # doctest.testmod(verbose=True)
    img_no_overlap = 生成无重合图片()
    result = 上下截屏图片无缝拼接(img_up, img_down)
    # print(result)
    save_path = str(get_path("merged_img.png"))
    cv2.imwrite(save_path, result)

