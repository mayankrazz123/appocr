import pytesseract
from PIL import Image
import cv2
import numpy as np
import base64
import tempfile
import re
from PIL import Image
import io

# Tesseract Configuration
# For Windows, update this path to your Tesseract installation
# Common paths: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# For Linux/Docker: "/usr/bin/tesseract"
try:
    # Try to use tesseract from PATH first
    pytesseract.get_tesseract_version()
except:
    # If not in PATH, set the path manually
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

#"custom_config = '--oem 3  --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ'



# Clean extracted text
def clean_text(text):
    #text = re.sub(r'[^ऀ-ॿa-zA-Z0-9\s।,!?%():\-–—"“”‘’\'\n]', '', text)
    #text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Extract text from saved image file with advanced preprocessing
def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image from path: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Get original dimensions
    height, width = gray.shape

    # Resize image for better OCR (scale up if too small)
    # Tesseract works best with text height around 30-40 pixels
    scale_factor = 2.0  # Increase resolution
    new_width = int(width * scale_factor)
    new_height = int(height * scale_factor)
    resized = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

    # Apply bilateral filter to reduce noise while keeping edges sharp
    filtered = cv2.bilateralFilter(resized, 9, 75, 75)

    # Increase contrast using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(filtered)

    # Apply sharpening kernel
    kernel_sharpening = np.array([[-1, -1, -1],
                                   [-1,  9, -1],
                                   [-1, -1, -1]])
    sharpened = cv2.filter2D(enhanced, -1, kernel_sharpening)

    # Apply Otsu's thresholding for better binarization
    # This automatically finds the optimal threshold value
    _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Morphological operations to clean up the image
    # Remove small noise
    kernel = np.ones((1, 1), np.uint8)
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

    print(pytesseract.get_languages(config=''))

    # Try multiple PSM modes and combine results
    # PSM 1 = Automatic page segmentation with OSD (Orientation and Script Detection)
    # PSM 3 = Fully automatic page segmentation (default) - best for multi-column newspaper
    # PSM 4 = Assume a single column of text of variable sizes
    # PSM 6 = Assume a single uniform block of text

    # Use PSM 1 for better handling of complex layouts like newspapers
    config = r'--oem 3 --psm 1'

    text = pytesseract.image_to_string(cleaned, config=config, lang='hin')
    print(text)
    return clean_text(text)

# Alternative extraction method with different preprocessing
def extract_text_alternative(image_path):
    """Alternative method using simpler preprocessing"""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image from path: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Scale up
    scale = 2.5
    width = int(gray.shape[1] * scale)
    height = int(gray.shape[0] * scale)
    resized = cv2.resize(gray, (width, height), interpolation=cv2.INTER_CUBIC)

    # Simple denoising
    denoised = cv2.fastNlMeansDenoising(resized, None, 10, 7, 21)

    # Adaptive thresholding
    binary = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 11, 2)

    # Try PSM 3 (automatic page segmentation)
    text = pytesseract.image_to_string(binary, config=r'--oem 3 --psm 3', lang='hin')
    return clean_text(text)


# Main processor for base64 images
def process_base64_images(base64_image: str):
    articles = []

    print('process_base64_images')
    try:
        # PIL handles PNGs more reliably than OpenCV
        image = Image.open(io.BytesIO(base64.decodebytes(bytes(base64_image, "utf-8")))).convert("RGB")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
            image.save(tmpfile.name, format="JPEG", quality=95)  # High quality JPEG for OCR

            # Try primary method
            print("Trying primary OCR method...")
            text1 = extract_text_from_image(tmpfile.name)

            # Try alternative method
            print("Trying alternative OCR method...")
            text2 = extract_text_alternative(tmpfile.name)

            # Choose the longer result (usually more complete)
            if len(text2) > len(text1):
                print(f"Using alternative method (length: {len(text2)} vs {len(text1)})")
                text = text2
            else:
                print(f"Using primary method (length: {len(text1)} vs {len(text2)})")
                text = text1

            # Preserve newlines for better text structure
            articles.append(text)

    except Exception as e:
        print(f"[ERROR] Failed processing image: {e}")
        import traceback
        traceback.print_exc()

    return articles
