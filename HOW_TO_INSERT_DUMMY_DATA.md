# How to Insert Dummy Data into MySQL Database

## ✅ Prerequisites
1. MySQL server is running
2. Database `cctns_state_db` exists
3. All required tables are created

## 📝 Step 1: Execute the SQL File

### Option A: Using MySQL Workbench (Recommended)
1. Open MySQL Workbench
2. Connect to your MySQL server (localhost, user: root, password: root)
3. Click on **File** → **Open SQL Script**
4. Navigate to and select `dummy_data.sql`
5. Click the **Execute** button (⚡ lightning icon) or press `Ctrl+Shift+Enter`
6. Check the output panel for success messages

### Option B: Using MySQL Command Line
```bash
# Navigate to your project directory
cd C:\Users\mayan\Downloads\app

# Execute the SQL file
mysql -u root -p cctns_state_db < dummy_data.sql

# Enter password when prompted: root
```

### Option C: Using PowerShell
```powershell
# Navigate to your project directory
cd C:\Users\mayan\Downloads\app

# Execute the SQL file
Get-Content dummy_data.sql | mysql -u root -p cctns_state_db

# Enter password when prompted: root
```

## 📊 What Data Will Be Inserted

### 1. **Districts (10 records)**
- Raipur (रायपुर)
- Durg (दुर्ग)
- Bilaspur (बिलासपुर)
- Rajnandgaon (राजनांदगांव)
- Korba (कोरबा)
- Raigarh (रायगढ़)
- Bastar (बस्तर)
- Dhamtari (धमतरी)
- Janjgir-Champa (जांजगीर-चांपा)
- Mahasamund (महासमुंद)

### 2. **Police Stations (13 records)**
- 5 stations in Raipur district
- 3 stations in Durg district
- 2 stations in Bilaspur district
- 2 stations in Rajnandgaon district
- 1 station in Korba district

### 3. **Crime Data (14 law sections)**
- Murder (हत्या) - Severity 10
- Rape (बलात्कार) - Severity 10
- Attempt to Murder (हत्या का प्रयास) - Severity 9
- Dacoity (डकैती) - Severity 9
- Robbery (लूट) - Severity 8
- Kidnapping (अपहरण) - Severity 8
- And more...

### 4. **FIR Records (10 recent records)**
- Dates: January 24, 2026 to February 1, 2026
- All with complete Hindi content
- Covering various crime types

### 5. **News Uploads (7 records)**
- Matching the FIR incidents
- From various newspapers (दैनिक भास्कर, नवभारत टाइम्स, etc.)

### 6. **Published Incidents (3 records)**
- Final processed reports
- Ready for display

## 🧪 Step 2: Verify Data Insertion

After executing the SQL file, verify the data:

```sql
-- Check districts
SELECT COUNT(*) as total_districts FROM m_district;
SELECT * FROM m_district;

-- Check police stations
SELECT COUNT(*) as total_police_stations FROM m_police_station;
SELECT * FROM m_police_station;

-- Check crime data
SELECT COUNT(*) as total_crime_types FROM crime_data;
SELECT * FROM crime_data;

-- Check FIR records
SELECT COUNT(*) as total_firs FROM t_fir_registration;
SELECT FIR_REG_NUM, REG_DT, SUBSTRING(FIR_CONTENTS, 1, 100) as preview 
FROM t_fir_registration 
ORDER BY REG_DT DESC;

-- Check news uploads
SELECT COUNT(*) as total_news FROM t_news_upload;
SELECT NEWS_ID, UPLOAD_DATE, NEWS_SOURCE FROM t_news_upload;

-- Check published incidents
SELECT COUNT(*) as total_incidents FROM t_incidents_published;
SELECT INCIDENT_NO, FIR_NUMBER, DISTRICT_NAME, PS_NAME FROM t_incidents_published;
```

## 🚀 Step 3: Test the API Endpoints

Once data is inserted, test your API:

```bash
# Test health endpoint
curl http://localhost:5000/health

# Get FIR records from last 24 hours
curl "http://localhost:5000/fir-records?last_24_hours=true"

# Get FIR records by date range
curl "http://localhost:5000/fir-records?start_date=2026-01-24&end_date=2026-02-01"

# Get news
curl "http://localhost:5000/getnews?start_date=2026-01-24&end_date=2026-02-01"

# Get law sections
curl http://localhost:5000/law-hi

# Get district name
curl "http://localhost:5000/district/name?district_cd=3301&state_cd=33"

# Get police station name
curl "http://localhost:5000/police-station/name?ps_cd=330101&district_cd=3301&state_cd=33"
```

## 📌 Expected Results

After successful insertion, you should have:
- ✅ 10 districts in Chhattisgarh
- ✅ 13 police stations across districts
- ✅ 14 crime law sections with severity scores
- ✅ 10 FIR records (recent dates)
- ✅ 7 news upload records
- ✅ 3 published incident reports

## ⚠️ Troubleshooting

### Error: "Unknown column 'DISTRICT_NAME_EN'"
- **Solution**: The SQL file has been updated to use correct column names (`DISTRICT`, `PS`, etc.)

### Error: "Table doesn't exist"
- **Solution**: Make sure you've created all tables first using the database schema SQL

### Error: "Duplicate entry"
- **Solution**: The SQL uses `ON DUPLICATE KEY UPDATE` so it's safe to run multiple times

### Error: "Access denied"
- **Solution**: Check your MySQL credentials (user: root, password: root)

## 🎯 Next Steps

After inserting dummy data:
1. ✅ Server is running on http://localhost:5000
2. ✅ Test all API endpoints
3. ✅ Check API documentation at http://localhost:5000/docs
4. ✅ Verify data in MySQL Workbench

Enjoy testing your CCTNS News Processing Application! 🎉

