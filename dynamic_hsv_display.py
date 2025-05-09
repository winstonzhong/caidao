import cv2
import numpy as np
import matplotlib.pyplot as plt



def show_hsv(fpath):
    # 读取图像
    img = cv2.imread(fpath)
    if img is None:
        print("无法读取图像，请检查图像路径。")
    else:
        # 转换为 RGB 格式
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # 转换为 HSV 格式
        img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 显示图像
        fig, ax = plt.subplots()
        ax.imshow(img_rgb)

        def on_click(event):
            if event.inaxes is not None:
                x, y = int(round(event.xdata, 0)), int(round(event.ydata, 0))
                if 0 <= x < img_rgb.shape[1] and 0 <= y < img_rgb.shape[0]:
                    hsv_pixel = img_hsv[y, x]
                    rgb_pixel = img_rgb[y, x]
                    h, s, v = hsv_pixel[0], hsv_pixel[1], hsv_pixel[2]
                    r, g, b = rgb_pixel[0], rgb_pixel[1], rgb_pixel[2]
                    plt.title(f"""
                              ({x}, {y})
                              HSV: ({h}, {s}, {v})
                              RGB: ({r}, {g}, {b})
                              """.strip().replace(' ','')
                              )
                    plt.draw()

        # 绑定鼠标点击事件
        fig.canvas.mpl_connect('button_press_event', on_click)

        plt.show()