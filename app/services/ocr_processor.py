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

# Extract text from saved image file
def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image from path: {image_path}")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    print(pytesseract.get_languages(config=''))
    
    #r'--oem 3 --psm 12
    text = pytesseract.image_to_string(gray, config="r'--oem 3 --psm 12'", 
    lang='hin')
    print(text)
    return clean_text(text)

# Main processor for base64 images


def process_base64_images(base64_image: str):
    articles = []
    
    print('process_base64_images');
    try:
            #image_data = base64.b64decode(base64_str)
        #bytes_representation = base64_image.encode(encoding="utf-8") 

            # PIL handles PNGs more reliably than OpenCV
        image = Image.open(io.BytesIO(base64.decodebytes(bytes(base64_image, "utf-8")))).convert("RGB")

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmpfile:
            image.save(tmpfile.name, format="JPEG")  # convert to jpg for OCR
            text = extract_text_from_image(tmpfile.name)
            #if len(text.strip()) > 30:
                #articles.append(text.strip())
            articles.append(text.replace('\n', ' '))
        
     
        
    except Exception as e:
            print(f"[ERROR] Failed processing image  : {e}")
            

    return articles
