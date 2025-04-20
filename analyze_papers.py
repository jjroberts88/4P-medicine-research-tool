import json
import os
import requests
from datetime import datetime

# Load API keys from configuration file
def load_api_keys(config_file='api_keys.json'):
    """Load API keys from configuration file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: API keys file {config_file} not found.")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: API keys file {config_file} is not valid JSON.")
        return {}

# Try to load API key from config file first, then environment variable
api_keys = load_api_keys()
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", api_keys.get("google_api_key", "your_api_key_here"))

# Gemini API endpoint for the 2.5 Pro experimental model
GEMINI_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro-exp-03-25:generateContent"

def analyze_papers_with_gemini(json_file, max_papers=None):
    """
    Use Google's Gemini 2.5 Pro to analyze papers and identify those related to 4P medicine.
    
    Args:
        json_file: Path to the JSON file containing papers to analyze
        max_papers: Maximum number of papers to analyze (for testing)
    """
    # Load papers from JSON file
    with open(json_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    if not papers:
        print("No papers found in the JSON file.")
        return []
        
    print(f"Analyzing {len(papers)} papers...")
    
    # Filter out papers without abstracts
    papers_with_abstracts = [p for p in papers if p['abstract'].strip()]
    print(f"Found {len(papers_with_abstracts)} papers with abstracts")
    
    if not papers_with_abstracts:
        print("No papers with abstracts found. Cannot proceed with analysis.")
        return []
    
    # Limit the number of papers if max_papers is specified
    if max_papers is not None:
        papers_to_analyze = papers_with_abstracts[:max_papers]
        print(f"Limiting analysis to {len(papers_to_analyze)} papers (max_papers={max_papers})")
    else:
        papers_to_analyze = papers_with_abstracts
    
    # Prepare results
    results = []
    
    # Process each paper
    for i, paper in enumerate(papers_to_analyze):
        print(f"Processing paper {i+1}/{len(papers_to_analyze)}: {paper['title'][:50]}...")
        
        # Create prompt for Gemini
        prompt = f"""
        You are a medical research expert specializing in 4P medicine (Predictive, Preventive, Personalized, and Participatory medicine). Review the following medical research paper and evaluate it carefully.

        Title: {paper['title']}
        Journal: {paper['journal']}
        Publication Date: {paper['publication_date']}
        Abstract: {paper['abstract']}
        
        Analyze this paper for:
        1. Relevance to 4P medicine (Predictive, Preventive, Personalized, Participatory)
        2. Impact and significance, with particular focus on large trials/RCTs
        3. Revolutionary, interesting, or exciting aspects of the research
        4. Potential to change clinical practice or understanding of medicine
        
        Please provide:
        1. Is this paper relevant to 4P medicine? (Yes/No)
        2. Which specific aspects of 4P medicine does it address? (Predictive, Preventive, Personalized, Participatory)
        3. Is this a large trial or RCT? (Yes/No)
        4. Brief summary of the paper's significance (2-3 sentences)
        5. What makes this paper revolutionary, interesting, or exciting? (if applicable)
        6. Overall impact score (1-10 scale, where 10 is extremely high impact)
        
        Format your response as JSON with the following fields:
        - is_relevant: boolean
        - aspects: list of strings (e.g., ["Predictive", "Personalized"])
        - is_large_trial: boolean
        - summary: string
        - revolutionary_aspects: string (or null if none)
        - impact_score: integer
        """
        
        # Call Gemini API with timeout and retries
        max_retries = 3
        retry_count = 0
        success = False
        response = None
        
        while retry_count < max_retries and not success:
            try:
                print(f"  Sending request to Gemini API (attempt {retry_count + 1}/{max_retries})...")
                
                # Add a timeout to prevent hanging indefinitely
                response = requests.post(
                    f"{GEMINI_API_ENDPOINT}?key={GOOGLE_API_KEY}",
                    headers={"Content-Type": "application/json"},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": prompt}]
                            }
                        ],
                        "generationConfig": {
                            "temperature": 0.3,
                            "topP": 0.8,
                            "topK": 40
                        }
                    },
                    timeout=60  # 60 second timeout
                )
                
                # Check if the response is successful
                if response.status_code == 200:
                    success = True
                else:
                    print(f"  API returned status code {response.status_code}: {response.text}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        print(f"  Failed after {max_retries} attempts. Skipping this paper.")
                        break
                
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"  Request timed out. Retrying ({retry_count}/{max_retries})...")
                else:
                    print(f"  Request timed out after {max_retries} attempts. Skipping this paper.")
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"  Request error: {e}. Retrying ({retry_count}/{max_retries})...")
                else:
                    print(f"  Request failed after {max_retries} attempts: {e}. Skipping this paper.")
        
        # If we have a successful response, parse it
        analysis = None
        if success and response is not None:
            try:
                response_data = response.json()
                
                # Extract the text from the response
                if 'candidates' in response_data and len(response_data['candidates']) > 0:
                    candidate = response_data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        llm_response = candidate['content']['parts'][0]['text']
                        print(f"  Received response from Gemini API")
                        
                        # Extract JSON from response
                        try:
                            # Find JSON in the response (it might be wrapped in markdown code blocks)
                            if "```json" in llm_response:
                                json_str = llm_response.split("```json")[1].split("```")[0].strip()
                            elif "```" in llm_response:
                                json_str = llm_response.split("```")[1].strip()
                            else:
                                json_str = llm_response
                            
                            analysis = json.loads(json_str)
                            
                            # Add paper info to analysis
                            analysis['paper'] = {
                                'pubmed_id': paper['pubmed_id'],
                                'title': paper['title'],
                                'url': paper['url'],
                                'journal': paper['journal'],
                                'publication_date': paper['publication_date']
                            }
                            
                            # Ensure all required fields are present
                            if 'is_relevant' not in analysis:
                                analysis['is_relevant'] = False
                            if 'aspects' not in analysis:
                                analysis['aspects'] = []
                            if 'is_large_trial' not in analysis:
                                analysis['is_large_trial'] = False
                            if 'summary' not in analysis:
                                analysis['summary'] = ""
                            if 'revolutionary_aspects' not in analysis:
                                analysis['revolutionary_aspects'] = None
                            if 'impact_score' not in analysis:
                                analysis['impact_score'] = 0
                            
                            print(f"  Successfully parsed response: Paper is{' ' if analysis['is_relevant'] else ' not '}relevant to 4P medicine")
                            
                        except Exception as e:
                            print(f"  Error parsing Gemini response: {e}")
                            print(f"  Raw response: {llm_response[:100]}...")
                    else:
                        print(f"  Unexpected response format: missing content or parts")
                else:
                    print(f"  Unexpected response format: no candidates found")
            except Exception as e:
                print(f"  Error processing response: {e}")
        
        # Add the analysis to results if it was successfully created
        if analysis is not None:
            results.append(analysis)
    
    # Save results as JSON
    json_output_file = f"4p_analysis_gemini_{datetime.now().strftime('%Y%m%d')}.json"
    with open(json_output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Generate summary report
    relevant_papers = [p for p in results if p.get('is_relevant', False)]
    
    print(f"\nAnalysis complete!")
    print(f"Found {len(relevant_papers)} papers relevant to 4P medicine")
    print(f"Results saved to {json_output_file}")
    
    # Sort by impact score and revolutionary aspects
    if relevant_papers:
        # Create a custom sorting function that prioritizes impact_score and revolutionary_aspects
        def paper_sort_key(paper):
            impact_score = paper.get('impact_score', 0)
            has_revolutionary_aspects = 1 if paper.get('revolutionary_aspects') else 0
            is_large_trial = 1 if paper.get('is_large_trial', False) else 0
            return (impact_score, has_revolutionary_aspects, is_large_trial)
        
        relevant_papers.sort(key=paper_sort_key, reverse=True)
        
        # Generate markdown output
        markdown_output_file = f"4p_medicine_papers_{datetime.now().strftime('%Y%m%d')}.md"
        with open(markdown_output_file, 'w', encoding='utf-8') as f:
            f.write("# Top Papers Relevant to 4P Medicine\n\n")
            f.write("*Generated on: " + datetime.now().strftime('%Y-%m-%d') + "*\n\n")
            f.write("This report highlights the most impactful, revolutionary, and exciting papers related to 4P Medicine (Predictive, Preventive, Personalized, and Participatory).\n\n")
            
            # Write table of contents
            f.write("## Table of Contents\n\n")
            for i, paper in enumerate(relevant_papers[:20], 1):
                title = paper['paper']['title']
                aspects_tags = ", ".join([f"[{a}]" for a in paper.get('aspects', [])])
                f.write(f"{i}. [{title}](#{i}) {aspects_tags}\n")
            f.write("\n")
            
            # Write detailed entries
            f.write("## Detailed Paper Reviews\n\n")
            for i, paper in enumerate(relevant_papers[:20], 1):
                title = paper['paper']['title']
                journal = paper['paper']['journal']
                # Authors are intentionally excluded as per requirements
                pub_date = paper['paper']['publication_date']
                url = paper['paper']['url']
                aspects = paper.get('aspects', [])
                aspects_badges = " ".join([f"![{a}](https://img.shields.io/badge/-{a}-blue)" for a in aspects])
                impact_score = paper.get('impact_score', 0)
                is_large_trial = "Yes" if paper.get('is_large_trial', False) else "No"
                summary = paper.get('summary', '')
                revolutionary = paper.get('revolutionary_aspects', '')
                
                f.write(f"<a id='{i}'></a>\n")
                f.write(f"### {i}. {title}\n\n")
                f.write(f"{aspects_badges}\n\n")
                f.write(f"**Journal:** {journal}  \n")
                f.write(f"**Publication Date:** {pub_date}  \n")
                f.write(f"**Impact Score:** {impact_score}/10  \n")
                f.write(f"**Large Trial/RCT:** {is_large_trial}  \n\n")
                f.write(f"**Summary:**  \n{summary}\n\n")
                if revolutionary:
                    f.write(f"**Revolutionary Aspects:**  \n{revolutionary}\n\n")
                f.write(f"[View on PubMed]({url})\n\n")
                f.write("---\n\n")
        
        print(f"Markdown report saved to {markdown_output_file}")
        
        # Print top papers to console
        print("\nTop 5 most impactful papers for 4P medicine:")
        for i, paper in enumerate(relevant_papers[:5], 1):
            print(f"{i}. {paper['paper']['title']} (Impact: {paper.get('impact_score', 'N/A')}/10)")
            print(f"   Aspects: {', '.join(paper.get('aspects', []))}")
            print(f"   URL: {paper['paper']['url']}")
            print(f"   Summary: {paper.get('summary', 'N/A')}")
            if paper.get('revolutionary_aspects'):
                print(f"   Revolutionary aspects: {paper.get('revolutionary_aspects')}")
            print()
    
    return results

if __name__ == "__main__":
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Analyze medical papers for 4P medicine relevance using Gemini 2.5 Pro')
    parser.add_argument('--file', type=str, help='Specific JSON file to analyze (default: most recent)')
    parser.add_argument('--max', type=int, help='Maximum number of papers to analyze (for testing)')
    args = parser.parse_args()
    
    # Check if API key is set
    if GOOGLE_API_KEY == "your_api_key_here":
        print("WARNING: No Google API key set. Analysis will fail with API errors.")
        print("Please set your API key using the GOOGLE_API_KEY environment variable or by editing this script.")
        print("Continuing anyway, but expect API errors...\n")
    
    # Determine which file to analyze
    if args.file:
        if os.path.exists(args.file):
            input_file = args.file
        else:
            print(f"Error: File {args.file} not found.")
            exit(1)
    else:
        # Find the most recent JSON file with medical papers
        json_files = [f for f in os.listdir() if f.startswith("medical_papers_") and f.endswith(".json")]
        
        if not json_files:
            print("No medical papers JSON files found. Please run search_medical_papers.py first.")
            exit(1)
        else:
            # Get file modification times and sort by most recent
            file_times = [(f, os.path.getmtime(f)) for f in json_files]
            file_times.sort(key=lambda x: x[1], reverse=True)  # Sort by modification time (newest first)
            
            input_file = file_times[0][0]
    
    print(f"Analyzing papers from {input_file}")
    analyze_papers_with_gemini(input_file, max_papers=args.max)