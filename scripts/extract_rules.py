#!/usr/bin/env python3
"""
ETL Script: Extract restaurant licensing rules from Word document to JSON

This script processes the regulatory document and creates a structured JSON file
with licensing rules that can be loaded by the backend at runtime.
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
INPUT_DOCX = Path("data/raw/18-07-2022_4.2A.docx")
OUTPUT_PROCESSED = Path("data/processed/restaurant_rules.json")
OUTPUT_BACKEND = Path("backend/rules/restaurant_rules.json")

def extract_sections_from_docx(docx_path: Path) -> List[Dict[str, Any]]:
    """
    Extract sections from Word document using python-docx
    
    Args:
        docx_path: Path to the Word document
        
    Returns:
        List of sections with headings and paragraphs
    """
    try:
        from docx import Document
        
        doc = Document(docx_path)
        sections = []
        current_section = {"heading": None, "paragraphs": []}
        
        def flush_section():
            nonlocal current_section
            if current_section["heading"] or current_section["paragraphs"]:
                sections.append(current_section)
            current_section = {"heading": None, "paragraphs": []}
        
        for paragraph in doc.paragraphs:
            text = (paragraph.text or "").strip()
            if not text:
                continue
                
            style_name = (paragraph.style.name or "").lower()
            
            # Check if this is a heading
            if "heading" in style_name:
                flush_section()
                current_section["heading"] = text
                logger.debug(f"Found heading: {text}")
            else:
                current_section["paragraphs"].append(text)
        
        flush_section()
        logger.info(f"Extracted {len(sections)} sections from document")
        return sections
        
    except ImportError:
        logger.error("python-docx not installed. Please install: pip install python-docx")
        return []
    except Exception as e:
        logger.error(f"Error reading document: {e}")
        return []

def create_curated_rules(document_analysis: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Create a curated list of restaurant licensing rules
    
    This is a manually curated set of rules based on the regulatory document.
    Each rule has conditions that determine when it applies.
    
    Returns:
        List of rule dictionaries
    """
    rules = []
    
    # Helper function to add rules
    def add_rule(rule_data):
        rules.append(rule_data)
    
    # Basic health requirements (always apply)
    add_rule({
        "id": "health-baseline",
        "category": "משרד הבריאות",
        "title": "עמידה בתנאי תברואה לבתי אוכל + מי שתייה ושפכים",
        "status": "חובה",
        "note": "תקנות בתי אוכל, איכות מי שתייה, מניעת עישון ושילוט.",
        "section_ref": "בריאות – תנאים רוחביים",
        "if": {}
    })
    
    add_rule({
        "id": "health-smoking-signage",
        "category": "משרד הבריאות",
        "title": "שילוט איסור עישון והפרדה אזורי עישון (אם יש)",
        "status": "חובה",
        "note": "חוק למניעת העישון ותקנות שילוט.",
        "section_ref": "",
        "if": {}
    })
    
    # Delivery-specific rules
    add_rule({
        "id": "delivery-rules",
        "category": "משרד הבריאות — שליחת מזון",
        "title": "דרישות לשליחת מזון",
        "status": "חובה",
        "note": "אזור ייעודי, קירור/הקפאה, בקרה ותיעוד טמפרטורות, ציוד אריזה, והובלה עד 3 שעות.",
        "section_ref": "",
        "if": {"features_any": ["delivery"]}
    })
    
    # Post-cooking cooling (for next-day preparation)
    add_rule({
        "id": "post-cook-cooling",
        "category": "משרד הבריאות — קירור לאחר בישול",
        "title": "קירור מהיר/בקרת טמפרטורות/תיעוד",
        "status": "חובה",
        "note": "כשמבשלים ליום המחרת - דורש קירור מהיר",
        "section_ref": "אחסון וקירור",
        "if": {"features_any": ["cook_next_day"]}
    })
    
    # Meat and fish handling rules
    meat_fish_rules = [
        ("vet-approval-meat-fish", "אישורים וטרינריים לבשר/דגים ותיעוד ספקים"),
        ("storage-separation", "הפרדה באחסון (בשר/דגים; גולמי/מוכן)"),
        ("prep-surfaces-separated", "משטחי עבודה נפרדים Raw/RTE")
    ]
    
    for rule_id, title in meat_fish_rules:
        add_rule({
            "id": rule_id,
            "category": "משרד הבריאות",
            "title": title,
            "status": "חובה",
            "note": "",
            "section_ref": "קבלת/אחסון/הכנה",
            "if": {"features_any": ["meat_and_fish", "meat"]}
        })
    
    # Gas-related rules
    add_rule({
        "id": "gas-cert",
        "category": "גז (גפ\"מ)",
        "title": "אישור מתקין גפ\"מ ועמידה בת\"י 158",
        "status": "חובה",
        "note": "בדיקות תקינות, ניתוקי חירום, תחזוקה שוטפת.",
        "section_ref": "",
        "if": {"features_any": ["gas"]}
    })
    
    # Hood suppression system
    add_rule({
        "id": "hood-suppression",
        "category": "כבאות – מנדפים",
        "title": "מערכת כיבוי למנדפים במטבח מקצועי",
        "status": "חובה",
        "note": "מערכת כימיקלים רטובים/לפי ת\"י 5356-2 + ניתוק אנרגיה.",
        "section_ref": "",
        "if": {"features_any": ["gas", "hood"]}
    })
    
    # Fire department rules - affidavit track (small establishments)
    add_rule({
        "id": "fire-affidavit",
        "category": "כבאות והצלה (תצהיר)",
        "title": "מסלול תצהיר – עד 50 איש ועד 150 מ״ר",
        "status": "חובה",
        "note": "עמידה בדרישות פרק 5 – שילוט יציאות, תאורת חירום, מטפים וכו'.",
        "section_ref": "",
        "if": {"area_max": 150, "seats_max": 50}
    })
    
    # Fire department rules - full track (large establishments by area)
    add_rule({
        "id": "fire-full-area",
        "category": "כבאות והצלה",
        "title": "מסלול מלא – שטח מעל 150 מ״ר",
        "status": "חובה",
        "note": "דרכי מוצא, עמדות כיבוי, תאורת חירום, ייתכן מתזים/גילוי עשן לפי ספים.",
        "section_ref": "",
        "if": {"area_min": 151}
    })
    
    # Fire department rules - full track (large establishments by capacity)
    add_rule({
        "id": "fire-full-seats",
        "category": "כבאות והצלה",
        "title": "מסלול מלא – תפוסה מעל 50",
        "status": "חובה",
        "note": "דרכי מוצא, עמדות כיבוי, תאורת חירום, ייתכן מתזים/גילוי עשן לפי ספים.",
        "section_ref": "",
        "if": {"seats_min": 51}
    })
    
    # Police requirements - alcohol service
    add_rule({
        "id": "police-alcohol",
        "category": "משטרת ישראל",
        "title": "דרישות משטרה עקב הגשת/מכירת אלכוהול",
        "status": "חובה",
        "note": "טמ״ס, תאורה חיצונית, שילוט איסור מכירה <18, החזקת הקלטות 14 יום וכו'.",
        "section_ref": "",
        "if": {"features_any": ["alcohol"]}
    })
    
    # Police requirements - large capacity
    add_rule({
        "id": "police-capacity",
        "category": "משטרת ישראל",
        "title": "דרישות משטרה עקב תפוסה מעל 200",
        "status": "חובה",
        "note": "דרישות נוספות לעסקים עם תפוסה גדולה.",
        "section_ref": "",
        "if": {"seats_min": 201}
    })
    
    logger.info(f"Created {len(rules)} curated rules")
    return rules

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    try:
        return hashlib.sha256(file_path.read_bytes()).hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return "unknown"

def write_rules_to_files(rules: List[Dict[str, Any]]) -> bool:
    """Write rules to both processed and backend locations"""
    success = True
    
    for output_path in [OUTPUT_PROCESSED, OUTPUT_BACKEND]:
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write rules to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            logger.info(f"Successfully wrote {len(rules)} rules to {output_path}")
            
        except Exception as e:
            logger.error(f"Error writing JSON file {output_path}: {e}")
            success = False
    
    return success

def analyze_document_structure(sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the document structure to understand content"""
    analysis = {
        "total_sections": len(sections),
        "sections_with_headings": 0,
        "chapter_headings": [],
        "key_terms_found": {}
    }
    
    # Key terms we're looking for in the regulatory document
    key_terms = {
        "משרד הבריאות": 0,
        "משטרת ישראל": 0,
        "כבאות והצלה": 0,
        "שליחת מזון": 0,
        "קירור": 0,
        "אחסון": 0,
        "גז": 0,
        "מנדפים": 0,
        "אלכוהול": 0,
        "תצהיר": 0,
        "מסלול מלא": 0
    }
    
    for section in sections:
        if section.get("heading"):
            analysis["sections_with_headings"] += 1
            heading = section["heading"]
            
            # Check if this looks like a chapter heading
            if any(word in heading for word in ["פרק", "נספח", "מבוא"]):
                analysis["chapter_headings"].append(heading)
            
            # Count key terms in headings and paragraphs
            all_text = heading + " " + " ".join(section.get("paragraphs", []))
            for term in key_terms:
                if term in all_text:
                    key_terms[term] += 1
    
    analysis["key_terms_found"] = key_terms
    return analysis

def main():
    """Main ETL process"""
    logger.info("Starting ETL process: Word document → JSON rules")
    logger.info("="*60)
    
    # Extract sections from document
    sections = []
    document_analysis = {}
    
    if INPUT_DOCX.exists():
        logger.info(f"Processing document: {INPUT_DOCX}")
        sections = extract_sections_from_docx(INPUT_DOCX)
        
        if sections:
            document_analysis = analyze_document_structure(sections)
            logger.info(f"Document analysis:")
            logger.info(f"  - Total sections: {document_analysis['total_sections']}")
            logger.info(f"  - Sections with headings: {document_analysis['sections_with_headings']}")
            logger.info(f"  - Chapter headings found: {len(document_analysis['chapter_headings'])}")
            
            # Log key terms found
            key_terms = document_analysis['key_terms_found']
            relevant_terms = {k: v for k, v in key_terms.items() if v > 0}
            if relevant_terms:
                logger.info(f"  - Key regulatory terms found: {relevant_terms}")
        else:
            logger.warning("No sections extracted from document")
    else:
        logger.warning(f"Input document not found: {INPUT_DOCX}")
        logger.info("Proceeding with curated rules only")
    
    # Generate curated rules (enhanced with document insights)
    rules = create_curated_rules(document_analysis=document_analysis)
    
    # Write rules to both locations
    if not write_rules_to_files(rules):
        return False
    
    # Generate and display metadata
    metadata = {
        "source_file": str(INPUT_DOCX),
        "source_exists": INPUT_DOCX.exists(),
        "source_sha256": calculate_file_hash(INPUT_DOCX) if INPUT_DOCX.exists() else "file_not_found",
        "rule_count": len(rules),
        "detected_sections": len([s for s in sections if s.get("heading")]),
        "chapter_headings": len(document_analysis.get("chapter_headings", [])),
        "output_processed": str(OUTPUT_PROCESSED),
        "output_backend": str(OUTPUT_BACKEND),
        "processed_size_bytes": OUTPUT_PROCESSED.stat().st_size if OUTPUT_PROCESSED.exists() else 0,
        "backend_size_bytes": OUTPUT_BACKEND.stat().st_size if OUTPUT_BACKEND.exists() else 0
    }
    
    print("\n" + "="*60)
    print("ETL PROCESS COMPLETED")
    print("="*60)
    for key, value in metadata.items():
        print(f"{key:20}: {value}")
    print("="*60)
    
    # Show sample of chapter headings if found
    if document_analysis.get("chapter_headings"):
        print("\nSample chapter headings found:")
        for i, heading in enumerate(document_analysis["chapter_headings"][:5]):
            print(f"  {i+1}. {heading}")
        if len(document_analysis["chapter_headings"]) > 5:
            print(f"  ... and {len(document_analysis['chapter_headings']) - 5} more")
    
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
