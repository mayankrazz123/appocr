import pytesseract
import cv2
import numpy as np
import base64
import tempfile
import re
import io
from PIL import Image

# ---------------- TESSERACT SETUP ---------------- #
try:
    pytesseract.get_tesseract_version()
except:
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ---------------- TEXT CLEANER ---------------- #
def clean_text(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------- DESKEW IMAGE ---------------- #
def deskew_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)

    thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
    )[1]

    coords = np.column_stack(np.where(thresh > 0))
    if coords.size == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)

    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )


# ---------------- MAIN OCR (HINDI + ENGLISH) ---------------- #
def extract_text_from_image(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    # Fix rotation
    image = deskew_image(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Scale up (VERY important for Hindi)
    scale = 2.5
    gray = cv2.resize(
        gray,
        (int(gray.shape[1] * scale), int(gray.shape[0] * scale)),
        interpolation=cv2.INTER_CUBIC
    )

    # Noise reduction
    denoised = cv2.fastNlMeansDenoising(gray, None, 15, 7, 21)

    # Contrast boost
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Adaptive threshold (best for newspapers)
    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 11
    )

    # Morphology (safe for Hindi + English)
    kernel = np.ones((2, 2), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

    # Try multiple page segmentation modes
    results = []
    for psm in [1, 3, 4, 6]:
        config = f'--oem 3 --psm {psm}'
        text = pytesseract.image_to_string(
            binary,
            config=config,
            lang='hin+eng'   # 🔥 THIS IS THE KEY
        )
        results.append(clean_text(text))

    # Pick best result
    best_text = max(results, key=lambda t: (len(t), t.count("\n")))
    return best_text


# ---------------- FALLBACK OCR ---------------- #
def extract_text_alternative(image_path: str) -> str:
    image = cv2.imread(image_path)
    if image is None:
        return ""

    image = deskew_image(image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    gray = cv2.resize(
        gray,
        (gray.shape[1] * 2, gray.shape[0] * 2),
        interpolation=cv2.INTER_CUBIC
    )

    _, binary = cv2.threshold(
        gray, 0, 255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    return clean_text(
        pytesseract.image_to_string(
            binary,
            config='--oem 3 --psm 3',
            lang='hin+eng'
        )
    )


# ---------------- BASE64 PROCESSOR ---------------- #
def process_base64_images(base64_image: str):
    articles = []

    try:
        image = Image.open(
            io.BytesIO(base64.b64decode(base64_image))
        ).convert("RGB")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            image.save(tmp.name, "JPEG", quality=95)

            text1 = extract_text_from_image(tmp.name)
            text2 = extract_text_alternative(tmp.name)

            final_text = text2 if len(text2) > len(text1) else text1
            articles.append(final_text)

    except Exception as e:
        print("[OCR ERROR]", e)

    return articles
