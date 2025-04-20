#!/bin/bash

# 4P Medicine Newsletter Tool Runner with Gemini
# This script runs both the search and Gemini-based analysis scripts in sequence

echo "Starting 4P Medicine Newsletter Tool with Gemini..."

# Process command line arguments
DAYS=30
MAX_RESULTS=250  # Default to 250 papers
GROUP="major_medical"  # Default to major medical journals
CONFIG="journal_config.json"
MAX_ANALYZE=0  # 0 means analyze all papers

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --days)
      DAYS="$2"
      shift 2
      ;;
    --max)
      MAX_RESULTS="$2"
      shift 2
      ;;
    --max-analyze)
      MAX_ANALYZE="$2"
      shift 2
      ;;
    --group)
      GROUP="$2"
      shift 2
      ;;
    --config)
      CONFIG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--days N] [--max N] [--max-analyze N] [--group GROUP_NAME] [--config CONFIG_FILE]"
      exit 1
      ;;
  esac
done

# Step 1: Run the search script
echo "Searching for recent medical papers..."
python search_medical_papers.py --days "$DAYS" --max "$MAX_RESULTS" --group "$GROUP" --config "$CONFIG"

# Check if the search was successful
if [ $? -ne 0 ]; then
    echo "Error: Paper search failed. Exiting."
    exit 1
fi

# Step 2: Run the analysis script
echo "Analyzing papers for 4P medicine relevance using Gemini 2.5 Pro..."
echo "This will identify the most impactful, revolutionary, and exciting papers related to 4P medicine."
echo "The results will be saved as a Markdown report."

# API key is loaded from api_keys.json
if [ "$MAX_ANALYZE" -gt 0 ]; then
    echo "Limiting analysis to $MAX_ANALYZE papers for testing"
    python analyze_papers.py --max "$MAX_ANALYZE"
else
    python analyze_papers.py
fi

# Check if the markdown file was created
MARKDOWN_FILE=$(ls -t 4p_medicine_papers_*.md 2>/dev/null | head -1)
if [ -n "$MARKDOWN_FILE" ]; then
    echo ""
    echo "Markdown report created: $MARKDOWN_FILE"
    echo "You can view this file to see the top 20 papers relevant to 4P medicine,"
    echo "sorted by impact score, with the most revolutionary and exciting papers at the top."
fi

# Check if the analysis was successful
if [ $? -ne 0 ]; then
    echo "Error: Paper analysis failed. Exiting."
    exit 1
fi

echo "Process complete! Check the output files for results."