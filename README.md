# CCTNS News Processing API

## 📋 Overview

This is a FastAPI-based application for processing crime news from newspapers using OCR and extracting structured information for the Crime and Criminal Tracking Network & Systems (CCTNS).

---

## 🚀 Quick Start

### **1. Start the Server**
```powershell
py -3.13 -m uvicorn app.news_app:app --host 0.0.0.0 --port 5000 --reload
```

### **2. Access API Documentation**
- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

---

## 📡 API Endpoints

### **Master Data Endpoints**

#### 1. Get All Districts
```http
GET /districts?state_cd=33
```

**Parameters:**
- `state_cd` (int, optional): State code (default: 33 for Chhattisgarh)

**Response:**
```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "DISTRICT_CD": 3301,
      "STATE_CD": 33,
      "DISTRICT": "रायपुर"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:5000/districts?state_cd=33"
```

---

#### 2. Get All Police Stations
```http
GET /police-stations?state_cd=33&district_cd=3301
```

**Parameters:**
- `state_cd` (int, optional): State code (default: 33)
- `district_cd` (int, optional): Filter by district code

**Response:**
```json
{
  "success": true,
  "count": 13,
  "data": [
    {
      "PS_CD": 330101,
      "DISTRICT_CD": 3301,
      "STATE_CD": 33,
      "PS": "कोतवाली",
      "LANG_CD": 6
    }
  ]
}
```

**Examples:**
```bash
# All police stations in state
curl "http://localhost:5000/police-stations?state_cd=33"

# Police stations in specific district
curl "http://localhost:5000/police-stations?state_cd=33&district_cd=3301"
```

---

#### 3. Get Specific District Name
```http
GET /district/name?district_cd=3301&state_cd=33
```

**Parameters:**
- `district_cd` (float, required): District code
- `state_cd` (float, required): State code

**Example:**
```bash
curl "http://localhost:5000/district/name?district_cd=3301&state_cd=33"
```

---

#### 4. Get Specific Police Station Name
```http
GET /police-station/name?ps_cd=330101&district_cd=3301&state_cd=33
```

**Parameters:**
- `ps_cd` (float, required): Police station code
- `district_cd` (float, required): District code
- `state_cd` (float, required): State code

**Example:**
```bash
curl "http://localhost:5000/police-station/name?ps_cd=330101&district_cd=3301&state_cd=33"
```

---

#### 5. Get All Crime Law Sections (Hindi)
```http
GET /law-hi
```

**Response:**
```json
[
  "भारतीय दंड संहिता धारा 302",
  "भारतीय दंड संहिता धारा 376",
  "भारतीय दंड संहिता धारा 307"
]
```

**Example:**
```bash
curl "http://localhost:5000/law-hi"
```

---

### **Transaction Data Endpoints**

#### 6. Get FIR Records
```http
GET /fir-records?start_date=2026-01-24&end_date=2026-02-01
```

**Parameters:**
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format

**Response:**
```json
[
  {
    "FIR_ID": 1,
    "FIR_REG_NUM": "001/2026",
    "STATE_CD": 33,
    "DISTRICT_CD": 3301,
    "PS_CD": 330101,
    "REG_DT": "2026-01-24T10:30:00",
    "FIR_CONTENTS": "रायपुर जिले के कोतवाली थाना क्षेत्र में हत्या की घटना..."
  }
]
```

**Example:**
```bash
curl "http://localhost:5000/fir-records?start_date=2026-01-24&end_date=2026-02-01"
```

---

#### 7. Get News Uploads
```http
GET /getnews?start_date=2026-01-24&end_date=2026-02-01
```

**Parameters:**
- `start_date` (string, optional): Start date in YYYY-MM-DD format
- `end_date` (string, optional): End date in YYYY-MM-DD format
- `last_24_hours` (boolean, optional): Set to true to fetch past 24 hours

**Response:**
```json
[
  {
    "UPLOAD_ID": 1,
    "LANG_CD": 6,
    "UPLOADED_IMAGE": "base64_encoded_image...",
    "RECORD_CREATED_ON": "2026-02-01T11:00:00"
  }
]
```

**Examples:**
```bash
# Get news by date range
curl "http://localhost:5000/getnews?start_date=2026-01-24&end_date=2026-02-01"

# Get news from last 24 hours
curl "http://localhost:5000/getnews?last_24_hours=true"
```

---

#### 8. Get Published Incidents
```http
GET /incidents?district_cd=3301&limit=100
```

**Parameters:**
- `district_cd` (int, optional): Filter by district code
- `limit` (int, optional): Maximum number of records (default: 100)

**Response:**
```json
{
  "success": true,
  "count": 7,
  "data": [
    {
      "ID": 1,
      "INCIDENT_NO": "INC001",
      "DISTRICT_NAME": "रायपुर",
      "PS_NAME": "कोतवाली",
      "ACCUSED_NAME": "मोहन सिंह",
      "COMPLAINANT_NAME": "राम कुमार",
      "CRIME_TYPE": "हत्या",
      "SUMMARY": "...",
      "RECORD_CREATED_ON": "2026-02-01 12:00:00"
    }
  ]
}
```

**Examples:**
```bash
# All incidents
curl "http://localhost:5000/incidents"

# Incidents in specific district
curl "http://localhost:5000/incidents?district_cd=3301"

# Limit results
curl "http://localhost:5000/incidents?limit=50"
```

---

### **Processing Endpoints**

#### 9. Upload News Image
```http
POST /uploadnews
```

**Request:**
- Content-Type: `multipart/form-data`
- Body: File upload

**Parameters:**
- `file` (UploadFile, required): Image file to upload

**Response:**
```json
{
  "message": "News uploaded successfully",
  "upload_id": 1
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/uploadnews" \
  -F "file=@newspaper.jpg"
```

---

#### 10. Extract Articles from Uploaded Image
```http
POST /extract-articles
```

**Request:**
```json
{
  "uploadedImage": "base64_encoded_image_string"
}
```

**Response:**
```json
{
  "success": true,
  "articles": [
    {
      "districtCode": "3301",
      "districtName": "रायपुर",
      "policeStation": "कोतवाली",
      "accusedName": "मोहन सिंह",
      "complainantName": "राम कुमार",
      "crimeType": "हत्या",
      "newsHeading": "रायपुर में हत्या की घटना",
      "summary": "...",
      "fullText": "..."
    }
  ]
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/extract-articles" \
  -H "Content-Type: application/json" \
  -d '{"uploadedImage": "base64_string_here"}'
```

---

#### 11. Extract Local Newspaper
```http
GET /extract-local-newspaper
```

Processes the local newspaper image at `app/services/newspaper.jpg` and returns extracted data with base64 image.

**Response:**
```json
{
  "success": true,
  "image_path": "app/services/newspaper.jpg",
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAA...",
  "extracted_data": {
    "districtCode": "3301",
    "districtName": "रायपुर",
    "policeStation": "कोतवाली",
    "accusedName": "राम कुमार",
    "complainantName": "श्याम सिंह",
    "crimeType": "हत्या",
    "newsHeading": "...",
    "summary": "...",
    "fullText": "..."
  }
}
```

**Example:**
```bash
curl "http://localhost:5000/extract-local-newspaper"
```

---

#### 12. Save Summary
```http
POST /savesummary
```

**Request:**
```json
{
  "date": "2026-02-01",
  "district": "रायपुर",
  "policeStation": "कोतवाली",
  "accused": "मोहन सिंह",
  "complainant": "राम कुमार",
  "crimeType": "हत्या",
  "summary": "रायपुर में हत्या की घटना..."
}
```

**Response:**
```json
{
  "message": "Summary saved successfully",
  "incident_id": 1
}
```

---

#### 13. Extract Keywords
```http
GET /extract-keywords
```

Extracts keywords from news articles for analysis.

**Example:**
```bash
curl "http://localhost:5000/extract-keywords"
```

---

#### 14. Generate Report
```http
GET /generate-report
```

Generates final summary report from processed news data.

**Response:**
```json
{
  "message": "Report generation complete",
  "total": 10,
  "report_data": [...]
}
```

**Example:**
```bash
curl "http://localhost:5000/generate-report"
```

---

### **Utility Endpoints**

#### 15. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl "http://localhost:5000/health"
```

---

### **Test Endpoints** (For Development)

#### 16. Test All Counts
```http
GET /test/all-counts
```

Returns count of all records in database tables.

**Response:**
```json
{
  "success": true,
  "counts": {
    "districts": 10,
    "police_stations": 13,
    "crime_types": 14,
    "fir_records": 10,
    "news_uploads": 7,
    "incidents": 7
  },
  "expected": {
    "districts": 10,
    "police_stations": 13,
    "crime_types": 14,
    "fir_records": 10,
    "news_uploads": 7,
    "incidents": 7
  },
  "status": "OK"
}
```

**Example:**
```bash
curl "http://localhost:5000/test/all-counts"
```

---

#### 17-21. Other Test Endpoints

- `GET /test/districts` - Get all districts
- `GET /test/police-stations` - Get all police stations
- `GET /test/crime-data` - Get all crime data
- `GET /test/fir-records` - Get all FIR records
- `GET /test/incidents` - Get all incidents

---

## 📊 Complete Endpoint Summary

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 1 | `/districts` | GET | Get all districts |
| 2 | `/police-stations` | GET | Get all police stations |
| 3 | `/district/name` | GET | Get specific district name |
| 4 | `/police-station/name` | GET | Get specific PS name |
| 5 | `/law-hi` | GET | Get crime law sections (Hindi) |
| 6 | `/fir-records` | GET | Get FIR records by date |
| 7 | `/getnews` | GET | Get news uploads by date |
| 8 | `/incidents` | GET | Get published incidents |
| 9 | `/uploadnews` | POST | Upload news image |
| 10 | `/extract-articles` | POST | Extract from uploaded image |
| 11 | `/extract-local-newspaper` | GET | Extract local newspaper.jpg |
| 12 | `/savesummary` | POST | Save incident summary |
| 13 | `/extract-keywords` | GET | Extract keywords |
| 14 | `/generate-report` | GET | Generate final report |
| 15 | `/health` | GET | Health check |
| 16-21 | `/test/*` | GET | Test endpoints for development |

---

## 🗄️ Database Setup

### **1. Create Database and Tables**
```powershell
mysql -u root -proot --default-character-set=utf8mb4 < create_database.sql
```

### **2. Insert Dummy Data**
```powershell
mysql -u root -proot --default-character-set=utf8mb4 cctns_state_db < dummy_data.sql
```

### **3. Verify Data**
```sql
USE cctns_state_db;
SELECT COUNT(*) FROM m_district;
SELECT COUNT(*) FROM crime_data;
```

---

## 🔧 Configuration

### **Database Connection**
Edit `app/news_app.py`:
```python
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='cctns_state_db',
    cursorclass=pymysql.cursors.DictCursor
)
```

---

## 📝 Sample Data

After running `dummy_data.sql`, you'll have:
- ✅ **10 Districts** - Chhattisgarh state districts
- ✅ **13 Police Stations** - Various police stations
- ✅ **14 Crime Types** - IPC sections with Hindi names
- ✅ **10 FIR Records** - Sample FIR records
- ✅ **7 News Uploads** - Sample news records
- ✅ **7 Incidents** - Published incidents

---

## 🌐 Interactive Documentation

Once the server is running, visit:
- **Swagger UI:** http://localhost:5000/docs
- **ReDoc:** http://localhost:5000/redoc

These provide interactive API testing with request/response examples.

---

## 🧪 Testing

### **Quick Test Script**
```powershell
# Double-click this file
test_database.bat
```

### **Manual Testing**
```bash
# Check if server is running
curl "http://localhost:5000/health"

# Get all districts
curl "http://localhost:5000/districts?state_cd=33"

# Get FIR records
curl "http://localhost:5000/fir-records?start_date=2026-01-24&end_date=2026-02-01"

# Check database counts
curl "http://localhost:5000/test/all-counts"
```

---

## 📚 Additional Documentation

- **`WORKING_ENDPOINTS.md`** - Detailed endpoint documentation
- **`TEST_DATABASE_API.md`** - Testing guide
- **`CHECK_DUMMY_DATA.md`** - Quick data verification
- **`START_HERE.md`** - Quick start guide
- **`QUICK_API_REFERENCE.md`** - Quick reference card

---

## 🛠️ Technologies Used

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **PyMySQL** - MySQL connector
- **Tesseract OCR** - Hindi text extraction
- **Pillow** - Image processing
- **Python 3.13** - Programming language

---

## 📞 Support

For issues or questions, check the documentation files or visit the interactive API docs at `/docs`.

---

**Happy Coding! 🎉**

