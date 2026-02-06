
import os
import sys
from dotenv import load_dotenv

# Ensure the current directory is in the path so we can import app modules
sys.path.append(os.getcwd())

load_dotenv()

def test_integration():
    print("Testing IndicNER Integration...")
    
    # 1. Test the keyword_extractor directly
    try:
        from app.services.keyword_extractor import extract_entities_with_ner
        print("Successfully imported extract_entities_with_ner")
    except ImportError as e:
        print(f"Failed to import: {e}")
        return

    # Test with the user's example (English)
    text_en = "My name is Sarah Jessica Parker but you can call me Jessica"
    print(f"\nTesting with English text: '{text_en}'")
    results_en = extract_entities_with_ner(text_en)
    print(f"Results: {results_en}")

    # Test with Hindi text (Relevant for the app)
    text_hi = "आरोपी रमेश कुमार को पुलिस ने गिरफ्तार किया।" # Accused Ramesh Kumar was arrested by police.
    print(f"\nTesting with Hindi text: '{text_hi}'")
    results_hi = extract_entities_with_ner(text_hi)
    print(f"Results: {results_hi}")

    # 2. Test the fallback logic in news_app (simulated)
    # We won't import the whole news_app to avoid side effects like DB connections if possible,
    # but we can simulate the logic we injected.
    
    print("\nSimulating extract_accused fallback logic...")
    persons = []
    if results_hi:
        for ent in results_hi:
            label = ent.get('entity_group') or ent.get('entity')
            # IndicNER often returns B-PER, I-PER. HuggingFace 'simple' aggregation returns entity_group='PER'
            # If aggregation is off, we get 'B-PER', etc.
            if label and 'PER' in label:
                persons.append(ent.get('word', ''))
    
    print(f"Extracted Persons from Hindi text: {persons}")
    if "रमेश कुमार" in persons or "रमेश" in " ".join(persons): 
        print("SUCCESS: Found Ramesh in extracted entities.")
    else:
        print("WARNING: Ramesh not found or model behavior differs.")

if __name__ == "__main__":
    test_integration()
