from typing import List, Dict
from .keyword_extractor import KeywordExtractor
from .literature_searcher import LiteratureSearcher
from .paper_filter import LLMPaperFilter


class LLMProcessor:
    """LLM based Literature Search and Filtering Service"""

    def __init__(self, use_groq: bool = True, use_gemini: bool = True):
        """
        Initialize LLM Service

        Args:
            use_groq: True if Groq API is used, False otherwise
            use_deepseek: True if DeepSeek API is used for LLM filtering, False otherwise
        """
        self.use_groq = use_groq
        self.use_gemini = use_gemini
        self.keyword_extractor = KeywordExtractor(use_groq=self.use_groq)
        self.literature_searcher = LiteratureSearcher()
        self.paper_filter = LLMPaperFilter(use_gemini=self.use_gemini)

    def process_query(self, molecular_name: str,
                      molecular_formula: str,
                      molecular_isotope: str,
                      additional_keywords: List[str] = None,
                      min_year: int = None,
                      max_year: int = None,
                      min_citations: int = 1,
                      enable_llm_filter: bool = True,
                      llm_filter_threshold: float = 0.8) -> Dict:
        """Process user query to search and filter literature"""

        print(
            f"\nUser Query: Searching for papers related to {molecular_name} with formula {molecular_formula} and isotope {molecular_isotope if molecular_isotope else 'None'}")

        print(
            f"\nDesignated title keywords: {', '.join(additional_keywords)}")

        if min_year or max_year:
            year_desc = []
            if min_year:
                year_desc.append(f"After {min_year}")
            if max_year:
                year_desc.append(f"Before {max_year}")
            print(f"\nYear range restriction: {' and '.join(year_desc)}")

        # 1. Use LLM to extract keywords from user input
        keywords = self.keyword_extractor.extract_keywords(
            molecular_name, molecular_formula, molecular_isotope)

        if not keywords:
            return {
                'success': False,
                'error': "Failed to conclude keywords based on user's query.",
                'specified_keywords': additional_keywords or [],
                'keywords': [],
                'papers': []
            }

        # 2. Use keywords to search literature (with year settings)
        papers = self.literature_searcher.search(
            base_keywords=keywords,
            additional_keywords=additional_keywords,
            min_year=min_year,
            max_year=max_year)

        # 3. Filter papers based on quality and relevance
        citation_filtered_papers = self.literature_searcher.filter_papers_citations_only(
            papers,
            min_citations=min_citations
        )

        print(
            f"\nFound {len(citation_filtered_papers)} papers after citation filtering.")

        if citation_filtered_papers:
            print("\n" + "=" * 70)
            print("LLM Paper Filtering...")
            print("=" * 70)

            # Apply LLM-based filtering on titles
            final_papers = self.paper_filter.filter_papers_by_title(
                citation_filtered_papers,
                molecular_name,
                molecular_formula,
                molecular_isotope,
                batch_size=100,
                min_score=llm_filter_threshold
            )

        else:
            print("\nNo papers found after quality filtering, skipping LLM filtering.")

        final_papers = sorted(
            final_papers, key=lambda x: x['year'], reverse=True)

        # 4. Return the final search result
        result = {
            'success': True,
            'molecular_name': molecular_name,
            'molecular_formula': molecular_formula,
            'molecular_isotope': molecular_isotope,
            'specified_keywords': additional_keywords or [],
            'extracted_keywords': keywords,
            'search_keywords': list(set(keywords + (additional_keywords or []))),
            'total_found': len(papers),
            'final_count': len(final_papers),
            'papers': final_papers,
            'search_metadata': {
                'min_year': min_year,
                'max_year': max_year,
                'min_citations': min_citations,
                'llm_filter_applied': enable_llm_filter,
                'llm_filter_threshold': llm_filter_threshold if enable_llm_filter else None,
            }
        }

        return result

    def save_results(self, search_result: Dict) -> str:
        """Save search results to a file"""
        return self.literature_searcher.save_results(
            search_result['papers'])
