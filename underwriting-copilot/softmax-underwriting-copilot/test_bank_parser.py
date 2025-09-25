#!/usr/bin/env python3
"""
Test script for bank_parser functionality with the mock PDF data.
"""
import sys
import logging
from pathlib import Path

import pytest

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from pipeline.parser_adapter import parse
from pipeline.bank_parser.registry import detect_bank, BANK_DETECTORS

# Import DataHandler to register the bank parsers
from pipeline.bank_parser import DataHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@pytest.mark.skip(reason="Utility script – not executed as part of automated test suite")
def test_pdf_file(pdf_path):
    """Test parsing a single PDF file."""
    print(f"\n{'='*60}")
    print(f"Testing PDF: {pdf_path}")
    print(f"{'='*60}")

    try:
        # Test the adapter
        result = parse(pdf_path)

        print(f"Bank Code: {result['bank_code']}")
        print(f"Customer Name: {result['customer_name']}")
        print(f"Account Number: {result['account_number']}")
        print(f"Rows Found: {result['stats']['row_count']}")

        if result['stats']['period_from'] and result['stats']['period_to']:
            print(f"Period: {result['stats']['period_from']} to {result['stats']['period_to']}")

        if result['rows']:
            print(f"\nFirst few rows:")
            for i, row in enumerate(result['rows'][:3]):
                print(f"  Row {i+1}: {row}")

        return True

    except Exception as e:
        print(f"ERROR: Failed to parse {pdf_path}")
        print(f"Error details: {e}")
        return False

def main():
    """Test all PDF files in the mockdata directory."""

    # Print registered bank detectors
    print(f"Registered bank detectors: {len(BANK_DETECTORS)}")
    for i, (checker, parser) in enumerate(BANK_DETECTORS):
        print(f"  {i+1}. {parser.__name__}")

    # Find all PDF files in mockdata
    mockdata_dir = Path("mockdata")
    if not mockdata_dir.exists():
        print(f"ERROR: mockdata directory not found at {mockdata_dir}")
        return

    pdf_files = list(mockdata_dir.glob("*.pdf"))
    if not pdf_files:
        print(f"ERROR: No PDF files found in {mockdata_dir}")
        return

    print(f"\nFound {len(pdf_files)} PDF files to test:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file.name}")

    # Test each PDF file
    successful = 0
    failed = 0

    for pdf_file in pdf_files:
        if test_pdf_file(str(pdf_file)):
            successful += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total files tested: {len(pdf_files)}")
    print(f"Successful parses: {successful}")
    print(f"Failed parses: {failed}")
    print(f"Success rate: {successful/len(pdf_files)*100:.1f}%")

if __name__ == "__main__":
    main()
