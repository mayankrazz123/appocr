# Testing Newspaper Image Extraction

## ✅ **New Endpoint Created: `/extract-local-newspaper`**

This endpoint processes the local `app/services/newspaper.jpg` file and extracts crime information from it.

---

## 🚀 **How to Test**

### **Step 1: Start the Server**

Open PowerShell and run:

```powershell
cd C:\Users\mayan\Downloads\app
py -3.13 -m uvicorn app.news_app:app --host 0.0.0.0 --port 5000 --reload
```

Wait for the server to start. You should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000
```

---

### **Step 2: Test the Endpoint**

#### **Option A: Using Browser**
Simply open your browser and go to:
```
http://localhost:5000/extract-local-newspaper
```

#### **Option B: Using curl**
```bash
curl http://localhost:5000/extract-local-newspaper
```

#### **Option C: Using PowerShell**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/extract-local-newspaper" | Select-Object -ExpandProperty Content
```

---

## 📊 **Expected Response**

The endpoint will return a JSON response with:

```json
{
  "success": true,
  "image_path": "C:\\Users\\mayan\\Downloads\\app\\app\\services\\newspaper.jpg",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...(long base64 string)...",
  "extracted_data": {
    "districtCode": "3301",
    "districtName": "रायपुर",
    "policeStation": "कोतवाली अंबिकापुर",
    "accusedName": "राम कुमार",
    "complainantName": "श्याम सिंह",
    "crimeType": "हत्या",
    "newsHeading": " रायपुर, कोतवाली अंबिकापुर _प्राथमिकी संख्या ",
    "summary": "राम कुमार को हत्या के मामले में आरोपी बनाया गया है। इस प्रकरण में शिकायतकर्ता का नाम श्याम सिंह है। ",
    "fullText": "...extracted Hindi text from the newspaper image..."
  }
}
```

---

## 🔍 **What the Endpoint Does**

1. **Reads** the local image file: `app/services/newspaper.jpg`
2. **Converts** it to base64 encoding
3. **Processes** the image using OCR (Tesseract) to extract Hindi text
4. **Extracts** crime information:
   - District name (जिला)
   - Police station (थाना)
   - Accused name (आरोपी)
   - Complainant name (शिकायतकर्ता)
   - Crime type (अपराध का प्रकार)
5. **Returns** both the base64 image and extracted data in JSON format

---

## 📝 **API Documentation**

You can also view the interactive API documentation at:
- **Swagger UI**: http://localhost:5000/docs
- **ReDoc**: http://localhost:5000/redoc

---

## ⚠️ **Troubleshooting**

### **Error: Image file not found**
- Make sure `app/services/newspaper.jpg` exists
- Check the file path is correct

### **Error: Database connection failed**
- This endpoint doesn't require database connection
- It only processes the local image file

### **Error: OCR processing failed**
- Make sure Tesseract is installed and configured
- Check `app/services/ocr_processor.py` for Tesseract path

---

## 🎯 **Next Steps**

After testing this endpoint, you can:

1. **Insert dummy data** into the database using `dummy_data.sql`
2. **Test other endpoints** like `/fir-records`, `/getnews`, etc.
3. **Upload different images** by modifying the endpoint to accept file uploads

---

## 📌 **Related Files**

- **Endpoint Code**: `app/news_app.py` (lines 946-1012)
- **OCR Processor**: `app/services/ocr_processor.py`
- **Image File**: `app/services/newspaper.jpg`
- **Dummy Data**: `dummy_data.sql`

