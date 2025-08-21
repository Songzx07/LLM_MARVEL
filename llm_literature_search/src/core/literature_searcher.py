import os
import csv
import json
import time
import logging
from copy import deepcopy
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any
import requests
from tqdm import tqdm


@dataclass
class SearchStats:
    """Statistics for search operations"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    empty_responses: int = 0
    start_time: float = 0

    def __post_init__(self):
        if self.start_time == 0:
            self.start_time = time.time()


@dataclass
class Paper:
    """Structured representation of a research paper"""
    title: str = ""
    authors: List[str] = None
    year: Optional[int] = None
    venue: str = ""
    doi: str = ""
    abstract: str = ""
    publisher: str = ""
    citation_count: int = 0
    url: str = ""
    doc_type: str = ""
    page: str = ""
    volume: str = ""
    issue: str = ""
    source: str = "crossref"
    llm_analysis: Optional[Dict[str, Any]] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.llm_analysis is None:
            self.llm_analysis = {}
        if self.extra_data is None:
            self.extra_data = {}

    def to_dict(self) -> Dict:
        """Convert Paper object to dictionary for backward compatibility"""
        result = asdict(self)
        if self.extra_data:
            result.update(self.extra_data)
        return result

    def __contains__(self, key):
        """Support 'in' operator"""
        if isinstance(key, str):
            if hasattr(self, key):
                return True
            return key in self.extra_data
        return False

    def __getitem__(self, key):
        """Allow dictionary-style access for backward compatibility"""
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            elif key in self.extra_data:
                return self.extra_data[key]
            else:
                raise KeyError(f"Key '{key}' not found")
        else:
            raise TypeError("Key must be a string")

    def __setitem__(self, key, value):
        """Allow dictionary-style setting for backward compatibility"""
        if isinstance(key, str):
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                self.extra_data[key] = value
        else:
            raise TypeError("Key must be a string")

    def get(self, key, default=None):
        """Allow dict.get() style access for backward compatibility"""
        if isinstance(key, str):
            try:
                return self[key]
            except (KeyError, AttributeError):
                return default
        return default

    def copy(self):
        """Return a deep copy of the Paper object"""
        return deepcopy(self)


class CrossrefAPI:
    """Wrapper for Crossref API interactions"""

    BASE_URL = "https://api.crossref.org/works"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LLM-Literature-Searcher/2.0'
        })
        self.logger = logging.getLogger(__name__)

    def search(self, query: str, filters: List[str], cursor: str = "*",
               rows: int = 1000, timeout: int = 30) -> Dict:
        """Make a search request to Crossref API"""
        params = {
            'query': query,
            'cursor': cursor,
            'rows': rows,
            'sort': 'relevance',
            'order': 'desc'
        }

        if filters:
            params['filter'] = ','.join(filters)

        response = self.session.get(
            self.BASE_URL, params=params, timeout=timeout)

        if response.status_code == 429:
            raise requests.exceptions.HTTPError(
                "Rate limit exceeded", response=response)
        elif response.status_code >= 500:
            raise requests.exceptions.HTTPError(
                "Server error", response=response)

        response.raise_for_status()
        return response.json()


class PaperParser:
    """Parser for converting API responses to Paper objects"""

    @staticmethod
    def parse_crossref_item(item: Dict) -> Optional[Paper]:
        """Parse a Crossref API item into a Paper object"""
        try:
            # Extract title
            title_list = item.get('title', [])
            title = title_list[0] if title_list else ''

            # Extract authors
            authors = []
            for author in item.get('author', []):
                given = author.get('given', '')
                family = author.get('family', '')
                if given and family:
                    authors.append(f"{given} {family}")
                elif family:
                    authors.append(family)

            # Extract year
            year = None
            published_date = (item.get('published-print') or
                              item.get('published-online') or
                              item.get('created'))
            if published_date and 'date-parts' in published_date:
                date_parts = published_date['date-parts'][0]
                if date_parts:
                    year = date_parts[0]

            # Extract venue
            venue = ''
            container_title = item.get('container-title', [])
            if container_title:
                venue = container_title[0]

            # Extract other fields
            doi = item.get('DOI', '')
            url = item.get('URL', '') or (
                f"https://doi.org/{doi}" if doi else '')

            return Paper(
                title=title,
                authors=authors,
                year=year,
                venue=venue,
                doi=doi,
                abstract=item.get('abstract', ''),
                publisher=item.get('publisher', ''),
                citation_count=item.get('is-referenced-by-count', 0),
                url=url,
                doc_type=item.get('type', ''),
                page=item.get('page', ''),
                volume=item.get('volume', ''),
                issue=item.get('issue', '')
            )

        except Exception as e:
            logging.error(f"Failed to parse Crossref item: {e}")
            return None


class FileExporter:
    """Handles exporting papers to various file formats"""

    @staticmethod
    def create_output_directory() -> str:
        """Create timestamped output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_path = f"retrieval_results/{timestamp}"
        os.makedirs(dir_path, exist_ok=True)
        return dir_path

    @staticmethod
    def export_json(papers: List[Paper], filepath: str):
        """Export papers to JSON format"""
        data = {
            'search_metadata': {
                'total_papers': len(papers),
                'search_method': 'LLM-Enhanced Search',
            },
            'papers': [asdict(paper) for paper in papers]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def export_csv(papers: List[Paper], filepath: str):
        """Export titles and DOIs to CSV format"""
        with open(filepath, 'w', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['title', 'doi'])
            writer.writeheader()

            for paper in papers:
                if paper.title or paper.doi:
                    writer.writerow({'title': paper.title, 'doi': paper.doi})

    @staticmethod
    def export_bibtex(papers: List[Paper], filepath: str):
        """Export papers to BibTeX format"""
        with open(filepath, 'w', encoding='utf-8') as bibfile:
            for i, paper in enumerate(papers, 1):
                entry = BibtexFormatter.format_entry(paper, i)
                if entry:
                    bibfile.write(entry + '\n\n')


class BibtexFormatter:
    """Handles BibTeX formatting"""

    TYPE_MAPPING = {
        'journal-article': 'article',
        'conference-paper': 'inproceedings',
        'book-chapter': 'inbook',
        'book': 'book',
        'thesis': 'phdthesis',
        'report': 'techreport',
        'preprint': 'misc',
        'proceedings-article': 'inproceedings'
    }

    BIBTEX_ESCAPES = {
        '{': '\\{', '}': '\\}', '%': '\\%', '$': '\\$',
        '&': '\\&', '#': '\\#', '_': '\\_', '^': '\\^{}',
        '~': '\\textasciitilde{}', '\\': '\\textbackslash{}'
    }

    @classmethod
    def format_entry(cls, paper: Paper, index: int) -> Optional[str]:
        """Format a paper as a BibTeX entry"""
        try:
            citation_key = cls._generate_citation_key(paper, index)
            bibtex_type = cls.TYPE_MAPPING.get(
                paper.doc_type.lower(), 'article')

            lines = [f"@{bibtex_type}{{{citation_key},"]

            if paper.title:
                clean_title = cls._clean_text(paper.title)
                lines.append(f"  title = {{{{{clean_title}}}}},")

            if paper.authors:
                formatted_authors = cls._format_authors(paper.authors)
                lines.append(f"  author = {{{formatted_authors}}},")

            if paper.year:
                lines.append(f"  year = {{{paper.year}}},")

            if paper.venue:
                clean_venue = cls._clean_text(paper.venue)
                field = ("booktitle" if "conference" in paper.venue.lower() or
                         "proceedings" in paper.venue.lower() else "journal")
                lines.append(f"  {field} = {{{clean_venue}}},")

            if paper.doi:
                lines.append(f"  doi = {{{paper.doi}}},")

            if paper.publisher:
                clean_publisher = cls._clean_text(paper.publisher)
                lines.append(f"  publisher = {{{clean_publisher}}},")

            for field, value in [('volume', paper.volume), ('number', paper.issue),
                                 ('pages', paper.page)]:
                if value:
                    lines.append(f"  {field} = {{{value}}},")

            # Remove trailing comma from last line
            if lines[-1].endswith(','):
                lines[-1] = lines[-1][:-1]

            lines.append("}")
            return '\n'.join(lines)

        except Exception as e:
            logging.error(f"Failed to format BibTeX entry: {e}")
            return None

    @classmethod
    def _generate_citation_key(cls, paper: Paper, index: int) -> str:
        """Generate a citation key for the paper"""
        try:
            year_str = str(paper.year)[-2:] if paper.year else ""

            author_parts = []
            for i, author in enumerate(paper.authors[:3]):
                if author:
                    name_parts = author.split()
                    if name_parts:
                        last_name = name_parts[-1]
                        clean_name = ''.join(
                            c for c in last_name if c.isalpha())
                        if clean_name:
                            author_parts.append(clean_name[:2])

            if not author_parts:
                author_parts = ['unknown']

            return f"{year_str}{''.join(author_parts)}"

        except Exception:
            return f"paper{index}"

    @classmethod
    def _format_authors(cls, authors: List[str]) -> str:
        """Format authors for BibTeX"""
        formatted = []
        for author in authors:
            author = author.strip()
            if not author:
                continue

            if ',' in author:
                formatted.append(author)
            else:
                parts = author.split()
                if len(parts) >= 2:
                    last = parts[-1]
                    first_middle = ' '.join(parts[:-1])
                    formatted.append(f"{last}, {first_middle}")
                else:
                    formatted.append(author)

        return ' and '.join(formatted)

    @classmethod
    def _clean_text(cls, text: str) -> str:
        """Clean text for BibTeX format"""
        if not text:
            return ""

        for char, replacement in cls.BIBTEX_ESCAPES.items():
            text = text.replace(char, replacement)

        return text


class LiteratureSearcher:
    """Main class for literature searching with improved architecture"""

    def __init__(self):
        self.api = CrossrefAPI()
        self.parser = PaperParser()
        self.logger = logging.getLogger(__name__)

        # Default search parameters
        self.rows_per_page = 1000
        self.papers_per_year = 2000
        self.max_retries = 5
        self.request_timeout = 30

        # Setup logging
        logging.basicConfig(level=logging.INFO,
                            format="%(levelname)s: %(message)s")

    def search(self, base_keywords: List[str],
               additional_keywords: List[str],
               min_year: int = 1900,
               max_year: Optional[int] = None) -> List[Paper]:
        """Search using multiple keyword strategies with year splitting"""
        if max_year is None:
            max_year = datetime.now().year

        all_papers = []

        # Combine all keywords for comprehensive search
        all_keywords = base_keywords.copy()
        if additional_keywords:
            all_keywords.extend(additional_keywords)
        all_keywords = list(dict.fromkeys(all_keywords))

        try:
            papers = self._search_with_year_splitting(
                all_keywords, min_year, max_year)
            all_papers.extend(papers)
            self.logger.info(f"Found {len(papers)} papers")
        except Exception as e:
            self.logger.error(f"Search failed: {e}")

        return all_papers

    def filter_papers_citations_only(self, papers: List[Paper],
                                     min_citations: int = 1) -> List[Paper]:
        """Filter papers by minimum citation count"""
        return [p for p in papers if p.citation_count >= min_citations]

    def save_results(self, papers: List[Paper]) -> Tuple[str, str]:
        """Save search results to files"""
        dir_path = FileExporter.create_output_directory()
        base_filename = os.path.join(dir_path, "literature_search")

        # Export in all formats
        FileExporter.export_json(papers, f"{base_filename}.json")
        csv_filename = f"{base_filename}_titles_dois.csv"
        FileExporter.export_csv(papers, csv_filename)
        FileExporter.export_bibtex(papers, f"{base_filename}.bib")

        self.logger.info(f"Results saved to {dir_path}")
        return csv_filename, dir_path

    def _search_with_pagination(self, keywords: List[str],
                                per_year_limit: int, min_year: int, max_year: int) -> List[Paper]:
        """Search with cursor-based pagination"""
        query = " ".join(keywords)
        filters = self._build_filters(min_year, max_year)

        papers = []
        cursor = "*"
        stats = SearchStats()

        with tqdm(total=per_year_limit, desc=f"Searching {min_year}-{max_year}", bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt}") as pbar:
            while len(papers) < per_year_limit and cursor:
                try:
                    stats.total_requests += 1

                    data = self.api.search(
                        query=query,
                        filters=filters,
                        cursor=cursor,
                        rows=self.rows_per_page,
                        timeout=self.request_timeout
                    )

                    stats.successful_requests += 1

                    items = data.get('message', {}).get('items', [])
                    cursor = data.get('message', {}).get('next-cursor')

                    if not items:
                        stats.empty_responses += 1
                        self.logger.debug("No more items found")
                        break

                    batch_count = 0
                    for item in items:
                        if len(papers) >= per_year_limit:
                            break

                        paper = self.parser.parse_crossref_item(item)
                        if paper:
                            papers.append(paper)
                            batch_count += 1

                    pbar.update(batch_count)

                    # Rate limiting
                    sleep_time = 1.0 if len(papers) > 10000 else 0.5
                    time.sleep(sleep_time)

                except requests.exceptions.HTTPError as e:
                    stats.failed_requests += 1
                    if "Rate limit" in str(e):
                        self.logger.warning("Rate limit hit, waiting...")
                        time.sleep(60)
                        continue
                    elif stats.failed_requests >= self.max_retries:
                        self.logger.error("Too many failed requests, stopping")
                        break
                    time.sleep(10)

                except Exception as e:
                    stats.failed_requests += 1
                    self.logger.error(f"Search error: {e}")
                    if stats.failed_requests >= self.max_retries:
                        break
                    time.sleep(10)

        return papers

    def _search_with_year_splitting(self, keywords: List[str],
                                    min_year: int, max_year: int) -> List[Paper]:
        """Split large queries into yearly searches"""
        all_papers = []

        self.logger.info(
            f"Splitting query into yearly searches ({min_year}-{max_year})")

        for year in range(min_year, max_year + 1):
            self.logger.info(f"Searching year {year}...")

            try:
                yearly_papers = self._search_with_pagination(
                    keywords, self.papers_per_year, year, year)
                all_papers.extend(yearly_papers)

            except Exception as e:
                self.logger.error(f"Error searching year {year}: {e}")

            time.sleep(1)

        return all_papers

    def _build_filters(self, min_year: int, max_year: int) -> List[str]:
        """Build Crossref API filters"""
        filters = []
        if min_year:
            filters.append(f"from-pub-date:{min_year}")
        if max_year:
            filters.append(f"until-pub-date:{max_year}")
        return filters
