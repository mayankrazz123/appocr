# Debugging News Extraction - Why "N/A" Values Are Returned

## Problem
The `/extract-local-newspaper` endpoint is returning "N/A" for all extracted fields:
- districtCode: "N/A"
- districtName: "N/A"
- policeStation: "N/A"
- accusedName: "N/A"
- complainantName: "N/A"

## Root Causes

### 1. **OCR Text Quality Issue**
The most likely cause is that the OCR (Optical Character Recognition) is not extracting clear Hindi text from the newspaper image. This could be due to:
- Poor image quality
- Incorrect Tesseract configuration
- Missing Hindi language data for Tesseract
- Image preprocessing issues

### 2. **Regex Pattern Mismatch**
Even if OCR extracts text, the regex patterns in the extraction functions might not match the actual format of the text in the newspaper.

### 3. **Bug Fixed: `extract_accused` Function**
There was a bug where `extract_accused(text)` was trying to access `text[0]` when `text` was already a string, not a list. This has been fixed.

## Changes Made

### 1. Fixed `extract_accused` Function
**Before:**
```python
def extract_accused(text):
    for pattern in patterns:
        match = re.search(pattern, text[0])  # BUG: text is a string, not a list
```

**After:**
```python
def extract_accused(text):
    # Handle both string and list inputs
    text_str = text[0] if isinstance(text, list) else text
    
    for pattern in patterns:
        match = re.search(pattern, text_str)  # FIXED
```

### 2. Added Debug Logging
The endpoint now prints:
- The full extracted OCR text
- Each extracted field value
- Any errors that occur

### 3. Added Error Handling
The endpoint now returns a clear error message if OCR fails to extract text.

## How to Test and Debug

### Step 1: Run the Server
```powershell
cd C:\Users\mayan\Downloads\app
py -3.13 -m uvicorn app.news_app:app --host 0.0.0.0 --port 5000 --reload
```

### Step 2: Call the Endpoint
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/extract-local-newspaper" | Select-Object -ExpandProperty Content
```

### Step 3: Check the Console Output
Look at the server console for debug output:
```
================================================================================
EXTRACTED TEXT FROM OCR:
[The actual Hindi text extracted from the image will appear here]
================================================================================
Crime Type: [extracted value or N/A]
Police Station: [extracted value or N/A]
Accused Name: [extracted value or N/A]
Complainant Name: [extracted value or N/A]
District Name: [extracted value or N/A]
```

## Troubleshooting

### If OCR Returns Empty Text
1. **Check if Tesseract is installed:**
   ```powershell
   tesseract --version
   ```

2. **Check if Hindi language data is installed:**
   ```powershell
   tesseract --list-langs
   ```
   You should see `hin` in the list.

3. **Install Hindi language data if missing:**
   - Download from: https://github.com/tesseract-ocr/tessdata
   - Copy `hin.traineddata` to Tesseract's tessdata folder

### If OCR Returns Text But Extraction Fails
1. **Check the extracted text format** - Look at the console output to see what text was actually extracted
2. **Update regex patterns** - The patterns in `extract_accused`, `extract_complainant`, `extract_district`, etc. might need to be adjusted to match your newspaper format
3. **Check the newspaper content** - Make sure the newspaper image actually contains the expected Hindi keywords

### Example: If the newspaper uses different keywords
If your newspaper uses "अभियुक्त" instead of "आरोपी", you need to add that pattern to the extraction function.

## Next Steps

1. **Run the endpoint and check console output** to see what text is being extracted
2. **Share the console output** so we can see what's happening
3. **Check the newspaper.jpg file** to ensure it contains readable Hindi text
4. **Adjust regex patterns** based on the actual text format in your newspaper

## Testing with Sample Text

You can test the extraction functions directly with sample text:
```python
sample_text = "थाना कोतवाली में आरोपी राम कुमार को गिरफ्तार किया गया। प्रार्थी श्याम सिंह ने शिकायत दर्ज कराई।"

print(extract_police_station(sample_text))  # Should extract "कोतवाली"
print(extract_accused(sample_text))         # Should extract "राम कुमार"
print(extract_complainant(sample_text))     # Should extract "श्याम सिंह"
```

