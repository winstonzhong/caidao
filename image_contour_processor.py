"""
图像轮廓处理器

该类整合了图像边缘检测、轮廓提取和矩形分组功能。

设计考虑:
1. 边缘检测方法选择:
   - Otsu二值化: 适用于背景与前景对比明显的图像，自动计算阈值
   - Canny边缘检测: 适用于需要检测精细边缘的场景，对噪声更敏感

2. 轮廓检索模式选择:
   - RETR_EXTERNAL: 只检索最外层轮廓，忽略内部孔洞，适用于需要检测独立物体的场景
   - RETR_LIST: 检索所有轮廓，不建立层次关系，适用于需要获取所有轮廓的场景
"""

import cv2
import numpy
import os
import pandas as pd


class ImageContourProcessor:
    """
    图像轮廓处理器

    用于从图像中提取轮廓并进行分组处理。

    示例:
        processor = ImageContourProcessor(image)
        rects = processor.get_rect_by_group(gap=10, max_width=200, max_height=200)
    """

    def __init__(self, img):
        """
        初始化处理器

        Args:
            img: 输入图像 (numpy.ndarray), BGR格式
        """
        self.img = img
        self._mask = None
        self._contour_array = None

    def _to_gray(self, img):
        """将图像转换为灰度图"""
        if len(img.shape) == 2:
            return img
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    def _create_mask_by_otsu(self, invert=True):
        """
        使用Otsu自动二值化创建掩码

        优点:
            - 自动计算最佳阈值，无需手动调整
            - 对光照变化有较好的适应性
            - 计算速度快

        适用场景:
            - 前景与背景对比明显的图像
            - 需要快速获取二值化结果

        Args:
            invert: 是否反转二值化结果 (默认True，使前景为白色)

        Returns:
            二值化掩码图像
        """
        gray = self._to_gray(self.img)

        if invert:
            _, binary = cv2.threshold(
                gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )
        else:
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary

    def _create_mask_by_canny(self, low=80, high=200):
        """
        使用Canny边缘检测创建掩码

        优点:
            - 能检测精细的边缘
            - 使用双阈值进行边缘连接，减少噪声干扰

        缺点:
            - 对参数敏感，需要根据图像调整low/high
            - 可能产生断裂的边缘

        适用场景:
            - 需要精确边缘定位的场景
            - 物体边界清晰的图像

        Args:
            low: 低阈值
            high: 高阈值

        Returns:
            边缘掩码图像
        """
        gray = self._to_gray(self.img)
        img_blur = cv2.GaussianBlur(gray, (3, 3), 0)
        edges = cv2.Canny(img_blur, low, high)

        return edges

    def _create_mask(self, method="otsu", **kwargs):
        """
        创建掩码的内部方法

        Args:
            method: 方法选择 ('otsu' 或 'canny')
            **kwargs: 传递给具体方法的参数

        Returns:
            掩码图像
        """
        if method == "otsu":
            return self._create_mask_by_otsu(**kwargs)
        elif method == "canny":
            return self._create_mask_by_canny(**kwargs)
        else:
            raise ValueError(f"Unknown method: {method}. Use 'otsu' or 'canny'")

    def get_contour_array(self, method="otsu", mode="list", **mask_kwargs):
        """
        获取轮廓数组

        自动创建掩码（如果尚未创建），并根据指定方法提取轮廓

        方法选择建议:
            - 'otsu': 适用于大多数场景，自动计算阈值
            - 'canny': 适用于需要精确边缘的场景

        模式选择建议:
            - 'external': 只获取最外层轮廓，适合检测独立物体
            - 'list': 获取所有轮廓，适合需要完整信息的场景

        Args:
            method: 掩码创建方法 ('otsu' 或 'canny')
            mode: 轮廓检索模式 ('external' 或 'list')
            **mask_kwargs: 传递给掩码创建方法的参数

        Returns:
            轮廓数组，每行格式为 [x, y, width, height]
        """
        # 自动创建掩码
        self._mask = self._create_mask(method=method, **mask_kwargs)

        # 根据模式选择检索方式
        if mode == "external":
            retrieval_mode = cv2.RETR_EXTERNAL
        elif mode == "list":
            retrieval_mode = cv2.RETR_LIST
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'external' or 'list'")

        contours, _ = cv2.findContours(
            self._mask,
            retrieval_mode,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        if not contours:
            return numpy.array([])

        result = numpy.stack([cv2.boundingRect(x) for x in contours])
        self._contour_array = result
        return result

    def get_filtered_contours(
        self,
        method="otsu",
        mode="external",
        max_width=10000,
        max_height=10000,
        min_len=5,
        **mask_kwargs,
    ):
        """
        获取过滤后的轮廓数组（快捷函数）

        整合 get_contour_array 和 filter_contour_array 两个步骤

        Args:
            method: 掩码创建方法 ('otsu' 或 'canny')
            mode: 轮廓检索模式 ('external' 或 'list')
            max_width: 最大宽度过滤
            max_height: 最大高度过滤
            min_len: 最小边长过滤
            **mask_kwargs: 传递给掩码创建方法的参数

        Returns:
            过滤后的轮廓数组，每行格式为 [x, y, width, height]
        """
        contours = self.get_contour_array(method=method, mode=mode, **mask_kwargs)
        return self.filter_contour_array(contours, max_width, max_height, min_len)

    def get_otsu_external_contours(
        self, max_width=10000, max_height=10000, min_len=5, invert=True
    ):
        """
        获取 Otsu + EXTERNAL 过滤后的轮廓（快捷函数）

        Args:
            max_width: 最大宽度过滤
            max_height: 最大高度过滤
            min_len: 最小边长过滤
            invert: Otsu二值化是否反转

        Returns:
            过滤后的轮廓数组，每行格式为 [x, y, width, height]
        """
        return self.get_filtered_contours(
            method="otsu",
            mode="external",
            max_width=max_width,
            max_height=max_height,
            min_len=min_len,
            invert=invert,
        )

    def get_canny_list_contours(
        self, max_width=10000, max_height=10000, min_len=5, low=80, high=200
    ):
        """
        获取 Canny + LIST 过滤后的轮廓（快捷函数）

        Args:
            max_width: 最大宽度过滤
            max_height: 最大高度过滤
            min_len: 最小边长过滤
            low: Canny低阈值
            high: Canny高阈值

        Returns:
            过滤后的轮廓数组，每行格式为 [x, y, width, height]
        """
        return self.get_filtered_contours(
            method="canny",
            mode="list",
            max_width=max_width,
            max_height=max_height,
            min_len=min_len,
            low=low,
            high=high,
        )

    def filter_contour_array(self, a, max_width, max_height, min_len=10):
        """
        根据尺寸过滤轮廓数组

        Args:
            a: 轮廓数组
            max_width: 最大宽度
            max_height: 最大高度
            min_len: 最小边长

        Returns:
            过滤后的轮廓数组
        """
        return a[
            (a[:, 2] < max_width)
            & (a[:, 3] < max_height)
            & (a[:, 2] >= min_len)
            & (a[:, 3] > min_len)
        ]

    def get_default_config_by_width_height(self, width, height):
        """
        根据宽高获取默认配置

        Args:
            width: 参考宽度
            height: 参考高度

        Returns:
            配置字典
        """
        return {
            "max_width": width * 1.1,
            "max_height": height * 1.1,
            "min_len": min(width, height) / 8,
        }

    def get_default_config_by_rect(self, rect):
        """
        根据Rect对象获取默认配置

        Args:
            rect: Rect对象，需要有width和height属性

        Returns:
            配置字典
        """
        return self.get_default_config_by_width_height(rect.width, rect.height)

    def filter_contour_array_by_rect(self, a, rect):
        """根据Rect对象过滤轮廓数组"""
        config = self.get_default_config_by_rect(rect)
        return self.filter_contour_array(a, **config)

    def filter_contour_array_by_wh(self, a, width, height):
        """根据宽高过滤轮廓数组"""
        config = self.get_default_config_by_width_height(width, height)
        return self.filter_contour_array(a, **config)

    def compute_group_distance(self, a, gap):
        """
        计算轮廓分组距离

        将轮廓分为两组：与最大轮廓距离小于gap的轮廓，和距离大于等于gap的轮廓

        Args:
            a: 轮廓数组
            gap: 距离阈值

        Returns:
            (close_group, far_group): 近距离组和远距离组
        """
        half = a[..., 2:] // 2
        center = a[..., 0:2] + half
        f = numpy.product if hasattr(numpy, "product") else numpy.prod
        i = f(half, axis=1).argmax()
        delta = numpy.abs(center - center[i]) - half - half[i]
        return a[numpy.all(delta < gap, axis=1)], a[numpy.any(delta >= gap, axis=1)]

    def get_bounding_rect(self, a):
        """
        获取轮廓数组的包围矩形

        Args:
            a: 轮廓数组

        Returns:
            包围矩形 (x, y, width, height)
        """
        return cv2.boundingRect(
            numpy.concatenate((a[..., :2], a[..., :2] + a[..., 2:]))
        )

    def get_rect_by_group(self, a, gap, max_width, max_height):
        """
        按组获取矩形

        将相近的轮廓分组，返回每组的包围矩形

        Args:
            a: 轮廓数组，可通过get_contour_array获得
            gap: 分组间距阈值
            max_width: 最大宽度限制
            max_height: 最大高度限制

        Yields:
            每组的包围矩形 (x, y, width, height)
        """
        while 0 not in a.shape:
            b, a = self.compute_group_distance(a, gap)
            bounds = self.get_bounding_rect(b)

            if bounds[2] > max_width + gap or bounds[3] > max_height + gap:
                continue

            if len(b) > 1:
                a = numpy.concatenate((numpy.array(bounds).reshape(1, -1), a))
            else:
                yield self.get_bounding_rect(b)

    def get_bounding_array_by_group(self, a, gap, max_width, max_height):
        """
        获取分组后的包围矩形数组

        Args:
            a: 轮廓数组
            gap: 分组间距阈值
            max_width: 最大宽度限制
            max_height: 最大高度限制

        Returns:
            包围矩形数组，每行格式为 [x, y, width, height]
        """
        return numpy.stack(list(self.get_rect_by_group(a, gap, max_width, max_height)))

    def get_bounding_dict_list_by_group(self, a, gap, x, y, max_width, max_height):
        """
        获取分组后的包围矩形字典列表

        Args:
            a: 轮廓数组
            gap: 分组间距阈值
            x: 参考点x坐标
            y: 参考点y坐标
            max_width: 最大宽度限制
            max_height: 最大高度限制

        Returns:
            包含边界框、距离、宽高和中心点的字典列表
        """
        a = self.get_bounding_array_by_group(a, gap, max_width, max_height)
        center = a[..., 0:2] + a[..., 2:] // 2
        distance = numpy.linalg.norm(center - (x, y), axis=1)

        return [
            {
                "bounds": (
                    a[i][0],
                    a[i][0] + a[i][2],
                    a[i][1],
                    a[i][1] + a[i][3],
                ),  # left, right, top, bottom
                "distance": distance[i],
                "w": a[i][2],
                "h": a[i][3],
                "center": center[i].tolist(),
            }
            for i in range(a.shape[0])
        ]


    def get_bounding_df_by_group(self, a, gap, x, y, task_id, max_width, max_height):
        data_list = self.get_bounding_dict_list_by_group(a, gap, x, y, max_width, max_height)
        for d in data_list:
            b = d.pop('bounds')
            d['img'] = f'''<img src="/admin/tasks/task/img_rect_view/?id={task_id}&bounds={b}" />
            '''.replace("\n", "")
            d['mask'] = f'''<img src="/admin/tasks/task/img_rect_view/?id={task_id}&bounds={b}&mask=1" />
            '''.replace("\n", "")
            d['action'] = f'''
            <input type="button" value="保存"
                onclick="location.replace('/admin/tasks/task/save_img_tpl/?id={task_id}&bounds={b}&mask=1');"
            />
            '''.replace("\n", "")
        df = pd.DataFrame(data_list)
        df = df.sort_values(by='distance').reset_index(drop=True)
        return df

    def _draw_rects_on_image(self, img, rects, color=(0, 255, 0), thickness=2):
        """
        在图像上绘制矩形

        Args:
            img: 输入图像
            rects: 矩形数组，每行格式为 [x, y, width, height]
            color: 矩形颜色 (B, G, R)
            thickness: 线宽

        Returns:
            绘制后的图像
        """
        result = img.copy()
        if len(rects) == 0:
            return result

        for rect in rects:
            x, y, w, h = rect
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
        return result

    def _add_label_to_image(self, img, label, color, count):
        """
        在图像上添加标签和轮廓数量

        Args:
            img: 输入图像
            label: 标签文本
            color: 文本颜色
            count: 轮廓数量

        Returns:
            添加标签后的图像
        """
        result = img.copy()
        h, w = result.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(w, h) / 800
        font_thickness = max(1, int(min(w, h) / 300))

        # 标签背景
        label_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]
        cv2.rectangle(
            result, (5, 5), (label_size[0] + 15, label_size[1] + 15), (0, 0, 0), -1
        )
        cv2.putText(
            result,
            label,
            (10, label_size[1] + 10),
            font,
            font_scale,
            color,
            font_thickness,
        )

        # 显示轮廓数量
        count_text = f"Count: {count}"
        count_size = cv2.getTextSize(count_text, font, font_scale, font_thickness)[0]
        cv2.rectangle(
            result,
            (5, label_size[1] + 20),
            (count_size[0] + 15, label_size[1] + count_size[1] + 30),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            result,
            count_text,
            (10, label_size[1] + count_size[1] + 25),
            font,
            font_scale,
            color,
            font_thickness,
        )

        return result

    def show_contours_rects(
        self,
        mode="otsu_external",
        max_width=10000,
        max_height=10000,
        min_len=5,
        color=None,
        thickness=2,
        title=None,
        save_path=None,
        display=True,
        **method_kwargs,
    ):
        """
        显示轮廓矩形图

        在原图上绘制通过get_contour_array得到的所有rect(矩形)
        支持两种模式选择:
            - 'otsu_external': Otsu + EXTERNAL (默认绿色)
            - 'canny_list': Canny + LIST (默认红色)

        注意: 如果在多线程环境或Jupyter Notebook中遇到Qt线程错误，
              可以设置 display=False 并指定 save_path 保存图像

        Args:
            mode: 模式选择 ('otsu_external' 或 'canny_list')
            max_width: 过滤最大宽度
            max_height: 过滤最大高度
            min_len: 过滤最小边长
            color: 矩形颜色，None则使用默认颜色
            thickness: 矩形线宽
            title: 窗口标题，None则自动生成
            save_path: 保存路径，如果指定则保存图像
            display: 是否显示图像（设置为False可避免Qt线程错误）
            **method_kwargs: 传递给具体方法的参数 (如invert, low, high等)

        Returns:
            绘制后的图像
        """
        # 根据模式获取轮廓和默认颜色
        if mode == "otsu_external":
            contours = self.get_otsu_external_contours(
                max_width=max_width,
                max_height=max_height,
                min_len=min_len,
                **method_kwargs,
            )
            default_color = (0, 255, 0)  # 绿色
            label = "Otsu + EXTERNAL"
        elif mode == "canny_list":
            contours = self.get_canny_list_contours(
                max_width=max_width,
                max_height=max_height,
                min_len=min_len,
                **method_kwargs,
            )
            default_color = (0, 0, 255)  # 红色
            label = "Canny + LIST"
        else:
            raise ValueError(
                f"Unknown mode: {mode}. Use 'otsu_external' or 'canny_list'"
            )

        # 使用指定颜色或默认颜色
        rect_color = color if color is not None else default_color

        # 在图像上绘制矩形
        result = self._draw_rects_on_image(
            self.img, contours, color=rect_color, thickness=thickness
        )

        # 添加标签
        result = self._add_label_to_image(result, label, rect_color, len(contours))

        # 保存图像（如果指定了路径）
        if save_path:
            cv2.imwrite(save_path, result)
            print(f"Image saved to: {save_path}")

        # 显示图像
        if display:
            try:
                # 尝试使用非Qt后端
                cv2.imshow(title or f"Contours - {label}", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
            except Exception as e:
                print(f"Warning: Could not display image: {e}")
                print(
                    "Tip: Set display=False and use save_path to save the image instead."
                )

        return result

    def get_contours_rects_image(
        self,
        mode="otsu_external",
        max_width=10000,
        max_height=10000,
        min_len=5,
        color=None,
        thickness=2,
        **method_kwargs,
    ):
        """
        获取轮廓矩形图（不显示，仅返回图像）

        与show_contours_rects功能相同，但不显示窗口，仅返回图像和轮廓信息

        Args:
            mode: 模式选择 ('otsu_external' 或 'canny_list')
            max_width: 过滤最大宽度
            max_height: 过滤最大高度
            min_len: 过滤最小边长
            color: 矩形颜色，None则使用默认颜色
            thickness: 矩形线宽
            **method_kwargs: 传递给具体方法的参数

        Returns:
            绘制后的图像, 以及轮廓信息字典
        """
        # 根据模式获取轮廓和默认颜色
        if mode == "otsu_external":
            contours = self.get_otsu_external_contours(
                max_width=max_width,
                max_height=max_height,
                min_len=min_len,
                **method_kwargs,
            )
            default_color = (0, 255, 0)  # 绿色
            label = "Otsu + EXTERNAL"
        elif mode == "canny_list":
            contours = self.get_canny_list_contours(
                max_width=max_width,
                max_height=max_height,
                min_len=min_len,
                **method_kwargs,
            )
            default_color = (0, 0, 255)  # 红色
            label = "Canny + LIST"
        else:
            raise ValueError(
                f"Unknown mode: {mode}. Use 'otsu_external' or 'canny_list'"
            )

        # 使用指定颜色或默认颜色
        rect_color = color if color is not None else default_color

        # 在图像上绘制矩形
        result = self._draw_rects_on_image(
            self.img, contours, color=rect_color, thickness=thickness
        )

        # 添加标签
        result = self._add_label_to_image(result, label, rect_color, len(contours))

        info = {
            "mode": mode,
            "label": label,
            "contours": contours,
            "count": len(contours),
            "color": rect_color,
        }

        return result, info

    def save_contours_comparison(
        self,
        save_path,
        max_width=10000,
        max_height=10000,
        min_len=5,
        otsu_color=(0, 255, 0),
        canny_color=(0, 0, 255),
        thickness=2,
    ):
        """
        保存两种模式的轮廓对比图

        生成包含两种模式（Otsu+EXTERNAL 和 Canny+LIST）的对比图并保存

        Args:
            save_path: 保存路径
            max_width: 过滤最大宽度
            max_height: 过滤最大高度
            min_len: 过滤最小边长
            otsu_color: Otsu+EXTERNAL矩形的颜色
            canny_color: Canny+LIST矩形的颜色
            thickness: 矩形线宽

        Returns:
            拼接后的对比图像
        """
        # 获取两种模式的图像
        img_otsu, info_otsu = self.get_contours_rects_image(
            mode="otsu_external",
            max_width=max_width,
            max_height=max_height,
            min_len=min_len,
            color=otsu_color,
            thickness=thickness,
        )

        img_canny, info_canny = self.get_contours_rects_image(
            mode="canny_list",
            max_width=max_width,
            max_height=max_height,
            min_len=min_len,
            color=canny_color,
            thickness=thickness,
        )

        # 水平拼接
        combined = numpy.hstack([img_otsu, img_canny])

        # 保存
        cv2.imwrite(save_path, combined)
        print(f"Comparison image saved to: {save_path}")
        print(f"  Otsu+EXTERNAL: {info_otsu['count']} contours")
        print(f"  Canny+LIST: {info_canny['count']} contours")

        return combined

    # 便捷方法：一键处理
    def process(
        self,
        gap,
        max_width,
        max_height,
        method="otsu",
        mode="external",
        filter_config=None,
        x=None,
        y=None,
        task_id=None,
    ):
        """
        一键处理图像，获取分组后的矩形

        Args:
            gap: 分组间距阈值
            max_width: 最大宽度限制
            max_height: 最大高度限制
            method: 掩码创建方法 ('otsu' 或 'canny')
            mode: 轮廓检索模式 ('external' 或 'list')
            filter_config: 过滤配置字典，可选
            x: 参考点x坐标，用于计算距离，可选
            y: 参考点y坐标，用于计算距离，可选

        Returns:
            如果提供了x,y则返回字典列表，否则返回包围矩形数组
        """
        # 获取轮廓
        a = self.get_contour_array(method=method, mode=mode)

        # 过滤轮廓
        if filter_config:
            a = self.filter_contour_array(a, **filter_config)

        # 分组并返回结果
        if x is not None and y is not None and task_id is not None:
            return self.get_bounding_df_by_group(
                # a, gap, x, y, max_width, max_height
                a, gap, x, y, task_id, max_width, max_height
            )
        else:
            return self.get_bounding_array_by_group(a, gap, max_width, max_height)


# 保留原始函数接口以便向后兼容
def get_contour_array(mask):
    """
    从掩码中获取轮廓数组

    使用RETR_LIST模式获取所有轮廓

    Args:
        mask: 二值化掩码图像

    Returns:
        轮廓数组，每行格式为 [x, y, width, height]
    """
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    return numpy.stack([cv2.boundingRect(x) for x in contours])


def filter_contour_array(a, max_width, max_height, min_len=10):
    """根据尺寸过滤轮廓数组"""
    return a[
        (a[:, 2] < max_width)
        & (a[:, 3] < max_height)
        & (a[:, 2] >= min_len)
        & (a[:, 3] > min_len)
    ]


def get_default_config_by_width_height(width, height):
    """根据宽高获取默认配置"""
    return {
        "max_width": width * 1.1,
        "max_height": height * 1.1,
        "min_len": min(width, height) / 8,
    }


def get_default_config_by_rect(rect):
    """根据Rect对象获取默认配置"""
    return get_default_config_by_width_height(rect.width, rect.height)


def filter_contour_array_by_rect(a, rect):
    """根据Rect对象过滤轮廓数组"""
    return filter_contour_array(a, **get_default_config_by_rect(rect))


def filter_contour_array_by_wh(a, width, height):
    """根据宽高过滤轮廓数组"""
    return filter_contour_array(a, **get_default_config_by_width_height(width, height))


def compute_group_distance(a, gap):
    """计算轮廓分组距离"""
    half = a[..., 2:] // 2
    center = a[..., 0:2] + half
    f = numpy.product if hasattr(numpy, "product") else numpy.prod
    i = f(half, axis=1).argmax()
    delta = numpy.abs(center - center[i]) - half - half[i]
    return a[numpy.all(delta < gap, axis=1)], a[numpy.any(delta >= gap, axis=1)]


def get_bounding_rect(a):
    """获取轮廓数组的包围矩形"""
    return cv2.boundingRect(numpy.concatenate((a[..., :2], a[..., :2] + a[..., 2:])))


def get_rect_by_group(a, gap, max_width, max_height):
    """
    按组获取矩形

    Args:
        a: 轮廓数组，可通过get_contour_array获得
        gap: 分组间距阈值
        max_width: 最大宽度限制
        max_height: 最大高度限制

    Yields:
        每组的包围矩形 (x, y, width, height)
    """
    while 0 not in a.shape:
        b, a = compute_group_distance(a, gap)
        bounds = get_bounding_rect(b)

        if bounds[2] > max_width + gap or bounds[3] > max_height + gap:
            continue

        if len(b) > 1:
            a = numpy.concatenate((numpy.array(bounds).reshape(1, -1), a))
        else:
            yield get_bounding_rect(b)


def get_bounding_array_by_group(a, gap, max_width, max_height):
    """获取分组后的包围矩形数组"""
    return numpy.stack(list(get_rect_by_group(a, gap, max_width, max_height)))


def get_bounding_dict_list_by_group(a, gap, x, y, max_width, max_height):
    """获取分组后的包围矩形字典列表"""
    a = get_bounding_array_by_group(a, gap, max_width, max_height)
    center = a[..., 0:2] + a[..., 2:] // 2
    distance = numpy.linalg.norm(center - (x, y), axis=1)

    return [
        {
            "bounds": (a[i][0], a[i][0] + a[i][2], a[i][1], a[i][1] + a[i][3]),
            "distance": distance[i],
            "w": a[i][2],
            "h": a[i][3],
            "center": center[i].tolist(),
        }
        for i in range(a.shape[0])
    ]


def img2edges(img, low=80, high=200):
    """
    使用Canny算法检测图像边缘

    优点:
        - 能检测精细的边缘
        - 使用双阈值进行边缘连接

    缺点:
        - 对参数敏感
        - 可能产生断裂的边缘

    Args:
        img: 输入图像
        low: 低阈值
        high: 高阈值

    Returns:
        边缘图像
    """
    img = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_blur = cv2.GaussianBlur(img, (3, 3), 0)
    edges = cv2.Canny(img_blur, low, high)
    return edges
