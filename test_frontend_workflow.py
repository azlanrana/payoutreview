#!/usr/bin/env python3
"""Test script for the frontend workflow"""

import io
import sys
import os

# Add frontend to path
sys.path.append('frontend')

from validation_wrapper import validate_trades_csv, get_csv_download_content, get_validation_summary

def test_frontend_workflow():
    """Test the complete frontend workflow"""
    print("🧪 Testing Frontend Workflow...")
    print("=" * 50)

    # Simulate file upload by reading the test CSV
    with open('test_frontend.csv', 'rb') as f:
        file_content = f.read()

    # Create a file-like object (simulating Streamlit upload)
    uploaded_file = io.BytesIO(file_content)
    uploaded_file.name = 'test_frontend.csv'

    try:
        # Test validation
        print("📤 Processing uploaded CSV...")
        results, processed_df = validate_trades_csv(uploaded_file, account_size=100000.0)

        print("✅ Validation successful!")

        # Get summary
        summary = get_validation_summary(results)

        print(f"📊 Decision: {summary['decision']}")
        print(f"📈 Total Trades: {summary['total_trades']}")
        print(f"💰 Total Profit: ${summary['total_profit']:,.2f}")
        print(f"🚨 Breaches: {summary['breach_count']}")
        print(f"⚠️ Warnings: {summary['warning_count']}")

        # Test CSV download generation
        csv_content, filename = get_csv_download_content(processed_df, "test_analysis")

        print(f"📥 Generated download file: {filename}")
        print(f"📄 CSV content length: {len(csv_content)} characters")

        # Check if violation columns were added
        expected_cols = ['violation_type', 'violation_details', 'rule_status']
        missing_cols = [col for col in expected_cols if col not in processed_df.columns]

        if missing_cols:
            print(f"❌ Missing violation columns: {missing_cols}")
            return False
        else:
            print("✅ Violation columns added successfully")

        print("\n" + "=" * 50)
        print("🎉 Frontend workflow test PASSED!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_frontend_workflow()
    sys.exit(0 if success else 1)