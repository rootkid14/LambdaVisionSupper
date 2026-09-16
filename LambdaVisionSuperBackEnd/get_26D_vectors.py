import cv2
import numpy as np
from pathlib import Path

# ========================= CONFIG =========================
IMAGE_PATH = "/home/hieu/Downloads/lambda_vision_robot_v2/download (40).jpg"
OUTPUT_PATH = "/home/hieu/Downloads/lambda_vision_robot_v2/product_features.npz"
STRIDE = 4
# ==========================================================

FEATURE_NAMES = [
    "L","a","b","Gx","Gy","Gmag",
    "L_mean_5","L_std_5","a_mean_5","a_std_5","b_mean_5","b_std_5",
    "L_mean_15","L_std_15","a_mean_15","a_std_15","b_mean_15","b_std_15",
    "L_mean_31","L_std_31","a_mean_31","a_std_31","b_mean_31","b_std_31",
    "x_norm","y_norm"
]

def local_mean_std(x, k):
    mean = cv2.boxFilter(x, cv2.CV_32F, (k, k), borderType=cv2.BORDER_REFLECT101)
    mean_sq = cv2.boxFilter(x*x, cv2.CV_32F, (k, k), borderType=cv2.BORDER_REFLECT101)
    std = np.sqrt(np.maximum(mean_sq - mean*mean, 0.0))
    return mean, std

def extract_lab26(image_bgr, stride=4):
    if image_bgr is None or image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError("Expected BGR image [H,W,3]")
    if stride < 1:
        raise ValueError("stride must be >= 1")

    img = image_bgr.astype(np.float32) / 255.0
    L, a, b = cv2.split(cv2.cvtColor(img, cv2.COLOR_BGR2LAB))

    Gx = cv2.Sobel(L, cv2.CV_32F, 1, 0, ksize=3)
    Gy = cv2.Sobel(L, cv2.CV_32F, 0, 1, ksize=3)
    Gmag = cv2.magnitude(Gx, Gy)

    maps = [L, a, b, Gx, Gy, Gmag]
    for k in (5, 15, 31):
        for ch in (L, a, b):
            mean, std = local_mean_std(ch, k)
            maps.extend([mean, std])

    h, w = L.shape
    ys = np.arange(0, h, stride, dtype=np.int32)
    xs = np.arange(0, w, stride, dtype=np.int32)
    xn, yn = np.meshgrid(
        xs.astype(np.float32) / max(w-1, 1),
        ys.astype(np.float32) / max(h-1, 1)
    )

    sampled = [m[::stride, ::stride] for m in maps]
    features = np.stack(sampled + [xn, yn], axis=-1).astype(np.float32)
    return features, xs, ys

def save_features(path, features, xs, ys, stride, image_shape):
    np.savez(
        path,
        features=features,
        xs=xs,
        ys=ys,
        feature_names=np.array(FEATURE_NAMES),
        stride=np.int32(stride),
        image_shape=np.array(image_shape, dtype=np.int32)
    )

def save_features_csv(path, features, xs, ys):
    h, w, d = features.shape
    xx, yy = np.meshgrid(xs, ys)
    rows = np.column_stack([
        xx.reshape(-1),
        yy.reshape(-1),
        features.reshape(-1, d)
    ])

    header = ["x", "y"] + FEATURE_NAMES
    np.savetxt(
        path,
        rows,
        delimiter=",",
        header=",".join(header),
        comments="",
        fmt="%.6f"
    )

def main():
    image = cv2.imread(IMAGE_PATH)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {IMAGE_PATH}")

    features, xs, ys = extract_lab26(image, STRIDE)
    save_features_csv(OUTPUT_PATH, features, xs, ys)

    print(f"Input         : {Path(IMAGE_PATH).resolve()}")
    print(f"Image shape   : {image.shape}")
    print(f"Stride        : {STRIDE}")
    print(f"Feature shape : {features.shape}")
    print(f"Feature dtype : {features.dtype}")
    print(f"Output        : {Path(OUTPUT_PATH).resolve()}")

if __name__ == "__main__":
    main()