import cv2
from tool_img import img2edges
MASK_TYPE_NONE = 0
MASK_TYPE_BGR = 1
MASK_TYPE_HSV = 1


def get_mask_bgr(self):
    return cv2.inRange(self.img, self.lower, self.upper)

def get_mask_hsv(self):
    return cv2.inRange(self.img_hsv, self.lower, self.upper)


def get_mask(img, mask_type, self):
    if mask_type == MASK_TYPE_NONE:
        pass
    elif mask_type == MASK_TYPE_BGR:
        img = self.get_mask_bgr()
    elif mask_type == MASK_TYPE_HSV:
        img = self.get_mask_hsv()
    else:
        raise ValueError
    return img2edges(img, low=70, high=200)


if __name__ == "__main__":
    import doctest
    print(doctest.testmod(verbose=False, report=False))
