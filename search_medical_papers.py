import requests
import json
import xml.etree.ElementTree as ET
import os
import argparse
from datetime import datetime

def search_medical_papers(days_back=60, max_results=100, journals=None, article_types=None):
    """
    Search PubMed for recent papers published in specified medical journals and save results as JSON.
    
    Parameters:
    - days_back: Number of days to look back for papers
    - max_results: Maximum number of results to return
    - journals: List of journal names to search (default: The Lancet and NEJM)
    - article_types: List of article types to include (default: all types)
    """
    # Base URL for NCBI E-utilities
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    # Default journals if none provided
    if journals is None:
        journals = ["Lancet", "The New England journal of medicine"]
    
    # Construct journal part of the query
    journal_query = " OR ".join([f'"{j}"[Journal]' for j in journals])
    
    # Construct article type part of the query (if specified)
    article_type_query = ""
    if article_types:
        article_type_query = " AND (" + " OR ".join([f'"{t}"[Publication Type]' for t in article_types]) + ")"
    
    # Construct the full search query with a filter for papers that have abstracts
    query = f'({journal_query}) AND "last {days_back} days"[PDat]{article_type_query} AND hasabstract[text]'
    
    # Step 1: Search for paper IDs
    search_params = {
        'db': 'pubmed',
        'term': query,
        'retmax': max_results,
        'retmode': 'json',
        'sort': 'date'
    }
    
    print(f"Searching PubMed with query: {query}")
    search_response = requests.get(f"{base_url}esearch.fcgi", params=search_params)
    search_data = search_response.json()
    
    # Get list of PubMed IDs
    id_list = search_data['esearchresult']['idlist']
    
    if not id_list:
        print("No papers found matching the criteria.")
        return []
    
    print(f"Found {len(id_list)} papers matching the criteria.")
    
    # Step 2: Fetch details for these IDs
    fetch_params = {
        'db': 'pubmed',
        'id': ','.join(id_list),
        'retmode': 'xml',  # Use XML format instead of JSON
        'rettype': 'abstract'
    }
    
    fetch_response = requests.get(f"{base_url}efetch.fcgi", params=fetch_params)
    
    # Save the XML response for debugging
    with open('pubmed_response.xml', 'w', encoding='utf-8') as f:
        f.write(fetch_response.text)
    
    # Check if we got a valid XML response
    if not fetch_response.text.strip():
        print("Error: Empty response from PubMed API. This can happen when requesting too many results.")
        print("Try reducing the number of results with --max or narrowing your search criteria.")
        return []
    
    try:
        # Parse XML response
        root = ET.fromstring(fetch_response.text)
    except ET.ParseError as e:
        print(f"Error parsing XML response: {e}")
        print("This can happen when the PubMed API returns too many results or an invalid response.")
        print("Try reducing the number of results with --max or narrowing your search criteria.")
        print("You can also try searching for a specific journal group instead of all journals.")
        return []
    
    # Step 3: Process and extract relevant information
    papers = []
    papers_with_abstracts = 0
    
    # Process each PubmedArticle element
    for article in root.findall('.//PubmedArticle'):
        try:
            # Find the MedlineCitation element
            medline_citation = article.find('./MedlineCitation')
            if medline_citation is None:
                continue
                
            # Find the Article element
            article_data = medline_citation.find('./Article')
            if article_data is None:
                continue
                
            # Extract PMID
            pmid_elem = medline_citation.find('./PMID')
            pmid = pmid_elem.text if pmid_elem is not None else ''
            
            # Extract title
            title_elem = article_data.find('./ArticleTitle')
            title = title_elem.text if title_elem is not None else ''
            
            # Extract journal
            journal_elem = article_data.find('./Journal/Title')
            journal = journal_elem.text if journal_elem is not None else ''
            
            # Create paper dictionary
            paper = {
                'pubmed_id': pmid,
                'title': title,
                'journal': journal,
                'publication_date': '',
                'abstract': '',
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }
            
            # Extract publication date
            pub_date = article_data.find('./Journal/JournalIssue/PubDate')
            if pub_date is not None:
                year_elem = pub_date.find('./Year')
                month_elem = pub_date.find('./Month')
                day_elem = pub_date.find('./Day')
                
                year = year_elem.text if year_elem is not None else ''
                month = month_elem.text if month_elem is not None else ''
                day = day_elem.text if day_elem is not None else ''
                
                paper['publication_date'] = f"{year} {month} {day}".strip()
            
            # Authors are intentionally excluded as per requirements
            
            # Extract abstract
            abstract_elem = article_data.find('./Abstract')
            if abstract_elem is not None:
                abstract_parts = []
                for abstract_text in abstract_elem.findall('./AbstractText'):
                    label = abstract_text.get('Label')
                    text = abstract_text.text or ''
                    
                    if label:
                        abstract_parts.append(f"{label}: {text}")
                    else:
                        abstract_parts.append(text)
                
                paper['abstract'] = ' '.join(abstract_parts)
                papers_with_abstracts += 1
            
            # Extract publication type
            pub_types = []
            pub_type_list = article_data.find('./PublicationTypeList')
            if pub_type_list is not None:
                for pub_type in pub_type_list.findall('./PublicationType'):
                    pub_types.append(pub_type.text)
            
            paper['publication_types'] = pub_types
            
            papers.append(paper)
            
        except Exception as e:
            print(f"Error processing article: {e}")
    
    # Save to JSON file
    # Use the group name if available, otherwise create a simplified journal string
    if group_name != "custom":
        # Use the group name for the filename
        filename = f"medical_papers_{group_name}_{datetime.now().strftime('%Y%m%d')}.json"
    else:
        # For custom journal selections, use a simplified naming approach
        journal_count = len(journals)
        if journal_count == 1:
            # For a single journal, use its name (simplified)
            journal_name = journals[0].replace(" ", "_").lower()
            # Remove any problematic characters
            journal_name = ''.join(c for c in journal_name if c.isalnum() or c == '_')
            filename = f"medical_papers_{journal_name}_{datetime.now().strftime('%Y%m%d')}.json"
        else:
            # For multiple journals, just indicate the count
            filename = f"medical_papers_custom_{journal_count}_journals_{datetime.now().strftime('%Y%m%d')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(papers)} papers to {filename}")
    if papers:
        print(f"Papers with abstracts: {papers_with_abstracts} ({papers_with_abstracts/len(papers)*100:.1f}%)")
    else:
        print("No papers found with abstracts.")
    
    return papers

def load_journal_config(config_file='journal_config.json'):
    """
    Load journal configuration from a JSON file.
    
    Returns:
        dict: Dictionary containing journal groups and default group
    """
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: Configuration file {config_file} not found. Using default journals.")
        return {
            "journal_groups": {
                "major_medical": ["Lancet", "The New England journal of medicine", "JAMA", "BMJ"]
            },
            "default_group": "major_medical"
        }

if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Search for recent medical papers in PubMed')
    parser.add_argument('--days', type=int, default=30, help='Number of days to look back (default: 30)')
    parser.add_argument('--max', type=int, default=250, help='Maximum number of results (default: 250)')
    parser.add_argument('--config', type=str, default='journal_config.json', help='Path to journal configuration file')
    parser.add_argument('--group', type=str, default='major_medical', help='Journal group to use from configuration (default: major_medical)')
    parser.add_argument('--journals', type=str, nargs='+', help='Specific journals to search (overrides group)')
    parser.add_argument('--types', type=str, nargs='+', 
                        default=["Journal Article", "Clinical Trial", "Randomized Controlled Trial", "Review"],
                        help='Article types to include')
    
    args = parser.parse_args()
    
    # Load journal configuration
    config = load_journal_config(args.config)
    
    # Determine which journals to search
    if args.journals:
        journals = args.journals
        group_name = "custom"
    elif args.group:
        if args.group in config["journal_groups"]:
            journals = config["journal_groups"][args.group]
            group_name = args.group
        else:
            print(f"Warning: Group '{args.group}' not found in configuration. Using default group.")
            journals = config["journal_groups"][config["default_group"]]
            group_name = config["default_group"]
    else:
        journals = config["journal_groups"][config["default_group"]]
        group_name = config["default_group"]
    
    print(f"Using journal group: {group_name}")
    print(f"Journals: {', '.join(journals)}")
    
    # Search for papers
    papers = search_medical_papers(
        days_back=args.days,
        max_results=args.max,
        journals=journals,
        article_types=args.types
    )