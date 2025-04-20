import json
import csv
import sys

def convert_json_to_csv(json_file, csv_file):
    """
    Convert the medical papers JSON file to CSV format
    """
    # Load the JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    if not papers:
        print("No papers found in the JSON file.")
        return
    
    # Define the CSV fields
    fields = [
        'pubmed_id', 
        'title', 
        'journal', 
        'publication_date', 
        'url', 
        'authors',
        'abstract',
        'publication_types'
    ]
    
    # Write to CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(fields)
        
        # Write data rows
        for paper in papers:
            row = [
                paper.get('pubmed_id', ''),
                paper.get('title', ''),
                paper.get('journal', ''),
                paper.get('publication_date', ''),
                paper.get('url', ''),
                '; '.join(paper.get('authors', [])),
                paper.get('abstract', ''),
                '; '.join(paper.get('publication_types', []))
            ]
            writer.writerow(row)
    
    print(f"Successfully converted {len(papers)} papers to CSV format.")
    print(f"CSV file saved as: {csv_file}")

if __name__ == "__main__":
    # Get the JSON filename from command line or use default
    json_file = sys.argv[1] if len(sys.argv) > 1 else "medical_papers_major_medical_20250420.json"
    
    # Create CSV filename based on JSON filename
    csv_file = json_file.replace('.json', '.csv')
    
    # Convert the file
    convert_json_to_csv(json_file, csv_file)