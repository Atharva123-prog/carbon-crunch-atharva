import cv2
import numpy as np
from PIL import Image

def load_image(image_input):
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
        if img is None:
            pil_img = Image.open(image_input)
            img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        return img
    elif isinstance(image_input, np.ndarray):
        return image_input.copy()
    else:
        raise ValueError("Invalid image input type")

def estimate_blur(gray_image):
    if len(gray_image.shape) == 3:
        gray_image = cv2.cvtColor(gray_image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray_image, cv2.CV_64F).var())

def detect_skew(image):
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
    if lines is None:
        return 0.0
    angles = []
    for line in lines[:150]:
        line_data = line[0] if len(line) == 1 else line
        if len(line_data) >= 4:
            x1, y1, x2, y2 = line_data[0], line_data[1], line_data[2], line_data[3]
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            if -45.0 < angle < 45.0:
                angles.append(angle)
    if len(angles) == 0:
        return 0.0
    median_angle = float(np.median(angles))
    return median_angle

def deskew_image(image, angle):
    if abs(angle) < 0.3:
        return image.copy()
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def denoise_image(image):
    return cv2.GaussianBlur(image, (3, 3), 0)

def enhance_contrast(image):
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    return enhanced

def binarize_image(gray_image):
    adaptive = cv2.adaptiveThreshold(
        gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )
    return adaptive

def preprocess_image(image_input):
    img = load_image(image_input)
    h, w = img.shape[:2]
    max_dim = 700
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    blur_score = estimate_blur(img)
    skew_angle = detect_skew(img)
    deskewed = deskew_image(img, skew_angle)
    denoised = denoise_image(deskewed)
    gray = enhance_contrast(denoised)
    binary = binarize_image(gray)
    color_prep = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    return {
        "original": img,
        "deskewed": deskewed,
        "preprocessed": color_prep,
        "gray": gray,
        "binary": binary,
        "blur_score": blur_score,
        "skew_angle": skew_angle
    }
