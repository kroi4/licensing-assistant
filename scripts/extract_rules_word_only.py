#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL Script: Extract restaurant licensing rules from Word document ONLY
This script processes ONLY the Word document to avoid Hebrew text reversal issues from PDF
"""

import json
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File paths
INPUT_DOCX = Path("data/raw/18-07-2022_4.2A.docx")
OUTPUT_BACKEND = Path("backend/rules/restaurant_rules.json")

def extract_sections_from_docx(docx_path: Path) -> List[Dict[str, Any]]:
    """
    Extract sections from Word document using python-docx
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

def detect_chapter_from_content(content: str) -> Optional[str]:
    """Detect regulatory chapter from content"""
    content_lower = content.lower()
    
    # Look for chapter indicators
    if "משטרת ישראל" in content or "משטרה" in content:
        return "police"
    elif "משרד הבריאות" in content or "בריאות" in content:
        return "health"
    elif "כבאות והצלה" in content:
        if "תצהיר" in content:
            return "fire_affidavit"
        else:
            return "fire_full"
    elif "גז" in content or "גפ\"מ" in content:
        return "gas"
    
    return "general"

def is_meaningful_regulatory_content(text: str) -> bool:
    """Check if text contains meaningful regulatory content"""
    if len(text.strip()) < 10:
        return False
    
    # Skip table of contents, page numbers, headers
    skip_patterns = [
        r"^תוכן עניינים",
        r"^עמוד \d+",
        r"^\d+$",
        r"^\.{3,}",
        r"^מפרט אחיד לפריט",
        r"^הערה:",
        r"^פרק \d+ -",
    ]
    
    for pattern in skip_patterns:
        if re.match(pattern, text.strip()):
            return False
    
    # Look for regulatory indicators
    regulatory_indicators = [
        "אישור", "רישיון", "חובה", "דרישה", "תקנה", "חוק",
        "משטרת ישראל", "משרד הבריאות", "כבאות והצלה",
        "מ\"ר", "מקומות ישיבה", "עובדים", "מטבח", "מזון",
        "בטיחות", "בריאות", "היגיינה", "נגישות"
    ]
    
    return any(indicator in text for indicator in regulatory_indicators)

def extract_conditions_from_text(text: str) -> Dict[str, Any]:
    """Extract business conditions from regulatory text"""
    conditions = {}
    
    # Look for area thresholds (square meters)
    area_matches = re.findall(r'(\d+)\s*מ[״"]*ר', text)
    if area_matches:
        areas = [int(a) for a in area_matches]
        if any(area <= 150 for area in areas):
            conditions["area_max"] = 150
        elif any(area > 150 for area in areas):
            conditions["area_min"] = 151
    
    # Look for capacity thresholds
    capacity_matches = re.findall(r'(\d+)\s*מקומות?\s+ישיבה', text)
    if capacity_matches:
        capacities = [int(c) for c in capacity_matches]
        if any(cap <= 50 for cap in capacities):
            conditions["seats_max"] = 50
        elif any(cap > 50 for cap in capacities):
            conditions["seats_min"] = 51
    
    # Look for employee thresholds
    employee_matches = re.findall(r'(\d+)\s*עובדים?', text)
    if employee_matches:
        employees = [int(e) for e in employee_matches]
        conditions["employees_min"] = min(employees)
    
    # Look for feature requirements
    features = []
    if re.search(r'גז|גפ[״"]*מ', text):
        features.append("gas")
    if re.search(r'משלוח|שליחת?\s+מזון', text):
        features.append("delivery")
    if re.search(r'אלכוהול|משקאות?\s+משכרים?', text):
        features.append("alcohol")
    if re.search(r'בשר|עופות?|דגים?', text):
        features.append("meat_and_fish")
    if re.search(r'מנדפים?|אוורור', text):
        features.append("hood")
    
    if features:
        conditions["features_any"] = features
    
    return conditions

def create_rule_from_paragraph(paragraph: str, chapter: str, rule_id: str, section_heading: str = None) -> Optional[Dict[str, Any]]:
    """Create a structured rule from a paragraph"""
    
    # Clean the text
    cleaned_text = paragraph.strip()
    if len(cleaned_text) < 15:
        return None
    
    # Skip if not meaningful regulatory content
    if not is_meaningful_regulatory_content(cleaned_text):
        return None
    
    # Determine category based on chapter
    category_map = {
        'health': 'משרד הבריאות',
        'police': 'משטרת ישראל', 
        'fire_affidavit': 'כבאות והצלה (תצהיר)',
        'fire_full': 'כבאות והצלה',
        'gas': 'גז (גפ"מ)',
        'general': 'רגולטורי כללי'
    }
    
    category = category_map.get(chapter, 'רגולטורי')
    
    # Extract conditions from content
    conditions = extract_conditions_from_text(cleaned_text)
    
    # Create title (first 80 characters)
    title = cleaned_text[:80] + "..." if len(cleaned_text) > 80 else cleaned_text
    
    # Create the rule
    rule = {
        "id": rule_id,
        "category": category,
        "title": title,
        "status": "חובה",
        "note": f"מחולץ מקובץ Word - {section_heading or 'כללי'}",
        "section_ref": cleaned_text,
        "if": conditions,
        "source": "word_extraction"
    }
    
    return rule

def extract_rules_from_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract structured rules from document sections"""
    rules = []
    rule_counter = 1
    
    for section in sections:
        heading = section.get("heading", "")
        paragraphs = section.get("paragraphs", [])
        
        # Detect chapter from section content
        all_content = (heading or "") + " " + " ".join(paragraphs)
        chapter = detect_chapter_from_content(all_content)
        
        logger.debug(f"Processing section '{heading}' as chapter '{chapter}'")
        
        # Process each paragraph as a potential rule
        for paragraph in paragraphs:
            rule_id = f"{chapter}-{rule_counter}"
            rule = create_rule_from_paragraph(paragraph, chapter, rule_id, heading)
            
            if rule:
                rules.append(rule)
                rule_counter += 1
    
    logger.info(f"Created {len(rules)} rules from document sections")
    return rules

def save_rules_to_json(rules: List[Dict[str, Any]], output_path: Path) -> bool:
    """Save rules to JSON file"""
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save rules
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(rules)} rules to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving rules to {output_path}: {e}")
        return False

def calculate_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of file"""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.warning(f"Error calculating hash for {file_path}: {e}")
        return "unknown"

def main():
    """Main ETL process - Word document only"""
    logger.info("Starting ETL process: Word document ONLY → JSON rules")
    logger.info("="*70)
    logger.info("Processing Word document to avoid Hebrew text reversal from PDF")
    logger.info("="*70)
    
    # Check if Word document exists
    if not INPUT_DOCX.exists():
        logger.error(f"Word document not found: {INPUT_DOCX}")
        return False
    
    # Extract sections from Word document
    logger.info(f"Processing Word document: {INPUT_DOCX}")
    sections = extract_sections_from_docx(INPUT_DOCX)
    
    if not sections:
        logger.error("No sections extracted from Word document")
        return False
    
    logger.info(f"Successfully extracted {len(sections)} sections from Word document")
    
    # Extract rules from sections
    logger.info("Extracting rules from document content...")
    rules = extract_rules_from_sections(sections)
    
    if not rules:
        logger.error("No rules could be extracted from the document!")
        return False
    
    # Save rules to JSON
    if not save_rules_to_json(rules, OUTPUT_BACKEND):
        return False
    
    # Generate metadata
    metadata = {
        "extraction_date": "2025-09-14",
        "source_documents": ["Word document only"],
        "total_rules": len(rules),
        "static_rules": 0,
        "dynamic_rules": len(rules),
        "categories": list(set(rule["category"] for rule in rules)),
        "source_file_hash": calculate_file_hash(INPUT_DOCX),
        "extraction_method": "word_only_clean_hebrew"
    }
    
    # Display results
    logger.info("\n" + "="*70)
    logger.info("EXTRACTION COMPLETED SUCCESSFULLY")
    logger.info("="*70)
    logger.info(f"📄 Source: Word document only (clean Hebrew text)")
    logger.info(f"📊 Total rules extracted: {metadata['total_rules']}")
    logger.info(f"🏷️  Categories found: {len(metadata['categories'])}")
    for category in metadata['categories']:
        count = sum(1 for rule in rules if rule['category'] == category)
        logger.info(f"   • {category}: {count} rules")
    logger.info(f"💾 Output: {OUTPUT_BACKEND}")
    logger.info(f"🔍 Source hash: {metadata['source_file_hash'][:8]}...")
    
    # Show sample rules
    logger.info("\n📋 SAMPLE RULES (first 3):")
    for i, rule in enumerate(rules[:3], 1):
        logger.info(f"{i}. [{rule['category']}] {rule['title']}")
    
    logger.info("\n✅ ETL process completed successfully!")
    logger.info("Hebrew text should now be clean and readable in the UI.")
    
    return True

if __name__ == "__main__":
    main()
