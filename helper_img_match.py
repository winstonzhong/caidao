import cv2

from tool_img import to_gray


def get_match_similarity_ratio(img1, img2):
    img1 = to_gray(img1)
    img2 = to_gray(img2)

    orb = cv2.ORB_create()
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(img2, None)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(des1, des2)
    similarity_ratio = len(matches) / max(len(kp1), len(kp2))
    return similarity_ratio

