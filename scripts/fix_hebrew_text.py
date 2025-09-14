#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hebrew Text Direction Fix Utility
Fixes reversed Hebrew text from PDF extraction
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_reversed_hebrew_word(word: str) -> str:
    """
    Fix a single Hebrew word that appears reversed
    
    Args:
        word: The potentially reversed Hebrew word
        
    Returns:
        The corrected word
    """
    if not word or not re.search(r'[א-ת]', word):
        return word
    
    # Don't reverse very short words or words with punctuation at the end
    if len(word) <= 2:
        return word
    
    # Don't reverse if it ends with punctuation (likely correct)
    if word[-1] in '.,:;!?()[]{}':
        return word
    
    # Don't reverse if it starts with punctuation (likely correct)
    if word[0] in '([{':
        return word
    
    # Check if word seems reversed by looking for common Hebrew patterns
    # If it starts with final letters (ך,ם,ן,ף,ץ) it's likely reversed
    if word[0] in 'ךםןףץ':
        return word[::-1]
    
    # If it ends with letters that shouldn't be at the end, it's likely reversed
    if len(word) > 3 and word[-1] in 'בגדהוזחטיכלמנספצקרשת':
        # Check if reversing makes more sense
        reversed_word = word[::-1]
        if reversed_word[0] not in 'ךםןףץ':  # Final letters shouldn't be at start
            return reversed_word
    
    return word

def fix_reversed_hebrew_text(text: str) -> str:
    """
    Fix reversed Hebrew text from PDF extraction
    
    Args:
        text: The text that may contain reversed Hebrew
        
    Returns:
        The corrected text
    """
    if not text or not re.search(r'[א-ת]', text):
        return text
    
    # Split into words and fix each Hebrew word
    words = text.split()
    fixed_words = []
    
    for word in words:
        if re.search(r'[א-ת]', word):
            fixed_word = fix_reversed_hebrew_word(word)
            fixed_words.append(fixed_word)
        else:
            fixed_words.append(word)
    
    result = ' '.join(fixed_words)
    
    # Additional fixes for common patterns
    # Fix reversed common phrases
    result = re.sub(r'הז ןיינעל', 'לענין זה', result)
    result = re.sub(r'ךימסה אוהש רחא', 'אחר שהוא הסמיך', result)
    result = re.sub(r'הלצהו תואבכ', 'כבאות והצלה', result)
    result = re.sub(r'לארשי תרטשמ', 'משטרת ישראל', result)
    result = re.sub(r'תואירבה דרשמ', 'משרד הבריאות', result)
    result = re.sub(r'קסע ןיינעל', 'לענין עסק', result)
    result = re.sub(r'רושיא תתל', 'לתת אישור', result)
    result = re.sub(r'וכימסה םהש ימ', 'מי שהם הסמיכו', result)
    result = re.sub(r'ןוישיר', 'רישיון', result)
    result = re.sub(r'ןיצק', 'קצין', result)
    result = re.sub(r'ביצנ', 'נציב', result)
    result = re.sub(r'חקפמה', 'המפקח', result)
    result = re.sub(r'יללכה', 'הכללי', result)
    
    return result.strip()

def fix_rules_json(input_path: Path, output_path: Path) -> bool:
    """
    Fix Hebrew text direction in rules JSON file
    
    Args:
        input_path: Path to input JSON file
        output_path: Path to output JSON file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Loading rules from {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        logger.info(f"Loaded {len(rules)} rules")
        
        fixed_count = 0
        for rule in rules:
            original_title = rule.get('title', '')
            original_note = rule.get('note', '')
            original_section_ref = rule.get('section_ref', '')
            
            # Fix title
            if 'title' in rule:
                fixed_title = fix_reversed_hebrew_text(rule['title'])
                if fixed_title != original_title:
                    rule['title'] = fixed_title
                    fixed_count += 1
            
            # Fix note (but preserve "מחולץ מעמוד X של המסמך הרגולטורי")
            if 'note' in rule and not rule['note'].startswith('מחולץ מעמוד'):
                fixed_note = fix_reversed_hebrew_text(rule['note'])
                if fixed_note != original_note:
                    rule['note'] = fixed_note
            
            # Fix section_ref
            if 'section_ref' in rule:
                fixed_section_ref = fix_reversed_hebrew_text(rule['section_ref'])
                if fixed_section_ref != original_section_ref:
                    rule['section_ref'] = fixed_section_ref
        
        logger.info(f"Fixed {fixed_count} rules with reversed Hebrew text")
        
        # Save fixed rules
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved fixed rules to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing rules: {e}")
        return False

def main():
    """Main function to fix Hebrew text in rules"""
    input_file = Path("backend/rules/restaurant_rules.json")
    output_file = Path("backend/rules/restaurant_rules_fixed.json")
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} not found")
        return
    
    # Fix the rules
    if fix_rules_json(input_file, output_file):
        logger.info("Hebrew text fixing completed successfully")
        
        # Replace the original file with the fixed version
        import shutil
        shutil.move(str(output_file), str(input_file))
        logger.info("Original file replaced with fixed version")
        
        # Test a few examples
        with open(input_file, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        logger.info("\n=== SAMPLE FIXED RULES ===")
        for i, rule in enumerate(rules[:3]):
            logger.info(f"{i+1}. {rule.get('category', '')}")
            logger.info(f"   Title: {rule.get('title', '')}")
            logger.info(f"   Note: {rule.get('note', '')}")
            logger.info("")
            
    else:
        logger.error("Failed to fix Hebrew text")

if __name__ == "__main__":
    main()
