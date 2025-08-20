
import time
import os
import sys
import pandas as pd
from datetime import datetime
from src.core.llm_processor import LLMProcessor
from src.core.elsevier_article_retrieval import DOIFetcher
from config.settings import GROQ_API_KEY, GROQ_MODEL, GEMINI_API_KEY, GEMINI_MODEL, ELSEVIER_API_KEY, ELSEVIER_BASE_URL


sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def initialize_llm_service():

    print("=" * 70)
    print("LLM-enhanced literature retrieval tool")
    print("=" * 70)
    print("Supports natural language queries with automatic keyword extraction and academic literature search")
    print()

    print("Using Free Online API for LLM service")

    use_groq = True
    use_deepseek = True
    use_gemini = True
    groq_api_key = GROQ_API_KEY
    gemini_api_key = GEMINI_API_KEY
    if not groq_api_key or not gemini_api_key:
        print(
            "\nPlease set the environment variable of LLM service based on available API.")
        return None, None, None, None

    try:
        processor = LLMProcessor(
            use_groq=use_groq, use_gemini=use_gemini)
        print(
            f"\n{'LLM API service initialized successfully'} ")
        return processor, use_groq, use_deepseek, use_gemini
    except Exception as e:
        print(f"Failed to initialize LLM service: {e}")
        return None, None, None, None


def get_user_query():

    print("\n" + "=" * 70)
    print("Please enter the name and chemical formula of the molecule you want to search for:")
    molecular_name = input(
        "Enter the molecule name (e.g., 'methane'): ").strip()
    molecular_formula = input(
        "Enter the molecular formula (e.g., 'CH4'): ").strip()
    print("\nIf you want to search for a specific isotope of the molecule, please specify it as well. Only one isotope can be specified at a time.")
    molecular_isotope = input(
        "Enter the isotope (e.g., '12CH4', press Enter to skip): ").strip()

    if not molecular_name or not molecular_formula:
        print("Molecule name and formula are required, returning to menu")
        return None, None, None
    if not molecular_isotope:
        molecular_isotope = None
    return molecular_name, molecular_formula, molecular_isotope


def get_search_parameters():
    # Title keywords restriction
    print("\n" + "=" * 70)
    print(f"Any specifically required keywords:")
    print("(Specify keywords that can help search for more relvant papers)")

    required_keywords = input(
        "\nPlease enter required keywords (comma-separated, press Enter to skip): ").strip()

    additional_keywords = []
    if required_keywords:
        additional_keywords = [
            kw.strip() for kw in required_keywords.split(',') if kw.strip()]

    # Year range setting
    print("\n" + "=" * 70)
    print(f"Set year range for searching (minimum valid year is 1900):")

    min_year = None
    max_year = None
    current_year = datetime.now().year

    year_range = input(
        "\nPlease enter year range (e.g., 2000-2023, press Enter for no restriction): ").strip()

    if '-' in year_range:
        start_year, end_year = year_range.split('-', 1)
        min_year = int(start_year.strip())
        max_year = int(end_year.strip())

        # Check if the years are valid
        if min_year > max_year:
            print(
                "The start year cannot be greater than the end year, changing the order")
            min_year, max_year = max_year, min_year

        if min_year < 1900 or max_year > current_year:
            print(f"Invalid year range, using default: no restriction")
            min_year = 1900
            max_year = current_year
        else:
            print(f"\nYear range set: {min_year}-{max_year}")
    else:
        print("\nNo restriction on year range")
        min_year = 1900
        max_year = current_year

    # Citation count setting
    print("\n" + "=" * 70)
    print(f"Restriction on citation count:")
    print("\n1. No restriction on citation count (0 citations allowed)")
    print("2. At least 1 citation (low impact)")
    print("3. At least 5 citations (medium impact)")
    print("4. At least 20 citations (high impact)")
    print("5. At least 50 citations (very high impact)")

    citation_choice = input("\nPlease choose (1-5, defaults to 3): ").strip()

    min_citations = 5
    if citation_choice == "1":
        min_citations = 0
    elif citation_choice == "2":
        min_citations = 1
    elif citation_choice == "3":
        min_citations = 5
    elif citation_choice == "4":
        min_citations = 20
    elif citation_choice == "5":
        min_citations = 50

    return {
        'specified_keywords': additional_keywords,
        'min_year': min_year,
        'max_year': max_year,
        'min_citations': min_citations,
        'enable_llm_filter': True,  # Default value
        'llm_filter_threshold': 0.8  # Default threshold
    }


def display_search_config(molecular_name, molecular_formula, molecular_isotope, params, use_groq, use_deepseek, use_gemini):
    """display the search configuration"""
    print("\n" + "=" * 70)
    print(f"\nFULL SEARCH CONFIGURATION:")
    print(
        f"\nActivated LLM service: {'Groq API using model ' + GROQ_MODEL if use_groq else 'Groq API not used'}, {'Gemini API using model ' + GEMINI_MODEL if use_gemini else 'Gemini API not used'}")
    print(
        f"\nUser Query: Searching for papers related to {molecular_name} with formula {molecular_formula} and isotope {molecular_isotope if molecular_isotope else 'None'}")

    if params['specified_keywords']:
        print(
            f"\nAdditional specified keywords: {', '.join(params['specified_keywords'])}")
    else:
        print(f"\nAdditonal specified keywords: None")

    if params['min_year'] and params['max_year']:
        print(
            f"\nYear range for searching: {params['min_year']}-{params['max_year']} ")
    else:
        print(f"\nYear range: No restriction")

    print(
        f"\nCitation count: At least {params['min_citations']} citations per paper")

    print("\n" + "=" * 70)


def perform_search(processor, molecular_name, molecular_formula, molecular_isotope, params):

    start_time = datetime.now()

    try:
        result = processor.process_query(
            molecular_name=molecular_name,
            molecular_formula=molecular_formula,
            molecular_isotope=molecular_isotope,
            additional_keywords=params['specified_keywords'],
            min_year=params['min_year'],
            max_year=params['max_year'],
            min_citations=params['min_citations'],
            enable_llm_filter=params['enable_llm_filter'],
            llm_filter_threshold=params['llm_filter_threshold']
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        datetime_str = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        if result['success']:
            papers = result['papers']

            print("\n"+"=" * 70)
            print(f"Search completed! (Time spent: {duration:.1f} seconds)")

            if papers:
                # Save results
                saved_csv_file, path = processor.save_results(result)

                print(f"\nFinal results saved to: {path}")
                print(f"Included {len(papers)} papers")

                doi_file = saved_csv_file
                doi_data = pd.read_csv(doi_file)
                doi_list = doi_data['doi'].tolist()

                # Initialize DOIFetcher
                fetcher = DOIFetcher(
                    api_key=ELSEVIER_API_KEY,
                    base_url=ELSEVIER_BASE_URL,
                    rate_limit=10
                )

                # Fetch papers in batches
                results = fetcher.fetch_papers_batch(
                    doi_list=doi_list,
                    output_dir=f"../article_xmls/{datetime_str}"
                )

                print(
                    f"\nSuccessfully fetched {results['successful']} papers in xml format published by Elsevier.")

                # Display preview of top papers
                display_count = min(5, len(papers))
                print(f"\nPreview of top {display_count} papers:")
                print("-" * 70)

                for i, paper in enumerate(papers[:display_count]):
                    title = paper.get('title') or 'N/A'
                    authors = paper.get('authors', [])

                    print(f"{i+1}. {title}")
                    print(
                        f"   Author: {', '.join(authors[:3]) if authors else 'N/A'}")
                    print(f"   Year: {paper.get('year', 'N/A')}")
                    print(
                        f"   Citations: {paper.get('citation_count', 'N/A')}")
                    print(f"   Journal: {paper.get('venue', 'N/A')}")
                    print(f"   Publisher: {paper.get('publisher', 'N/A')}")
                    print(f"   DOI: {paper.get('doi', 'N/A')}")

                    # Display LLM analysis results
                    if 'llm_analysis' in paper:
                        analysis = paper['llm_analysis']
                        score = analysis.get('relevance_score', 0)
                        reasoning = analysis.get('reasoning', 'N/A')[:100] + "..." if len(
                            analysis.get('reasoning', '')) > 100 else analysis.get('reasoning', 'N/A')
                        print(f"   Relevance Score: {score:.1f}")
                        print(f"   Relevence Analysis: {reasoning}")

                    print()
            else:
                print("No papers found matching your criteria.")
                print("\nSuggestions to improve your search:")
                print("   - Lower the year range and citation count strictness")
                print("   - Lower or remove title keyword restrictions")
                print("   - Try more detailed or broader queries")

        else:
            print(f"\nSearch failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\nAn error occurred during the search: {e}")
        import traceback
        traceback.print_exc()


def main():
    """main program - LLM-enhanced literature retrieval tool with multiple search support"""

    # Initialize LLM service once
    processor, use_groq, use_deepseek, use_gemini = initialize_llm_service()
    if processor is None:
        return

    # Main loop for multiple searches
    while True:
        # Get user query
        molecular_name, molecular_formula, molecular_isotope = get_user_query()
        if molecular_name is None or molecular_formula is None:
            continue
        if molecular_isotope is None:
            molecular_isotope = ""

        # Get search parameters
        params = get_search_parameters()

        if molecular_isotope:
            params['specified_keywords'].append(molecular_isotope)

        # Display configuration
        display_search_config(
            molecular_name, molecular_formula, molecular_isotope, params, use_groq, use_deepseek, use_gemini)

        # Confirm search
        confirm = input(
            f"\nConfirm search with above settings? (y/n, defaults to y): ").strip().lower()
        if confirm in ['n', 'no']:
            print("Search cancelled by user.")
        else:
            print(f"\nStart searching")
            print("\n"+"=" * 70)

            # Perform search
            perform_search(processor, molecular_name,
                           molecular_formula, molecular_isotope, params)

        # Ask if user wants to continue
        print("\n" + "=" * 70)
        continue_choice = input(
            "\nDo you want to perform another search? (y/n, defaults to n): ").strip().lower()

        if continue_choice in ['y', 'yes']:
            print("\nStarting new search session...")
            continue
        else:
            print("\nThank you for using the LLM-enhanced literature retrieval tool!")
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
