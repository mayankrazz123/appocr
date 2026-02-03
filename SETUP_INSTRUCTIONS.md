# Setup Instructions for News App

## Issue Identified
Your system is running **Python 3.14.0a3 (alpha)** which has compatibility issues with pydantic-core DLL.

## Solution: Use Python 3.11 or 3.12

### Step 1: Install Python 3.11 or 3.12
Download and install from: https://www.python.org/downloads/

### Step 2: Create Virtual Environment with Correct Python Version
```powershell
# Remove existing venv
Remove-Item -Recurse -Force venv

# Create new venv with Python 3.11/3.12
py -3.11 -m venv venv
# OR
py -3.12 -m venv venv
```

### Step 3: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies (One by One)
```powershell
# Core dependencies
pip install fastapi==0.109.0
pip install uvicorn[standard]==0.27.0
pip install pydantic==2.6.0

# Database
pip install PyMySQL==1.1.0
pip install mysql-connector-python==8.3.0

# File handling
pip install python-multipart==0.0.6
pip install python-dateutil==2.8.2

# Image processing
pip install Pillow==10.2.0
pip install opencv-python==4.9.0.80
pip install pytesseract==0.3.10

# ML/NLP
pip install numpy==1.26.3
pip install scikit-learn==1.4.0
pip install scipy==1.12.0
pip install pandas==2.2.0

# Transformers (optional - for NER)
pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu
pip install transformers==4.37.2

# ONNX (if needed)
pip install onnx==1.16.0
pip install onnxruntime==1.19.2

# Other utilities
pip install requests==2.31.0
```

### Step 5: Update Database Connection
Edit `app/news_app.py` line 39-44:
```python
connection = pymysql.connect(
    host='localhost',          # Your MySQL host
    user='root',               # Your MySQL username
    password='your_password',  # Your MySQL password
    database='cctns_state_db',
    cursorclass=pymysql.cursors.DictCursor
)
```

### Step 6: Run the Server
```powershell
# Method 1: Using uvicorn
uvicorn app.news_app:app --host 0.0.0.0 --port 5000 --reload

# Method 2: Using python directly
python app\news_app.py
```

### Step 7: Access the Application
- API: http://localhost:5000
- Docs: http://localhost:5000/docs
- Health Check: http://localhost:5000/health

## Quick Fix (If you must use Python 3.14)
Try installing from source:
```powershell
pip install --no-binary pydantic-core pydantic-core
pip install pydantic
```

## Tesseract OCR Setup
Make sure Tesseract is installed and in PATH:
```powershell
# Check if installed
tesseract --version

# If not, download from:
# https://github.com/UB-Mannheim/tesseract/wiki
# Install with Hindi language pack
```

## Common Endpoints
- `GET /health` - Health check
- `GET /fir-records` - Get FIR records
- `GET /getnews` - Get news articles
- `POST /uploadnews` - Upload news image
- `POST /savesummary` - Save incident summary
- `POST /extract-articles` - Extract articles from image
- `GET /generate-report` - Generate final report

