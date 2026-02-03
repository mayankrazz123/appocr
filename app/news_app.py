from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import Error
from typing import List
from datetime import datetime
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import base64
from fastapi import File, UploadFile, Form
from dateutil import parser as dateutil_parser
from typing import Optional
from app.services.ocr_processor import process_base64_images
from fastapi import FastAPI, Query, Request, HTTPException
from typing import Optional
import json
from fastapi import Request
from datetime import datetime, timedelta
import uvicorn
import re
import pymysql
import os
from pathlib import Path

# NER pipeline is disabled - requires HuggingFace authentication
ner_pipeline = None

app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_connection():
    try:
        connection = pymysql.connect(
            host='localhost',          # Change to your MySQL host
            user='root',               # Change to your MySQL username
            password='root',  # Change to your MySQL password
            database='cctns_state_db',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")



class FIRRecord(BaseModel):
    FIR_REG_NUM: float
    STATE_CD: float
    DISTRICT_CD: float
    PS_CD: float
    REG_DT: datetime
    FIR_CONTENTS: Optional[str]
    



@app.get("/fir-records", response_model=List[FIRRecord])
def get_fir_records(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD (optional if single date)"),
    last_24_hours: Optional[bool] = Query(False, description="Fetch records from the past 24 hours")
):
    try:
        if last_24_hours:
            start = datetime.now() - timedelta(days=1)
            end = datetime.now()
        elif start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else start
        else:
            raise HTTPException(status_code=400, detail="Provide either 'last_24_hours' or 'start_date'")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = conn.cursor()  # Already configured as DictCursor in get_connection()
    query = """
        SELECT FIR_REG_NUM, STATE_CD, DISTRICT_CD, PS_CD, REG_DT, FIR_CONTENTS
        FROM t_fir_registration
        WHERE REG_DT BETWEEN %s AND %s
    """
    cursor.execute(query, (start, end))
    records = cursor.fetchall()

    # ✅ Convert REG_DT to string for each record
    for rec in records:
        if isinstance(rec.get("REG_DT"), datetime):
            rec["REG_DT"] = rec["REG_DT"].strftime("%Y-%m-%d %H:%M:%S")

    cursor.close()
    conn.close()

    return JSONResponse(content=records)



@app.get("/getnews")
def get_news(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format (optional)"),
    last_24_hours: Optional[bool] = Query(False, description="Set to true to fetch past 24 hours")
):
    try:
        if last_24_hours:
            start = datetime.now() - timedelta(days=1)
            end = datetime.now()
        elif start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
            else:
                end = start + timedelta(days=1) - timedelta(seconds=1)
        else:
            raise HTTPException(status_code=400, detail="Provide either 'last_24_hours' or 'start_date'")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    print(start);
    print(end);
    query = """
        SELECT UPLOAD_ID, LANG_CD, UPLOADED_IMAGE, RECORD_CREATED_ON
        FROM t_news_upload
        WHERE RECORD_CREATED_ON BETWEEN %s AND %s
    """
    cursor.execute(query, (start, end))
    rows = cursor.fetchall()
    print(len(rows));
    result = []
    for upload_id, lang_cd, image_blob, created_on in rows:
        image_base64 = base64.b64encode(image_blob).decode('utf-8') if image_blob else None # type: ignore
        result.append({
            "upload_id": upload_id,
            "language_code": lang_cd,
            "image_base64": image_base64,
            "created_on": str(created_on)
        })

    cursor.close()
    conn.close()

    return JSONResponse(content=result)





@app.post("/uploadnews")
async def upload_news_image(
    file: UploadFile = File(...),
    language: str = Form("Hindi")
):
    try:
        contents = await file.read()
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read file")

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        query = "INSERT INTO news_media (language, uploaded_image) VALUES (%s, %s)"
        cursor.execute(query, (language, contents))
        conn.commit()
        cursor.close()
        conn.close()
        return JSONResponse(content={"status": "success", "message": "Image uploaded successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





class SummaryData(BaseModel):
    date: str
    district: str
    police_station: str
    fir_number: str
    complainant: str
    accused: str
    weapon: str
    crime_type: str
    score: int
    crime_category: str
    heading: str
    summary: str



def parse_date(date_str: str) -> Optional[datetime]:
    if not date_str or date_str.strip().upper() in ("N/A", "NA", "NONE"):
        return None

    known_formats = [
        "%d.%m.%y", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d",
        "%d-%m-%Y", "%d %B %Y", "%d %b %Y"
    ]

    for fmt in known_formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    # Try smart fallback
    try:
        return dateutil_parser.parse(date_str.strip(), dayfirst=True)
    except Exception:
        return None




from fastapi import HTTPException
from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse

@app.post("/savesummary")
def save_summary(data: SummaryData):
    parsed_date = parse_date(data.date)

    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    insert_query = """
        INSERT INTO t_incidents_published (
            INCIDENT_NO, UPLOAD_ID, DISTRICT_NAME, PS_NAME,FIR_NUMBER,
            COMPLAINTANT_NAME, ACCUSED_NAME, WEAPON, CRIME_TYPE,
            NEWS_SCORE, CRIME_CATEGORY,  SUMMARY,
            RECORD_CREATED_ON, RECORD_CREATED_BY
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """


    row_no: int = get_incident_number();
    print(row_no)
    now = datetime.now()

    values = (
        row_no+1,
        1,
        data.district,
        data.police_station,
        data.fir_number,
        data.complainant,
        data.accused,
        data.weapon,
        data.crime_type,
        data.score,
        data.crime_category,
        #data.heading,
        data.summary,
        now,             # RECORD_CREATED_ON
        "SYSTEM",        # RECORD_CREATED_BY
    )

    try:
        cursor = conn.cursor()
        cursor.execute(insert_query, values)
        conn.commit()
        cursor.close()
        conn.close()
        return {"status": "success", "message": "Summary saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/police-station/name")
def get_police_station_name(ps_cd: float, district_cd: float, state_cd: float):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT PS FROM m_police_station
            WHERE PS_CD = %s AND DISTRICT_CD = %s AND STATE_CD = %s
        """
        cursor.execute(query, (ps_cd, district_cd, state_cd))
        result = cursor.fetchone()

        if result:
            return {"police_station": result["PS"]}
        else:
            raise HTTPException(status_code=404, detail="Police station not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            try:
                cursor.fetchall()  # Consume any remaining results
            except:
                pass
            cursor.close()
        conn.close()

def get_all_ps(district_cd: int, state_cd: int):
    conn = get_connection()
    print (conn)
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    try:
        print ('try ')
        cursor = conn.cursor()
        query = """
            SELECT PS FROM m_police_station
            WHERE LANG_CD = 6 AND DISTRICT_CD = %s AND STATE_CD =%s
        """
        cursor.execute(query, ( 33341, 33))
        result = cursor.fetchall()

        if result:
            return result
        else:
            raise HTTPException(status_code=404, detail="Police stations not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            try:
                cursor.fetchall()  # Consume any remaining results
            except:
                pass
            cursor.close()
        conn.close()


@app.get("/district/name")
def get_district_name(district_cd: float, state_cd: float):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT DISTRICT FROM m_district
            WHERE DISTRICT_CD = %s AND STATE_CD = %s
        """
        cursor.execute(query, (district_cd, state_cd))
        result = cursor.fetchone()

        if result:
            return {"district_name": result["DISTRICT"]}
        else:
            raise HTTPException(status_code=404, detail="District not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            try:
                cursor.fetchall()  # Consume any remaining unread results
            except:
                pass
            cursor.close()
        conn.close()


def get_incident_number():
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT max(INCIDENT_NO) FROM t_incidents_published;
        """
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            return result["max(INCIDENT_NO)"];
        else:
            raise HTTPException(status_code=404, detail="District not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            try:
                cursor.fetchall()  # Consume any remaining unread results
            except:
                pass
            cursor.close()
        conn.close()

class UploadData(BaseModel):
        uploadedImage:  str


@app.post("/extract-articles")
async def extract_news_articles(
    uploadData: UploadData,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    last_24_hours: Optional[bool] = Query(False)
):
    
    #print(uploadData)
    #bytes_representation = uploadData.uploadedImage.encode(encoding="utf-8")
     
    #image_base64 = base64.b64encode(bytes_representation).decode('utf-8');
    # 1. Reuse get_news to fetch image records
    

    print (uploadData.uploadedImage);
    


    # 3. OCR processing
    structured_articles = process_base64_images(uploadData.uploadedImage)
    crime_type_hi = [
        "हत्या", "हत्या का प्रयास", "बलात्कार", "बलात्कार का प्रयास", "छेड़छाड़", "दुष्कर्म", "अपहरण", "डकैती", "लूट", "चोरी",
        "गृहभेदन", "मारपीट", "धोखाधड़ी", "ठगी", "घूसखोरी", "साइबर अपराध", "नकली नोट", "नशीली दवाओं की तस्करी", "शराब तस्करी",
        "मानव तस्करी", "घरेलू हिंसा", "आतंकवाद", "देशद्रोह", "धार्मिक उन्माद", "नाबालिग से दुष्कर्म", "पत्नि पर अत्याचार",
        "आत्महत्या के लिए उकसाना", "धमकी देना", "अवैध हथियार रखना", "हथियारों की तस्करी", "जुआ", "मादक पदार्थ तस्करी",
        "नशीली दवाओं की तस्करी", "तस्करी", "नक्सली", "आत्मसमर्पण", "ईनामी", "पुनर्वास नीति", "माओवाद", "गांजा", "मादक पदार्थ",
        "एनडीपीएस", "बिक्री", "अवैध परिवहन", "नक्सलवाद", "देशद्रोह", "गौ हत्या", "गौ तस्करी","गायों", "देह व्यापार"
    ]
    
    crimeType=extract_crime_keywords(structured_articles);
    psName=extract_police_station(structured_articles[0])
    accusedName=extract_accused(structured_articles[0]);
    complainantName=extract_complainant(structured_articles[0]);
    dsName=extract_district(structured_articles[0])
    print (accusedName)
    print (psName)
    print (complainantName)
    ps_name_db=extract_ps_keywords(structured_articles[0])
    #structured_articles.append(psName);
    print(ps_name_db)
    distictCode= get_district_Code( 33,dsName)
    #dsName = get_district_name(distictCode, 33)
    heading, summary = extract_summary_string(accusedName, psName, complainantName, '', dsName, crimeType)
    #structured_articles.append(heading)
    #structured_articles.append(summary)
    
    return {"distictCd": distictCode['DISTRICT_CD'], "districtName": dsName, "psName" :psName , "accusedName" : accusedName, "complainantName":"","crimeType" :crimeType, "newsHeading":  heading, "summary": summary,"full_text":structured_articles[0]}

chhattisgarh_districts = ["बालोद", "बलौदाबाजार", "बलरामपुर", "बस्तर", "बेमेतरा", "बिलासपुर", "दंतेवाड़ा", "धमतरी", "दुर्ग", "गौरेला-पेंड्रा-मरवाही", "गरियाबंद", "जांजगीर-चांपा", "जशपुर", "कवर्धा", "कांकेर", "कोरबा", "कोरिया", "महासमुंद", "मुंगेली", "नारायणपुर", "रायगढ़", "रायपुर", "राजनांदगांव", "सुकमा", "सूरजपुर", "सरगुजा", "बीजापुर", "कोंडागांव", "खैरागढ़-छुईखदान-गंडई", "मोहला-मानपुर-अंबागढ़ चौकी", "सारंगढ़-बिलाईगढ़", "मनीन्द्रगढ़-चिरमिरी-भरतपुर"]
def extract_district(text):
    for district in chhattisgarh_districts:
        if district in text:
            return district
            break
    return "N/A"
    
def extract_police_station(text):
    for ps in ambikapur_police_stations:
        if ps in text:
            return ps
            break
    return "N/A" 

ambikapur_police_stations = [
    "कोतवाली अंबिकापुर",
    "गांधी नगर थाना",
    "महिला थाना",
    "दरिमा थाना",
    "उजियारपुर थाना",
    "सीतापुर थाना",
    "लुण्ड्रा थाना",
    "मैनपाट थाना",
    "बतौली थाना",
    "ओडगी थाना",
    "झारखंडी थाना",
    "प्रतापपुर थाना",
    "राजपुर थाना",
    "कुशमी थाना",
    "भटगांव थाना",
    "बिश्रामपुर थाना",
    "भटगांव कोयलरी थाना",
    "अभनपुर",
    "आजाद चौक",
    "आरंग",
    "उरला",
    "आमानाका",
    "सिविल लाइन्स",
     "सिविल लाइन",
    "टिकरापारा",
    "धरसीवां",
    "देवेन्द्रनगर",
    "दीनदयाल नगर",
    "गोल बाजार",
    "गंज",
    "गोबरा नवापारा",
    "गुढ़ियारी",
    "खमतराई",
    "खरोरा",
    "माना कैम्प",
    "मौदहापारा",
    "मंदिर हसौद",
    "तिल्दा नेवरा",
    "पुरानी बस्ती",
    "पंडरी",
    "महिला थाना",
    "कोतवाली",
    "राजेंद्रनगर",
    "सरस्वतीनगर",
    "तेलीबांधा",
    "विधानसभा",
    "राखी",
    "अनुसूचित जाति कल्याण रायपुर",
    "अपराध अन्वेषण विभाग, पुलिस मुख्यालय रायपुर",
    "राज्य साईबर पुलिस थाना",
    "कबीर नगर",
    "मुजगहन",
    "ए टी एस",
    "खम्हारडीह",
    "सायबर पुलिस थाना, रेंज रायपुर"
]


def get_district_Code(state_cd:int, districtName:str):
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor = None
    try:
        cursor = conn.cursor()
        query = """
            SELECT DISTRICT_CD FROM m_district
            WHERE STATE_CD = %s and DISTRICT=%s
        """
        cursor.execute(query, ( state_cd, districtName))
        result = cursor.fetchone()
        if result:
            print(len(result))
            print(result)
            return result
        else:
            raise HTTPException(status_code=404, detail="District not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if cursor:
            try:
                cursor.fetchall()  # Consume any remaining unread results
            except:
                pass
            cursor.close()
        conn.close()


def extract_summary_string(accusedName, psName, complainantName, fir_no, dsName, crime_type_extracted):
    heading = f" {dsName}, {psName} _प्राथमिकी संख्या {fir_no}"
    summary = (
        f"{accusedName} को {crime_type_extracted} के मामले में आरोपी बनाया गया है। "
        f"इस प्रकरण में शिकायतकर्ता का नाम {complainantName} है। "
    ) 
    
    return heading, summary

def extract_accused_keywords(structured_articles):
    
    accused_name_keywords = ["थाना", "पुलिस स्टेशन" ,"चौकी" , "पुलिस चौकी"]

    
    found_matches = []
    for keywords in accused_name_keywords:
        matches = re.findall(keywords, structured_articles[0])
        if matches:
            found_matches.extend(matches)
   
    print(f"' contains the pattern {len(found_matches)}'")
    structured_articles.append(found_matches)
    

    
def extract_complaintant_keywords(structured_articles):
    
    accused_name_keywords = [
        
    ]

    
    found_matches = []
    for keywords in accused_name_keywords:
        matches = re.findall(keywords, structured_articles[0])
        if matches:
            found_matches.extend(matches)
   
    print(f"' contains the pattern {len(found_matches)}'")
    structured_articles.append(found_matches)
   
def extract_ps_keywords(structured_articles):
    print ('extract_ps_keywords')
    ps_keywords = ["थाना", "पुलिस स्टेशन" ,"चौकी" , "पुलिस चौकी","पुलिस थाना","थाने" ]
    police_stations = get_all_ps(33341,33)
    print(police_stations)
    for ps in police_stations:
       # print(type(ps))
        #print(f" PS Name ::  {ps['PS']}")
        if (ps['PS'] +" थाना") in structured_articles[0]:
                print(f"' PS Name ::  {ps['PS']}'")
                return ps['PS']
                break


    return "N/A"
    
def extract_accused(text):
    # List of regex patterns covering different common Hindi patterns
    patterns = [
        r'गिरफ्तार आरोपी\s*-\s*([^\n]*)',
        r'आरोपी का नाम\s*[:-]?\s*([^\n]*)',
        r'आरोपी\s*[:-]?\s*([^\n]*)',
        r'संचालक\s*[:-]?\s*([^\n]*)',
        # r'नाम\s*[:-]?\s*([^\n]*)',
        r'अभियुक्त\s*[:-]?\s*([^\n]*)'
    ]

    # Handle both string and list inputs
    text_str = text[0] if isinstance(text, list) else text

    for pattern in patterns:
        match = re.search(pattern, text_str)
        if match:
            matched_text = match.group(1).strip()
            # Remove common suffixes like 'पिता', 'पुत्र', etc.
            matched_text = re.split(r'पिता|पुत्र|पति|Father|Son|Husband', matched_text)[0].strip()
            # Extract words (Hindi, Latin letters, digits)
            words = re.findall(r'[\w\u0900-\u097F]+', matched_text)
            # Take at most first 5 words
            limited_words = words[:5]
            name = ' '.join(limited_words)
            if name:
                return name

    # Fallback: use NER (e.g., transformers pipeline)
    try:
        if ner_pipeline:
            ner_results = ner_pipeline(text_str)
            persons = [ent['word'] for ent in ner_results if ent['entity_group'] == 'PER'] # type: ignore
            if persons:
                return persons[0]
    except Exception:
        pass  # fail silently if NER isn't available

    return "N/A"
    
def extract_complainant(text):
    # List of common patterns to detect complainant in Hindi FIRs
    patterns = [
        r'प्रार्थी\s*[:-]?\s*([^\n]*)',
        r'शिकायतकर्ता\s*[:-]?\s*([^\n]*)',
        r'फरियादी\s*[:-]?\s*([^\n]*)',
        r'Complainant\s*[:-]?\s*([^\n]*)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            matched_text = match.group(1).strip()
            words = re.findall(r'[\w\u0900-\u097F]+', matched_text)
            limited_words = words[:8]
            name = ' '.join(limited_words)
            if name:
                return name

    return "N/A"


def extract_crime_keywords(structured_articles):
    
    crime_type_hi = [
        "हत्या","कत्ल","खून",

        "हत्या का प्रयास","कत्ल का प्रयास","खून का प्रयास","हत्या की कोशिश","कत्ल की प्रयास","खून की प्रयास","डकैती",
        "बलात्कार", "बलात्कार का प्रयास", "छेड़छाड़", "दुष्कर्म","दुष्कर्म का प्रयास", "अपहरण", "डकैती", "लूट", "चोरी",
        "गृहभेदन", "मारपीट", "धोखाधड़ी", "ठगी", "घूसखोरी", "साइबर अपराध", "नकली नोट", "नशीली दवाओं की तस्करी", "नशीली दवा", "शराब तस्करी",
        "मानव तस्करी", "घरेलू हिंसा", "आतंकवाद", "देशद्रोह", "धार्मिक उन्माद", "नाबालिग से दुष्कर्म", "पत्नि पर अत्याचार",
        "आत्महत्या के लिए उकसाना", "धमकी देना", "अवैध हथियार रखना", "हथियारों की तस्करी", "जुआ", "मादक पदार्थ तस्करी",
        "नशीली दवाओं की तस्करी", "तस्करी", "नक्सली", "आत्मसमर्पण", "ईनामी", "पुनर्वास नीति", "माओवाद", "गांजा", "मादक पदार्थ",
        "एनडीपीएस", "बिक्री", "अवैध परिवहन", "नक्सलवाद", "देशद्रोह", "गौ हत्या", "गौ तस्करी","गायो","देह व्यापार"
    ]

    
    found_matches = []
    for crime in crime_type_hi:
        matches = re.findall(crime, structured_articles[0])
        if matches:
            found_matches.extend(matches)
   
    print(f"' contains the pattern {len(found_matches)}'")
    unique_elements = list(set(found_matches))
    result = ", ".join(unique_elements)
    print(result)
    return unique_elements


from fastapi import APIRouter, Request, Query, HTTPException
from typing import Optional
from app.services.keyword_extractor import analyze_articles



@app.get("/extract-keywords")
def auto_extract_keywords(
    request: Request,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    last_24_hours: Optional[bool] = Query(False)
):
    import json

    try:
        if last_24_hours:
            end = datetime.now()
            start = end - timedelta(days=1)
        elif start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else start
        else:
            raise HTTPException(status_code=400, detail="Provide either 'last_24_hours' or 'start_date'")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    fir_start = start - timedelta(days=7)
    fir_end = end

    # --- Step 1: Get News Images from Database ---
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    query = """
        SELECT UPLOAD_ID, LANG_CD, UPLOADED_IMAGE, RECORD_CREATED_ON
        FROM t_news_upload
        WHERE RECORD_CREATED_ON BETWEEN %s AND %s
    """
    cursor.execute(query, (start, end))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Extract articles from news images if available
    articles = []
    for upload_id, lang_cd, image_blob, created_on in rows:
        if image_blob:
            try:
                image_base64 = base64.b64encode(image_blob).decode('utf-8') # type: ignore
                structured_articles = process_base64_images(image_base64)
                if structured_articles:
                    articles.extend(structured_articles)
            except Exception as e:
                print(f"Error processing news image {upload_id}: {str(e)}")
                continue

    # --- Step 2: Get FIR Records ---
    # Query FIR records directly instead of calling the endpoint
    conn_fir = get_connection()
    if not conn_fir:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor_fir = conn_fir.cursor()
    fir_query = """
        SELECT FIR_REG_NUM, STATE_CD, DISTRICT_CD, PS_CD, REG_DT, FIR_CONTENTS
        FROM t_fir_registration
        WHERE REG_DT BETWEEN %s AND %s
    """
    cursor_fir.execute(fir_query, (fir_start, fir_end))
    fir_list = cursor_fir.fetchall()
    cursor_fir.close()
    conn_fir.close()

    fir_texts = [
        item["FIR_CONTENTS"].strip()
        for item in fir_list
        if item.get("FIR_CONTENTS") and len(item["FIR_CONTENTS"].strip()) > 30
    ]

    if not articles and not fir_texts:
        raise HTTPException(status_code=404, detail="No valid news or FIR text to extract.")

    # --- Step 3: Keyword Extraction ---
    news_keywords = analyze_articles(articles) if articles else []
    fir_keywords = analyze_articles(fir_texts) if fir_texts else []

    return {
        "news_keywords": news_keywords,
        "fir_keywords": fir_keywords
    }




from fastapi import APIRouter, HTTPException
from typing import List
from fastapi.responses import JSONResponse

@app.get("/districts")
def get_districts(state_cd: int = Query(33, description="State code (default: 33 for Chhattisgarh)")):
    """
    Get all districts for a given state
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        query = "SELECT DISTRICT_CD, STATE_CD, DISTRICT FROM m_district WHERE STATE_CD = %s ORDER BY DISTRICT_CD"
        cursor.execute(query, (state_cd,))
        districts = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "success": True,
            "count": len(districts),
            "data": districts
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/police-stations")
def get_police_stations(
    state_cd: int = Query(33, description="State code (default: 33 for Chhattisgarh)"),
    district_cd: Optional[int] = Query(None, description="District code (optional filter)")
):
    """
    Get all police stations for a given state, optionally filtered by district
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        if district_cd:
            query = "SELECT PS_CD, DISTRICT_CD, STATE_CD, PS, LANG_CD FROM m_police_station WHERE STATE_CD = %s AND DISTRICT_CD = %s ORDER BY PS_CD"
            cursor.execute(query, (state_cd, district_cd))
        else:
            query = "SELECT PS_CD, DISTRICT_CD, STATE_CD, PS, LANG_CD FROM m_police_station WHERE STATE_CD = %s ORDER BY PS_CD"
            cursor.execute(query, (state_cd,))

        stations = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "success": True,
            "count": len(stations),
            "data": stations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/law-hi", response_model=List[str])
def get_law_hi():
    """
    Get all crime law sections in Hindi from the database
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        query = "SELECT RELEVANT_LAW_SECTION_HINDI FROM crime_data WHERE RELEVANT_LAW_SECTION_HINDI IS NOT NULL"
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        # Return plain list - rows are dictionaries with DictCursor
        return [row["RELEVANT_LAW_SECTION_HINDI"] for row in rows if row.get("RELEVANT_LAW_SECTION_HINDI")]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents")
def get_incidents(
    district_cd: Optional[int] = Query(None, description="Filter by district code"),
    limit: int = Query(100, description="Maximum number of records to return")
):
    """
    Get published incidents, optionally filtered by district
    """
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        cursor = conn.cursor()
        if district_cd:
            query = """
                SELECT ID, INCIDENT_NO, UPLOAD_ID, DISTRICT_NAME, PS_NAME,
                       ACCUSED_NAME, COMPLAINANT_NAME, CRIME_TYPE, NEWS_HEADING,
                       SUMMARY, RECORD_CREATED_ON
                FROM t_incidents_published
                WHERE DISTRICT_CD = %s
                ORDER BY RECORD_CREATED_ON DESC
                LIMIT %s
            """
            cursor.execute(query, (district_cd, limit))
        else:
            query = """
                SELECT ID, INCIDENT_NO, UPLOAD_ID, DISTRICT_NAME, PS_NAME,
                       ACCUSED_NAME, COMPLAINANT_NAME, CRIME_TYPE, NEWS_HEADING,
                       SUMMARY, RECORD_CREATED_ON
                FROM t_incidents_published
                ORDER BY RECORD_CREATED_ON DESC
                LIMIT %s
            """
            cursor.execute(query, (limit,))

        incidents = cursor.fetchall()
        cursor.close()
        conn.close()

        # Convert datetime to string
        for incident in incidents:
            if isinstance(incident.get("RECORD_CREATED_ON"), datetime):
                incident["RECORD_CREATED_ON"] = incident["RECORD_CREATED_ON"].strftime("%Y-%m-%d %H:%M:%S")

        return {
            "success": True,
            "count": len(incidents),
            "data": incidents
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# from app.services.scoring_engine import run_scoring_and_save
from app.services.keyword_extractor import analyze_articles


@app.get("/generate-report")
def generate_final_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    last_24_hours: Optional[bool] = Query(False)
):
    # Step 1: Parse date range
    try:
        if last_24_hours:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=1)
        elif start_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else start_dt
        else:
            raise HTTPException(status_code=400, detail="Provide either 'last_24_hours' or 'start_date'")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Step 2: Fetch news images from database
    conn = get_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="DB connection failed")

    cursor = conn.cursor()
    query = """
        SELECT UPLOAD_ID, LANG_CD, UPLOADED_IMAGE, RECORD_CREATED_ON
        FROM t_news_upload
        WHERE RECORD_CREATED_ON BETWEEN %s AND %s
    """
    cursor.execute(query, (start_dt, end_dt))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Extract articles from news images
    articles = []
    for upload_id, _lang_cd, image_blob, _created_on in rows:
        if image_blob:
            try:
                image_base64 = base64.b64encode(image_blob).decode('utf-8') # type: ignore
                structured_articles = process_base64_images(image_base64)
                if structured_articles:
                    articles.extend(structured_articles)
            except Exception as e:
                print(f"Error processing news image {upload_id}: {str(e)}")
                continue

    if not articles:
        raise HTTPException(status_code=404, detail="No news articles found.")

    all_info_2d_list = analyze_articles(articles)

    # Step 3: Compute FIR time range (7 days back from start)
    fir_start = start_dt - timedelta(days=7)
    fir_end = end_dt

    # Step 4: Fetch FIR records directly from database
    conn_fir = get_connection()
    if not conn_fir:
        raise HTTPException(status_code=500, detail="Database connection failed")

    cursor_fir = conn_fir.cursor()
    fir_query = """
        SELECT FIR_REG_NUM, STATE_CD, DISTRICT_CD, PS_CD, REG_DT, FIR_CONTENTS
        FROM t_fir_registration
        WHERE REG_DT BETWEEN %s AND %s
    """
    cursor_fir.execute(fir_query, (fir_start, fir_end))
    fir_list = cursor_fir.fetchall()
    cursor_fir.close()
    conn_fir.close()

    # Step 4: Extract keywords from FIR contents
    fir_texts = [
        item["FIR_CONTENTS"].strip()
        for item in fir_list
        if item.get("FIR_CONTENTS") and len(item["FIR_CONTENTS"].strip()) > 30
    ]
    fir_info_2d_list = analyze_articles(fir_texts) if fir_texts else []

    # Step 5: Load law_hi
    law_hi = get_law_hi()
    

    # Step 6: Define crime mappings
    crime_severity_sorted = {
        'शराब तस्करी': 6, 'जुआ': 2, 'गौ हत्या': 6, 'गौ तस्करी': 5, 'नशीली दवाओं की तस्करी': 9, 'हथियारों की तस्करी': 9,
        'मादक पदार्थ तस्करी': 9, 'अवैध हथियार रखना': 8, 'एनडीपीएस': 8, 'मादक पदार्थ': 7, 'वन्यजीव तस्करी': 7,
        'अवैध उत्पादों की तस्करी': 7, 'फेंटेनिल': 4, 'एमडी ड्रग': 4, 'मेफेड्रोन': 4, 'कोकीन': 4, 'ब्राउन शुगर': 4,
        'हेरोइन': 4, 'गांजा': 4, 'धार्मिक उन्माद': 7, 'नकली नोट': 7, 'आतंकवाद': 10, 'देशद्रोह': 10, 'माओवाद': 9,
        'नक्सली': 9, 'नक्सलवाद': 9, 'पुनर्वास नीति': 2, 'साइबर अपराध': 6, 'डिजिटल गिरफ्तारी': 2, 'साइबर धोखाधड़ी': 6,
        'डकैती': 9, 'लूट': 8, 'गृहभेदन': 6, 'धोखाधड़ी': 6, 'चोरी': 5, 'ठगी': 5, 'सांप्रदायिक हत्या': 6, 'हत्या': 10,
        'बलात्कार': 10, 'दुष्कर्म': 10, 'मानव तस्करी': 10, 'नाबालिग से दुष्कर्म': 10, 'हत्या का प्रयास': 9,
        'बलात्कार का प्रयास': 9, 'अपहरण': 8, 'घरेलू हिंसा': 4, 'आत्महत्या के लिए उकसाना': 4, 'छेड़छाड़': 6,
        'मारपीट': 6, 'पत्नि पर अत्याचार': 7, 'धमकी देना': 5, 'ईनामी': 0, 'अवैध परिवहन': 0, 'बिक्री': 0, 'आत्मसमर्पण': 0
    }
    crime_type_hi = [
        "हत्या", "हत्या का प्रयास", "बलात्कार", "बलात्कार का प्रयास", "छेड़छाड़", "दुष्कर्म", "अपहरण", "डकैती", "लूट", "चोरी",
        "गृहभेदन", "मारपीट", "धोखाधड़ी", "ठगी", "घूसखोरी", "साइबर अपराध", "नकली नोट", "नशीली दवाओं की तस्करी", "शराब तस्करी",
        "मानव तस्करी", "घरेलू हिंसा", "आतंकवाद", "देशद्रोह", "धार्मिक उन्माद", "नाबालिग से दुष्कर्म", "पत्नि पर अत्याचार",
        "आत्महत्या के लिए उकसाना", "धमकी देना", "अवैध हथियार रखना", "हथियारों की तस्करी", "जुआ", "मादक पदार्थ तस्करी",
        "नशीली दवाओं की तस्करी", "तस्करी", "नक्सली", "आत्मसमर्पण", "ईनामी", "पुनर्वास नीति", "माओवाद", "गांजा", "मादक पदार्थ",
        "एनडीपीएस", "बिक्री", "अवैध परिवहन", "नक्सलवाद", "देशद्रोह", "गौ हत्या", "गौ तस्करी"
    ]

    # Step 7: Final scoring using FIR extracted keywords
    from app.services.scoring_engine import run_scoring_and_save_keywords

    report_data = run_scoring_and_save_keywords(
        fir_info_2d_list,             # FIR keywords 2D
        all_info_2d_list,             # News keywords 2D
        law_hi,
        crime_type_hi,
        crime_severity_sorted
    )


    return {
        "message": "Report generation complete",
        "total": len(report_data)
    }


@app.get("/extract-local-newspaper")
def extract_local_newspaper():
    """
    Extract articles from the local newspaper.jpg file in app/services/
    Returns extracted text and base64 encoded image
    """
    try:
        # Get the path to the newspaper.jpg file
        current_dir = Path(__file__).parent
        image_path = current_dir / "services" / "newspaper4.jpg"

        if not image_path.exists():
            raise HTTPException(status_code=404, detail=f"Image file not found at {image_path}")

        # Read the image file and convert to base64
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        # Process the image using OCR
        structured_articles = process_base64_images(image_base64)

        # Debug: Print extracted text
        print("=" * 80)
        print("EXTRACTED TEXT FROM OCR:")
        if structured_articles and len(structured_articles) > 0:
            print(structured_articles[0])
        else:
            print("No text extracted!")
        print("=" * 80)

        # Check if OCR extracted any text
        if not structured_articles or len(structured_articles) == 0 or not structured_articles[0].strip():
            return {
                "success": False,
                "error": "OCR failed to extract text from image",
                "image_path": str(image_path),
                "image_base64": image_base64,
                "extracted_data": {
                    "districtCode": "N/A",
                    "districtName": "N/A",
                    "policeStation": "N/A",
                    "accusedName": "N/A",
                    "complainantName": "N/A",
                    "crimeType": "N/A",
                    "newsHeading": "N/A",
                    "summary": "N/A",
                    "fullText": ""
                }
            }

        # Extract information from the articles
        crimeType = extract_crime_keywords(structured_articles)
        psName = extract_police_station(structured_articles[0])
        accusedName = extract_accused(structured_articles[0])
        complainantName = extract_complainant(structured_articles[0])
        dsName = extract_district(structured_articles[0])

        # Debug: Print extracted information
        print(f"Crime Type: {crimeType}")
        print(f"Police Station: {psName}")
        print(f"Accused Name: {accusedName}")
        print(f"Complainant Name: {complainantName}")
        print(f"District Name: {dsName}")

        # Get district code
        try:
            distictCode = get_district_Code(33, dsName)
            district_cd = distictCode.get('DISTRICT_CD', 'N/A')
        except Exception as e:
            print(f"Error getting district code: {e}")
            district_cd = 'N/A'

        # Generate heading and summary
        heading, summary = extract_summary_string(accusedName, psName, complainantName, '', dsName, crimeType)

        return {
            "success": True,
            "image_path": str(image_path),
            "image_base64": image_base64,
            "extracted_data": {
                "districtCode": district_cd,
                "districtName": dsName,
                "policeStation": psName,
                "accusedName": accusedName,
                "complainantName": complainantName,
                "crimeType": crimeType,
                "newsHeading": heading,
                "summary": summary,
                "fullText": structured_articles[0] if structured_articles else ""
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
