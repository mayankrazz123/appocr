from datetime import datetime
import pandas as pd

def generate_CCTNS_report(record):
    fir_id = record['प्राथमिकी संख्या']
    accused_name = record.get('गिरफ्तार व्यक्ति का नाम', 'नाम उपलब्ध नहीं')
    fir_date = pd.to_datetime(record.get('वास्तविक दिनांक और समय (एफआईआर)'), errors='coerce')
    fir_date_str = fir_date.strftime("%d %B %Y") if pd.notnull(fir_date) else "अज्ञात तिथि"
    section = record.get('अधिनियम- धारा', 'अनिर्दिष्ट अधिनियम')
    victim_name = record.get('पीड़ित का नाम', 'नाम उपलब्ध नहीं')
    district = record.get('ज़िला', 'ज़िला उपलब्ध नहीं')
    police_station = record.get('थाना', 'थाना उपलब्ध नहीं')
    heading = f"{district},  {police_station}___{fir_date_str}___प्राथमिकी संख्या {fir_id}"
    summary = (
        f"{accused_name} को {section} के अंतर्गत एक मामला दर्ज किया गया। "
        f"पीड़ित का नाम {victim_name} है "
        f"यह रिपोर्ट अखबारों में भी छपी है।"
    )
    return heading, summary

def Gruesome_check(row, law_hi, crime_type_hi, crime_severity_sorted):
    section = row.get('अधिनियम- धारा', '')
    accused = row.get('गिरफ्तार व्यक्ति का नाम', '')
    victim = row.get('पीड़ित का नाम', '')
    accused_count = len(accused.split(',')) if accused else 0
    victim_count = len(victim.split(',')) if victim else 0
    if any(str(law) in section for law in law_hi):
        return True
    if accused_count >= 4 or victim_count >= 4:
        return True
    return False

def run_scoring_and_save_keywords(fir_keywords_list, news_info, law_hi, crime_type_hi, crime_severity_sorted):
    # Import here to avoid circular dependency
    from app.news_app import SummaryData, save_summary
    complete = []
    used_news_indexes = set()

    for i, fir_keywords in enumerate(fir_keywords_list):
        best_score = 0
        best_index = -1

        for j, news_keywords in enumerate(news_info):
            if j in used_news_indexes:
                continue

            score = 0
            fir_kw_set = set(fir_keywords[7].split(','))
            news_kw_set = set(news_keywords[7].split(','))
            overlap = fir_kw_set.intersection(news_kw_set)
            score += len(overlap) * 2

            if fir_keywords[6] and fir_keywords[6] in news_keywords[6]:
                score += 1
            if fir_keywords[11] == news_keywords[11]:
                score += 2

            if score > best_score:
                best_score = score
                best_index = j

        if best_index != -1:
            used_news_indexes.add(best_index)
            matched = news_info[best_index]
            heading = matched[9]
            summary = matched[10]

            save_summary(SummaryData(**{
                "date": matched[2],
                "district": matched[1],
                "police_station": matched[0],
                "fir_number": matched[3],
                "complainant": matched[4],
                "accused": matched[5],
                "weapon": matched[6],
                "crime_type": matched[7],
                "score": best_score,
                "crime_category": matched[11],
                "heading": heading,
                "summary": summary + f"\nयह मामला अखबार के अनुसार दिनांक {matched[2]} का है।"
            }))
            complete.append([heading, summary, best_score])

    for i, info in enumerate(news_info):
        if i not in used_news_indexes:
            save_summary(SummaryData(**{
                "date": info[2],
                "district": info[1],
                "police_station": info[0],
                "fir_number": info[3],
                "complainant": info[4],
                "accused": info[5],
                "weapon": info[6],
                "crime_type": info[7],
                "score": info[8],
                "crime_category": info[11],
                "heading": info[9],
                "summary": info[10]
            }))
            complete.append([info[9], info[10], info[8]])

    return complete

