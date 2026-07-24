import sys
import os
import xml.etree.ElementTree as ET
from langchain_core.tools import tool
from Bio import Entrez

# Add parent directory to path so config can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

@tool
def pubmed_search(query: str) -> str:
    """Search NCBI PubMed for biomedical literature and return formatted citation and abstract results.
    
    Args:
        query: The search term or clinical question to query PubMed.
    """
    Entrez.email = config.ENTREZ_EMAIL
    if config.ENTREZ_API_KEY:
        Entrez.api_key = config.ENTREZ_API_KEY
        
    try:
        # Search for PMIDs (relevance sorted, max 5 results)
        search_handle = Entrez.esearch(db="pubmed", term=query, retmax=5, sort="relevance")
        search_xml = search_handle.read()
        search_handle.close()
        
        # Parse search XML
        search_root = ET.fromstring(search_xml)
        id_list_el = search_root.find("IdList")
        if id_list_el is None:
            return f"No PubMed results found for query: '{query}'"
            
        pmids = [id_el.text for id_el in id_list_el.findall("Id") if id_el.text]
        if not pmids:
            return f"No PubMed results found for query: '{query}'"
            
        # Fetch details for the PMIDs
        fetch_handle = Entrez.efetch(db="pubmed", id=",".join(pmids), retmode="xml")
        fetch_xml = fetch_handle.read()
        fetch_handle.close()
        
        # Parse fetch XML
        fetch_root = ET.fromstring(fetch_xml)
        articles = fetch_root.findall(".//PubmedArticle")
        if not articles:
            return f"PubMed search succeeded but failed to fetch details for PMIDs: {', '.join(pmids)}"
            
        formatted_results = []
        for article in articles:
            pmid_el = article.find(".//PMID")
            pmid = pmid_el.text if pmid_el is not None else "Unknown"
            
            title_el = article.find(".//ArticleTitle")
            title = "".join(title_el.itertext()).strip() if title_el is not None else "No Title Available"
            
            # Find publication year
            year = "Unknown Year"
            year_el = article.find(".//PubDate/Year")
            if year_el is not None:
                year = year_el.text
            else:
                medline_date_el = article.find(".//PubDate/MedlineDate")
                if medline_date_el is not None and len(medline_date_el.text) >= 4:
                    year = medline_date_el.text[:4]
                    
            abstract_el = article.find(".//Abstract")
            abstract_text = ""
            if abstract_el is not None:
                texts = [t.text for t in abstract_el.findall(".//AbstractText") if t.text]
                abstract_text = " ".join(texts).strip()
                
            if not abstract_text:
                abstract_text = "No abstract available."
                
            # Truncate to ~1500 chars
            if len(abstract_text) > 1500:
                abstract_text = abstract_text[:1497] + "..."
                
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            formatted_results.append(
                f"[PMID {pmid}] {title} ({year})\nURL: {url}\nAbstract: {abstract_text}"
            )
            
        return "\n\n---\n\n".join(formatted_results)
        
    except Exception as e:
        return f"Error executing PubMed search for '{query}': {str(e)}"
