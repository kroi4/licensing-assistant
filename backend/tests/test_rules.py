#!/usr/bin/env python3
"""
Basic tests for restaurant rules matching logic

These tests verify that the rule matching engine works correctly
for various business configurations.
"""

import sys
import os
import json
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import rule_matches, evaluate_restaurant, load_restaurant_rules

def test_rule_matching():
    """Test individual rule matching logic"""
    print("Testing rule matching logic...")
    
    # Test area constraints
    rule_area_max = {"if": {"area_max": 150}}
    assert rule_matches(rule_area_max["if"], {"area": 120, "seats": 30, "features": []})
    assert not rule_matches(rule_area_max["if"], {"area": 200, "seats": 30, "features": []})
    
    rule_area_min = {"if": {"area_min": 151}}
    assert rule_matches(rule_area_min["if"], {"area": 200, "seats": 30, "features": []})
    assert not rule_matches(rule_area_min["if"], {"area": 120, "seats": 30, "features": []})
    
    # Test seats constraints
    rule_seats_max = {"if": {"seats_max": 50}}
    assert rule_matches(rule_seats_max["if"], {"area": 100, "seats": 45, "features": []})
    assert not rule_matches(rule_seats_max["if"], {"area": 100, "seats": 60, "features": []})
    
    rule_seats_min = {"if": {"seats_min": 51}}
    assert rule_matches(rule_seats_min["if"], {"area": 100, "seats": 60, "features": []})
    assert not rule_matches(rule_seats_min["if"], {"area": 100, "seats": 45, "features": []})
    
    # Test feature constraints
    rule_features_any = {"if": {"features_any": ["gas", "delivery"]}}
    assert rule_matches(rule_features_any["if"], {"area": 100, "seats": 30, "features": ["gas"]})
    assert rule_matches(rule_features_any["if"], {"area": 100, "seats": 30, "features": ["delivery"]})
    assert rule_matches(rule_features_any["if"], {"area": 100, "seats": 30, "features": ["gas", "delivery"]})
    assert not rule_matches(rule_features_any["if"], {"area": 100, "seats": 30, "features": ["alcohol"]})
    
    rule_features_all = {"if": {"features_all": ["gas", "delivery"]}}
    assert rule_matches(rule_features_all["if"], {"area": 100, "seats": 30, "features": ["gas", "delivery"]})
    assert rule_matches(rule_features_all["if"], {"area": 100, "seats": 30, "features": ["gas", "delivery", "alcohol"]})
    assert not rule_matches(rule_features_all["if"], {"area": 100, "seats": 30, "features": ["gas"]})
    assert not rule_matches(rule_features_all["if"], {"area": 100, "seats": 30, "features": ["delivery"]})
    
    print("✅ Rule matching tests passed")

def test_small_restaurant():
    """Test small restaurant (affidavit track)"""
    print("Testing small restaurant scenario...")
    
    payload = {
        "area": 120,
        "seats": 45,
        "features": ["gas", "delivery"]
    }
    
    result = evaluate_restaurant(payload)
    
    # Should get affidavit track
    assert result["summary"]["fire_track"] == "תצהיר (פרק 5)"
    assert result["summary"]["police"] == "פטור מדרישות משטרה (≤200 מקומות וללא אלכוהול)"
    
    # Check that we get expected rules
    rule_ids = [rule["id"] for rule in result["checklist"]]
    
    # Should have basic health rules
    assert "health-baseline" in rule_ids
    assert "health-smoking-signage" in rule_ids
    
    # Should have delivery rules
    assert "delivery-rules" in rule_ids
    
    # Should have gas rules
    assert "gas-cert" in rule_ids
    assert "hood-suppression" in rule_ids
    
    # Should have fire affidavit (not full track)
    assert "fire-affidavit" in rule_ids
    assert "fire-full-area" not in rule_ids
    assert "fire-full-seats" not in rule_ids
    
    # Should not have police rules
    assert "police-alcohol" not in rule_ids
    assert "police-capacity" not in rule_ids
    
    print("✅ Small restaurant test passed")

def test_large_restaurant_with_alcohol():
    """Test large restaurant with alcohol (full requirements)"""
    print("Testing large restaurant with alcohol...")
    
    payload = {
        "area": 500,
        "seats": 200,
        "features": ["gas", "delivery", "alcohol", "hood"]
    }
    
    result = evaluate_restaurant(payload)
    
    # Should get full fire track
    assert result["summary"]["fire_track"] == "מסלול מלא (פרק 6)"
    assert result["summary"]["police"] == "חלים תנאי משטרה"
    
    # Check that we get expected rules
    rule_ids = [rule["id"] for rule in result["checklist"]]
    
    # Should have basic health rules
    assert "health-baseline" in rule_ids
    assert "health-smoking-signage" in rule_ids
    
    # Should have delivery rules
    assert "delivery-rules" in rule_ids
    
    # Should have gas rules
    assert "gas-cert" in rule_ids
    assert "hood-suppression" in rule_ids
    
    # Should have full fire track (both area and seats trigger it)
    assert "fire-full-area" in rule_ids
    assert "fire-full-seats" in rule_ids
    assert "fire-affidavit" not in rule_ids
    
    # Should have police rules for alcohol
    assert "police-alcohol" in rule_ids
    
    print("✅ Large restaurant with alcohol test passed")

def test_high_capacity_restaurant():
    """Test restaurant with >200 seats (police requirements)"""
    print("Testing high capacity restaurant...")
    
    payload = {
        "area": 200,
        "seats": 250,
        "features": ["delivery"]
    }
    
    result = evaluate_restaurant(payload)
    
    # Should get full fire track due to seats
    assert result["summary"]["fire_track"] == "מסלול מלא (פרק 6)"
    assert result["summary"]["police"] == "חלים תנאי משטרה"
    
    # Check that we get expected rules
    rule_ids = [rule["id"] for rule in result["checklist"]]
    
    # Should have police rules for capacity
    assert "police-capacity" in rule_ids
    
    # Should have full fire track for seats
    assert "fire-full-seats" in rule_ids
    assert "fire-full-area" in rule_ids  # area > 150
    
    print("✅ High capacity restaurant test passed")

def test_complex_features():
    """Test restaurant with multiple complex features"""
    print("Testing complex feature combinations...")
    
    payload = {
        "area": 80,
        "seats": 30,
        "features": ["delivery", "cook_next_day", "meat_and_fish"]
    }
    
    result = evaluate_restaurant(payload)
    
    # Should get affidavit track (small)
    assert result["summary"]["fire_track"] == "תצהיר (פרק 5)"
    
    # Check that we get expected rules
    rule_ids = [rule["id"] for rule in result["checklist"]]
    
    # Should have delivery rules
    assert "delivery-rules" in rule_ids
    
    # Should have post-cook cooling rules
    assert "post-cook-cooling" in rule_ids
    
    # Should have meat/fish handling rules
    assert "vet-approval-meat-fish" in rule_ids
    assert "storage-separation" in rule_ids
    assert "prep-surfaces-separated" in rule_ids
    
    print("✅ Complex features test passed")

def run_all_tests():
    """Run all tests"""
    print("="*60)
    print("RUNNING RESTAURANT RULES TESTS")
    print("="*60)
    
    # Load rules first
    load_restaurant_rules()
    
    try:
        test_rule_matching()
        test_small_restaurant()
        test_large_restaurant_with_alcohol()
        test_high_capacity_restaurant()
        test_complex_features()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("="*60)
        return False
    except Exception as e:
        print(f"\n💥 UNEXPECTED ERROR: {e}")
        print("="*60)
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
