#!/usr/bin/env python3
"""
Example script demonstrating how to use the 4P Medicine Newsletter Tool programmatically.
"""

import os
import json
from search_medical_papers import search_medical_papers, load_journal_config
from analyze_papers import analyze_papers_with_gemini

def main():
    # Load configuration
    config = load_journal_config()
    
    # Get journals from the major_medical group
    journals = config["journal_groups"]["major_medical"]
    
    print(f"Searching for papers in major medical journals: {', '.join(journals)}")
    
    # Search for papers (last 30 days, max 50 results)
    papers = search_medical_papers(
        days_back=30,
        max_results=50,
        journals=journals,
        article_types=["Journal Article", "Clinical Trial", "Randomized Controlled Trial", "Review"]
    )
    
    if not papers:
        print("No papers found. Exiting.")
        return
    
    # Get the most recent JSON file
    json_files = [f for f in os.listdir() if f.startswith("medical_papers_") and f.endswith(".json")]
    if not json_files:
        print("No JSON files found. Exiting.")
        return
    
    # Sort by modification time (newest first)
    json_file = sorted(json_files, key=lambda f: os.path.getmtime(f), reverse=True)[0]
    
    print(f"Analyzing papers from {json_file}")
    
    # Analyze papers (limit to 10 for this example)
    analyze_papers_with_gemini(json_file, max_papers=10)
    
    print("Analysis complete!")
    print("Check the generated markdown file for the results.")

if __name__ == "__main__":
    main()