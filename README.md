# 4P Medicine Newsletter Tool

This tool helps you gather and analyze recent medical publications for your 4P medicine newsletter.

## Overview

The tool consists of two main scripts:

1. `search_medical_papers.py` - Searches PubMed for recent papers published in major medical journals (The Lancet, NEJM, JAMA, BMJ)
2. `analyze_papers.py` - Uses an LLM to analyze papers and identify those related to 4P medicine

## Requirements

- Python 3.6+
- `requests` library
- Google API key for the Gemini API

## Installation

1. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

2. Set up your Google API key:

   Create a file named `api_keys.json` with the following content:
   ```json
   {
     "google_api_key": "your_google_api_key_here"
   }
   ```
   
   Alternatively, you can set your API key as an environment variable:
   ```
   export GOOGLE_API_KEY="your_google_api_key_here"
   ```
   
   Note: The `api_keys.json` file is included in `.gitignore` to prevent accidentally committing your API keys to version control.

## Usage

### Step 1: Gather Papers

Run the search script to collect recent papers from major medical journals:

```
python search_medical_papers.py
```

This will create a JSON file with a name based on the journal group used, for example:
- `medical_papers_major_medical_YYYYMMDD.json` (when using the major_medical group)
- `medical_papers_all_journals_YYYYMMDD.json` (when using the all_journals group)
- `medical_papers_lancet_YYYYMMDD.json` (when searching a single journal)
- `medical_papers_custom_N_journals_YYYYMMDD.json` (when searching multiple specific journals)

### Step 2: Analyze Papers

Run the analysis script to identify papers related to 4P medicine:

```bash
python analyze_papers.py  # Uses Google's Gemini 2.5 Pro
```

This will:
1. Use an LLM to analyze the papers and identify those related to 4P medicine
2. Evaluate each paper for its impact, significance, and revolutionary aspects
3. Focus on large trials and RCTs
4. Generate a markdown report with the top 20 papers, sorted by impact score
5. Tag each paper with relevant 4P medicine aspects (Predictive, Preventive, Personalized, Participatory)

The results will be saved to:
- A JSON file named `4p_analysis_YYYYMMDD.json` with detailed analysis
- A Markdown report named `4p_medicine_papers_YYYYMMDD.md` with the top 20 papers
- Print a summary of the most important papers for your newsletter

## Customization

### Modifying the Search

To change the search parameters in `search_medical_papers.py`:

- Adjust the `days_back` parameter to change the time period (default: 30 days)
- Modify the list of journals to search different publications
- Change the article types to focus on specific types of papers

### Journal Configuration

The tool now uses a configuration file (`journal_config.json`) to manage journal lists. This makes it easy to add, remove, or organize journals without modifying the code.

The configuration file organizes journals into groups:

```json
{
  "journal_groups": {
    "major_medical": [
      "Lancet",
      "The New England journal of medicine",
      "JAMA",
      "BMJ"
    ],
    "specialty_medical": [
      "Nature Medicine",
      "JAMA Internal Medicine",
      "Annals of Internal Medicine",
      "Journal of Clinical Oncology"
    ],
    "precision_medicine": [
      "NPJ Precision Oncology",
      "Journal of Personalized Medicine",
      "Personalized Medicine",
      "The Pharmacogenomics Journal",
      "OMICS: A Journal of Integrative Biology"
    ]
  },
  "default_group": "major_medical"
}
```

### Command Line Options

You can run the search script with various command line options:

```bash
# Search using the default settings (major_medical journals, max 250 papers, last 30 days)
python search_medical_papers.py

# Search using a specific journal group
python search_medical_papers.py --group precision_medicine

# Search all configured journals at once
python search_medical_papers.py --group all_journals

# Search with custom parameters
python search_medical_papers.py --days 60 --max 300 --group specialty_medical

# Search specific journals directly
python search_medical_papers.py --journals "Lancet" "Nature Medicine"

# Use a different configuration file
python search_medical_papers.py --config my_custom_config.json
```

The run script supports these options:

```bash
# Run with default settings (major_medical journals, max 250 papers, last 30 days)
./run_newsletter_tool.sh

# Search for papers from the last 60 days in precision medicine journals
./run_newsletter_tool.sh --days 60 --group precision_medicine

# Limit search to 100 papers and analysis to 10 papers (for testing)
./run_newsletter_tool.sh --max 100 --max-analyze 10

# Search all journals
./run_newsletter_tool.sh --group all_journals
```

The analysis script also supports direct options:

```bash
# Analyze a specific file
python analyze_papers.py --file medical_papers_major_medical_20250420.json

# Limit analysis to 5 papers (for testing)
python analyze_papers.py --max 5
```

### Using the Example Script

An example script is provided to demonstrate how to use the tool programmatically:

```bash
# Run the example script
python example.py
```

This script:
1. Searches for papers in major medical journals from the last 30 days
2. Analyzes the top 10 papers using Gemini
3. Generates a markdown report with the results
```

## Next Steps

1. Set up a cron job to run these scripts automatically on a regular schedule
2. Expand the search to include more journals
3. Create a simple web interface to view and manage the results

## Setting Up on GitHub

1. Create a new GitHub repository
2. Clone the repository to your local machine
3. Copy all the files from this project to your local repository
4. Create your own `api_keys.json` file with your Google API key
5. Commit and push the changes to GitHub

```bash
# Example commands
git clone https://github.com/yourusername/4p-medicine-newsletter.git
cd 4p-medicine-newsletter
# Copy files from this project
cp /path/to/this/project/* .
# Create your api_keys.json file
echo '{"google_api_key": "your_actual_api_key_here"}' > api_keys.json
# Add files to git (excluding api_keys.json which is in .gitignore)
git add .
git commit -m "Initial commit"
git push origin main
```

Note: The `api_keys.json` file is included in `.gitignore` to prevent accidentally committing your API keys to version control.

## License

This tool is provided for personal use only.