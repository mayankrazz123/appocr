# ✅ Fixed: Crime Data Insert Error

## 🔧 **Problem Solved!**

The error you were getting:
```
Error Code: 1364. Field 'CRIME_TYPE_HINDI' doesn't have a default value
```

**Root Cause:** The `crime_data` table requires the `CRIME_TYPE_HINDI` column, but the old SQL was only inserting `relevant_law_section_hindi`.

**Solution:** I've updated `dummy_data.sql` to insert all three required columns:
- `CRIME_TYPE_HINDI` (crime type in Hindi)
- `RELEVANT_LAW_SECTION_HINDI` (law section in Hindi)
- `SEVERITY_SCORE` (severity rating 0-10)

---

## 🚀 **Execute the Fixed SQL**

### **Method 1: Command Line (Recommended)**

```powershell
mysql -u root -proot --default-character-set=utf8mb4 cctns_state_db < dummy_data.sql
```

This will:
- ✅ Insert 10 districts
- ✅ Insert 13 police stations
- ✅ Insert 14 crime types with law sections
- ✅ Insert 10 FIR records
- ✅ Insert 7 news uploads
- ✅ Insert 7 published incidents

---

### **Method 2: MySQL Workbench**

1. Open MySQL Workbench
2. Connect to your database
3. **File → Open SQL Script**
4. Select `dummy_data.sql`
5. Click **Execute** (⚡ lightning bolt icon)

---

## ✅ **Verify Data Was Inserted**

### **Check in MySQL:**
```sql
USE cctns_state_db;

-- Check crime data (should show 14 records)
SELECT CRIME_TYPE_HINDI, RELEVANT_LAW_SECTION_HINDI, SEVERITY_SCORE 
FROM crime_data;

-- Check all counts
SELECT 
    (SELECT COUNT(*) FROM m_district) AS districts,
    (SELECT COUNT(*) FROM m_police_station) AS police_stations,
    (SELECT COUNT(*) FROM crime_data) AS crime_types,
    (SELECT COUNT(*) FROM t_fir_registration) AS fir_records,
    (SELECT COUNT(*) FROM t_news_upload) AS news_uploads,
    (SELECT COUNT(*) FROM t_incidents_published) AS incidents;
```

**Expected Result:**
```
districts: 10
police_stations: 13
crime_types: 14
fir_records: 10
news_uploads: 7
incidents: 7
```

---

### **Check via API:**

**Step 1: Start server**
```powershell
py -3.13 -m uvicorn app.news_app:app --host 0.0.0.0 --port 5000 --reload
```

**Step 2: Test endpoints**
```bash
# Check all counts
curl "http://localhost:5000/test/all-counts"

# Get crime data
curl "http://localhost:5000/test/crime-data"

# Get law sections
curl "http://localhost:5000/law-hi"
```

**Or in browser:**
- http://localhost:5000/test/all-counts
- http://localhost:5000/test/crime-data
- http://localhost:5000/law-hi

---

## 📊 **What's in the Crime Data Now**

The corrected SQL inserts 14 crime types:

| Crime Type (Hindi) | Law Section | Severity |
|-------------------|-------------|----------|
| हत्या | भारतीय दंड संहिता धारा 302 | 10 |
| बलात्कार | भारतीय दंड संहिता धारा 376 | 10 |
| हत्या का प्रयास | भारतीय दंड संहिता धारा 307 | 9 |
| डकैती | भारतीय दंड संहिता धारा 395 | 9 |
| लूट | भारतीय दंड संहिता धारा 392 | 8 |
| अपहरण | भारतीय दंड संहिता धारा 363 | 8 |
| मारपीट | भारतीय दंड संहिता धारा 323 | 6 |
| चोरी | भारतीय दंड संहिता धारा 379 | 5 |
| धोखाधड़ी | भारतीय दंड संहिता धारा 420 | 6 |
| नशीली दवाओं की तस्करी | एनडीपीएस अधिनियम धारा 20 | 9 |
| शराब तस्करी | आबकारी अधिनियम धारा 34 | 6 |
| साइबर अपराध | आईटी अधिनियम धारा 66 | 6 |
| नाबालिग से दुष्कर्म | पॉक्सो अधिनियम धारा 4 | 10 |
| घरेलू हिंसा | घरेलू हिंसा अधिनियम धारा 3 | 4 |

---

## 🎯 **Quick Summary**

**Problem:** Column `CRIME_TYPE_HINDI` was missing in INSERT statement

**Solution:** Updated `dummy_data.sql` to include all required columns

**Action Required:** Re-run the SQL file:
```powershell
mysql -u root -proot --default-character-set=utf8mb4 cctns_state_db < dummy_data.sql
```

**Verification:** Check via API or MySQL that you have 14 crime types

---

**The error is now fixed! Just execute the updated SQL file.** ✅

