#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Word Document Extraction
Tests if extracting from Word document produces better Hebrew text
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def main():
    """Test Word document extraction"""
    docx_path = Path("data/raw/18-07-2022_4.2A.docx")
    
    if not docx_path.exists():
        logger.error(f"Word document not found: {docx_path}")
        return
    
    logger.info("Testing Word document extraction...")
    sections = extract_sections_from_docx(docx_path)
    
    if not sections:
        logger.error("No sections extracted from Word document")
        return
    
    logger.info(f"Successfully extracted {len(sections)} sections from Word document")
    
    # Display first few sections to check Hebrew text quality
    logger.info("\n=== SAMPLE SECTIONS FROM WORD DOCUMENT ===")
    for i, section in enumerate(sections[:5]):
        logger.info(f"\nSection {i+1}:")
        if section.get("heading"):
            logger.info(f"  Heading: {section['heading']}")
        
        paragraphs = section.get("paragraphs", [])
        if paragraphs:
            logger.info(f"  Paragraphs ({len(paragraphs)}):")
            for j, para in enumerate(paragraphs[:3]):  # Show first 3 paragraphs
                logger.info(f"    {j+1}. {para}")
            if len(paragraphs) > 3:
                logger.info(f"    ... and {len(paragraphs) - 3} more paragraphs")
    
    # Look for specific Hebrew text patterns
    logger.info("\n=== HEBREW TEXT ANALYSIS ===")
    hebrew_samples = []
    
    for section in sections:
        if section.get("heading") and any(c in section["heading"] for c in "אבגדהוזחטיכלמנסעפצקרשת"):
            hebrew_samples.append(("Heading", section["heading"]))
        
        for para in section.get("paragraphs", []):
            if any(c in para for c in "אבגדהוזחטיכלמנסעפצקרשת"):
                hebrew_samples.append(("Paragraph", para))
                if len(hebrew_samples) >= 10:  # Limit samples
                    break
        
        if len(hebrew_samples) >= 10:
            break
    
    for i, (type_name, text) in enumerate(hebrew_samples):
        logger.info(f"{i+1}. {type_name}: {text[:100]}...")
    
    # Save sample for comparison
    sample_data = {
        "source": "Word document",
        "total_sections": len(sections),
        "hebrew_samples": [{"type": t, "text": txt} for t, txt in hebrew_samples[:5]]
    }
    
    with open("word_extraction_sample.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\nSample data saved to word_extraction_sample.json")

if __name__ == "__main__":
    main()
