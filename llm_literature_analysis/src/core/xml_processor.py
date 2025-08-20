import xml.etree.ElementTree as ET
import re
import csv
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime


class XMLProcessor:
    """
    XML Processor for extracting content from scientific papers

    This class handles:
    1. Content extraction (abstract, body, tables)
    2. Table data extraction and CSV export
    3. Text formatting for LLM processing
    """

    def __init__(self):
        self.setup_logging()
        self.namespaces = self._get_namespaces()

    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def _get_namespaces() -> Dict[str, str]:
        """Define XML namespaces used in scientific papers"""
        return {
            'ce': 'http://www.elsevier.com/xml/common/dtd',
            'sb': 'http://www.elsevier.com/xml/common/struct-bib/dtd',
            'dc': 'http://purl.org/dc/elements/1.1/',
            'prism': 'http://prismstandard.org/namespaces/basic/2.0/',
            'ja': 'http://www.elsevier.com/xml/ja/dtd',
            'xocs': 'http://www.elsevier.com/xml/xocs/dtd',
            'mml': 'http://www.w3.org/1998/Math/MathML',
            'tb': 'http://www.elsevier.com/xml/common/table/dtd',
            'sa': 'http://www.elsevier.com/xml/common/struct-aff/dtd',
            'xlink': 'http://www.w3.org/1999/xlink',
            'bk': 'http://www.elsevier.com/xml/bk/dtd',
            'cals': 'http://www.elsevier.com/xml/common/cals/dtd',
            'dcterms': 'http://purl.org/dc/terms/',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }

    # ==================== Main Content Extraction ====================

    def extract_content_from_xml(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Extract complete content from XML file

        Args:
            xml_file_path: Path to XML file

        Returns:
            Dictionary containing abstract, body content, and tables
        """
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            result = {
                'abstract': self._extract_abstract(root),
                'body_content': self._extract_body_content(root),
                'tables': self._extract_table_titles(root),
            }

            self.logger.info(
                f"Successfully extracted content from {xml_file_path}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to extract content from XML: {e}")
            raise

    def format_for_llm(self, extracted_content: Dict[str, Any]) -> str:
        """
        Format extracted content for LLM processing

        Args:
            extracted_content: Content extracted from XML

        Returns:
            Formatted string for LLM input
        """
        try:
            parts = ["=== PAPER ANALYSIS ==="]

            # Add abstract
            abstract = extracted_content.get('abstract', {})
            if abstract.get('author_abstract'):
                parts.append(f"Abstract: {abstract['author_abstract']}")

            # Add main content
            body_content = extracted_content.get('body_content', {})
            if body_content.get('full_text'):
                parts.append(f"Main Content: {body_content['full_text']}")

            # Add table information
            tables = extracted_content.get('tables', {}).get('tables', [])
            for table in tables:
                label = table.get('label', 'No Label')
                caption = table.get('caption', 'No Caption')
                parts.append(f"{label}: {caption}")

            return '\n'.join(parts)

        except Exception as e:
            self.logger.error(f"Failed to format content for LLM: {e}")
            return "Error formatting content for LLM"

    # ==================== Abstract Extraction ====================

    def _extract_abstract(self, root) -> Dict[str, str]:
        """Extract abstract information from XML root"""
        abstract_info = {}

        try:
            # Try multiple methods to find abstract elements
            abstract_elements = self._find_elements_multi_method(
                root, 'abstract', ['.//ce:abstract', './/abstract']
            )

            for abstract in abstract_elements:
                class_attr = abstract.get('class', '')
                abstract_text = self._extract_text_with_formatting(abstract)

                if not abstract_text.strip():
                    continue

                if class_attr == 'author':
                    abstract_info['author_abstract'] = abstract_text
                elif class_attr == 'graphical':
                    abstract_info['graphical_abstract'] = abstract_text
                elif not abstract_info:  # First abstract found
                    abstract_info['author_abstract'] = abstract_text

        except Exception as e:
            self.logger.error(f"Failed to extract abstract: {e}")

        return abstract_info

    # ==================== Body Content Extraction ====================

    def _extract_body_content(self, root) -> Dict[str, Any]:
        """Extract body content from XML root"""
        body_content = {'sections': [], 'full_text': ''}

        try:
            # Find body element using multiple methods
            body = self._find_body_element(root)
            if not body:
                self.logger.warning("No body element found")
                return body_content

            # Extract sections
            sections = self._find_elements_multi_method(
                body, 'section', ['.//ce:section', './/section']
            )

            self.logger.info(f"Found {len(sections)} section elements")

            for section in sections:
                section_info = self._extract_section(section)
                if section_info:
                    body_content['sections'].append(section_info)

            # Extract full text
            body_content['full_text'] = self._extract_all_text_from_body(body)

        except Exception as e:
            self.logger.error(f"Failed to extract body content: {e}")

        return body_content

    def _find_body_element(self, root):
        """Find body element using multiple strategies"""
        methods = [
            lambda: root.findall('.//body'),
            lambda: root.findall('.//ce:body', self.namespaces),
            lambda: [elem for elem in self._find_elements_by_tag_name(root, 'body')
                     if not elem.tag.endswith('tbody')]
        ]

        for method in methods:
            try:
                bodies = method()
                if bodies:
                    self.logger.info(f"Found body element: {bodies[0].tag}")
                    return bodies[0]
            except Exception:
                continue

        return None

    def _extract_all_text_from_body(self, body_element) -> str:
        """Extract all text content from body element"""
        if not body_element:
            return ""

        try:
            # Find all paragraph elements
            paragraphs = self._find_elements_multi_method(
                body_element, 'paragraph',
                ['.//ce:para', './/para', './/p']
            )

            self.logger.info(f"Found {len(paragraphs)} paragraph elements")

            text_parts = []
            for para in paragraphs:
                para_text = self._extract_text_with_formatting(para)
                if para_text.strip():
                    text_parts.append(para_text.strip())

            # Fallback: extract body text directly if no paragraphs found
            if not text_parts:
                self.logger.info(
                    "No paragraphs found, extracting body text directly")
                body_text = self._extract_text_with_formatting(body_element)
                if body_text.strip():
                    text_parts.append(body_text.strip())

            return '\n\n'.join(text_parts)

        except Exception as e:
            self.logger.error(f"Failed to extract text from body: {e}")
            return ""

    def _extract_section(self, section) -> Dict[str, Any]:
        """Extract information from a section element"""
        section_info = {}

        try:
            # Extract label
            label = self._find_element_multi_method(
                section, ['.//ce:label', './/label']
            )
            if label is not None and label.text:
                section_info['label'] = label.text.strip()

            # Extract title
            title = self._find_element_multi_method(
                section, ['.//ce:section-title',
                          './/section-title', './/title']
            )
            if title is not None:
                section_info['title'] = self._extract_text_with_formatting(
                    title)

            # Extract content paragraphs
            paragraphs = self._find_elements_multi_method(
                section, 'paragraph',
                ['.//ce:para', './/para', './/p']
            )

            content = []
            for para in paragraphs:
                para_text = self._extract_text_with_formatting(para)
                if para_text.strip():
                    content.append(para_text.strip())

            if content:
                section_info['content'] = content
            else:
                # Fallback: extract section text directly
                section_text = self._extract_text_with_formatting(section)
                if section_text.strip():
                    section_info['content'] = [section_text.strip()]

        except Exception as e:
            self.logger.error(f"Failed to extract section: {e}")

        return section_info

    # ==================== Table Extraction ====================

    def _extract_table_titles(self, root) -> Dict[str, List[Dict[str, str]]]:
        """Extract table titles and captions from XML"""
        tables = {'tables': []}

        try:
            table_elements = self._find_elements_multi_method(
                root, 'table', ['.//ce:table', './/table']
            )

            for table in table_elements:
                table_info = {}

                # Extract label
                label = self._find_element_multi_method(
                    table, ['.//ce:label', './/label']
                )
                if label is not None and label.text:
                    table_info['label'] = label.text

                # Extract caption
                caption = self._find_element_multi_method(
                    table, ['.//ce:caption', './/caption']
                )
                if caption is not None:
                    table_info['caption'] = self._extract_text_with_formatting(
                        caption)

                if table_info:
                    tables['tables'].append(table_info)

        except Exception as e:
            self.logger.error(f"Failed to extract tables: {e}")

        return tables

    # ==================== Table Data Extraction ====================

    def extract_table_data_by_title(self, xml_file_path: str, table_title: str,
                                    uncertainty: str = "", timestamp: str = "") -> bool:
        """
        Extract specific table data by title and save to files

        Args:
            xml_file_path: Path to XML file
            table_title: Title of target table
            uncertainty: Uncertainty information
            timestamp: Timestamp for output folder

        Returns:
            True if successful, False otherwise
        """
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Extract metadata
            doi = self._extract_doi(root) or "unknown_doi"
            safe_doi = re.sub(r'[^\w\-_.]', '_', doi)
            table_name = table_title[:7]

            # Find and extract target table
            target_table = self._find_table_by_title(root, table_title)
            if not target_table:
                self.logger.error(
                    f"Table '{table_title}' not found in {xml_file_path}")
                return False

            table_data = self._extract_table_structure(target_table)
            if not table_data:
                self.logger.error("Failed to extract table structure or data")
                return False

            # Save table files
            output_folder = Path("analysis_results") / \
                timestamp / f"{safe_doi}_table_data"
            output_folder.mkdir(parents=True, exist_ok=True)

            success = self._save_table_files(
                table_data, table_title, uncertainty, doi, output_folder, table_name
            )

            if success:
                self.logger.info(
                    f"Table data saved successfully: {output_folder}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to extract table data: {e}")
            return False

    def _find_table_by_title(self, root, table_title: str):
        """Find table element by matching title"""
        try:
            target_title = table_title.strip().lower()
            table_elements = self._find_elements_multi_method(
                root, 'table', ['.//ce:table', './/table']
            )

            for table in table_elements:
                label = self._find_element_multi_method(
                    table, ['.//ce:label', './/label']
                )

                if label is not None and label.text:
                    table_label = label.text.strip().lower()
                    if target_title in table_label or table_label in target_title:
                        return table

            return None

        except Exception as e:
            self.logger.error(
                f"Failed to find table by title '{table_title}': {e}")
            return None

    def _extract_table_structure(self, table_element) -> Optional[Dict[str, Any]]:
        """Extract complete table structure including data"""
        try:
            table_data = {
                'label': '',
                'caption': '',
                'headers': [],
                'rows': [],
                'footnotes': [],
                'colspec': {}
            }

            # Extract basic info
            self._extract_table_metadata(table_element, table_data)

            # Find table body
            tgroup = self._find_element_multi_method(
                table_element, ['.//tgroup', './/ce:tgroup', './/cals:tgroup']
            )

            if tgroup is not None:
                # Extract table structure and data
                table_data['colspec'] = self._extract_colspec(tgroup)
                all_rows = self._find_all_rows(tgroup)
                thead_rows, tbody_rows = self._separate_header_data_rows(
                    tgroup, all_rows)

                # Process headers and data rows
                table_data['headers'] = [
                    self._extract_row_cells(row, table_data['colspec'])
                    for row in thead_rows
                ]
                table_data['rows'] = [
                    self._extract_row_cells(row, table_data['colspec'])
                    for row in tbody_rows
                ]

                # Remove empty rows
                table_data['headers'] = [h for h in table_data['headers'] if h]
                table_data['rows'] = [r for r in table_data['rows'] if r]

            # Extract footnotes
            self._extract_table_footnotes(table_element, table_data)

            self.logger.info(
                f"Extracted table structure: {table_data['label']}")
            return table_data

        except Exception as e:
            self.logger.error(f"Failed to extract table structure: {e}")
            return None

    def _extract_table_metadata(self, table_element, table_data: Dict[str, Any]):
        """Extract table label and caption"""
        # Extract label
        label = self._find_element_multi_method(
            table_element, ['.//ce:label', './/label']
        )
        if label is not None and label.text:
            table_data['label'] = label.text.strip()

        # Extract caption
        caption = self._find_element_multi_method(
            table_element, ['.//ce:caption', './/caption']
        )
        if caption is not None:
            table_data['caption'] = self._extract_text_with_formatting(caption)

    # ==================== Table Structure Processing ====================

    def _find_all_rows(self, tgroup) -> List:
        """Find all row elements in tgroup"""
        methods = [
            lambda: tgroup.findall('.//row'),
            lambda: tgroup.findall('.//ce:row', self.namespaces),
            lambda: self._find_elements_by_tag_name(tgroup, 'row'),
            lambda: [e for e in tgroup.iter() if e.tag.split('}')[-1] == 'row']
        ]

        for method in methods:
            try:
                rows = method()
                if rows:
                    return rows
            except Exception:
                continue

        return []

    def _separate_header_data_rows(self, tgroup, all_rows) -> Tuple[List, List]:
        """Separate header and data rows"""
        thead_rows = []
        tbody_rows = []

        # Find thead
        thead = self._find_element_multi_method(
            tgroup, ['.//thead', './/ce:thead']
        )
        if thead is not None:
            thead_rows = self._find_elements_multi_method(
                thead, 'row', ['.//row', './/ce:row']
            )

        # Find tbody
        tbody = self._find_element_multi_method(
            tgroup, ['.//tbody', './/ce:tbody']
        )
        if tbody is not None:
            tbody_rows = self._find_elements_multi_method(
                tbody, 'row', ['.//row', './/ce:row']
            )
        else:
            # If no tbody, assume remaining rows are data rows
            tbody_rows = [row for row in all_rows if row not in thead_rows]

        return thead_rows, tbody_rows

    def _extract_colspec(self, tgroup) -> Dict[str, int]:
        """Extract column specifications"""
        colspec_map = {}

        try:
            colspecs = self._find_elements_multi_method(
                tgroup, 'colspec', ['.//colspec',
                                    './/ce:colspec', './/cals:colspec']
            )

            for idx, colspec in enumerate(colspecs):
                colname = colspec.get('colname')
                if colname:
                    colspec_map[colname] = idx

            # Fallback: infer from cols attribute
            if not colspec_map:
                cols = tgroup.get('cols')
                if cols:
                    try:
                        total_cols = int(cols)
                        colspec_map = {
                            f"col{i+1}": i for i in range(total_cols)}
                    except ValueError:
                        pass

        except Exception as e:
            self.logger.error(f"Failed to extract colspec: {e}")

        return colspec_map

    def _extract_row_cells(self, row, colspec: Dict[str, int]) -> List[Dict[str, str]]:
        """Extract cells from a row element"""
        try:
            entries = self._find_elements_multi_method(
                row, 'entry', ['.//entry', './/ce:entry', 'entry']
            )

            row_cells = []
            for entry in entries:
                cell_text = self._extract_text_with_formatting(entry)
                colspan = self._calculate_colspan(
                    entry.get('namest'), entry.get('nameend'), colspec
                )

                row_cells.append({
                    'text': cell_text,
                    'align': entry.get('align', 'left'),
                    'morerows': entry.get('morerows', '0'),
                    'namest': entry.get('namest'),
                    'nameend': entry.get('nameend'),
                    'colspan': str(colspan)
                })

            return row_cells

        except Exception as e:
            self.logger.error(f"Failed to extract row cells: {e}")
            return []

    def _calculate_colspan(self, namest: Optional[str], nameend: Optional[str],
                           colspec: Dict[str, int]) -> int:
        """Calculate colspan from namest/nameend attributes"""
        try:
            if not namest or not nameend:
                return 1

            # Use colspec mapping if available
            if colspec and namest in colspec and nameend in colspec:
                return max(1, colspec[nameend] - colspec[namest] + 1)

            # Extract numbers from attribute names
            start_match = re.search(r'(\d+)', namest)
            end_match = re.search(r'(\d+)', nameend)

            if start_match and end_match:
                start_num = int(start_match.group(1))
                end_num = int(end_match.group(1))
                return max(1, end_num - start_num + 1)

            return 1

        except Exception as e:
            self.logger.error(f"Failed to calculate colspan: {e}")
            return 1

    def _extract_table_footnotes(self, table_element, table_data: Dict[str, Any]):
        """Extract table footnotes"""
        try:
            # Extract legend
            legend = self._find_element_multi_method(
                table_element, ['.//ce:legend', './/legend']
            )
            if legend is not None:
                footnote_text = self._extract_text_with_formatting(legend)
                if footnote_text.strip():
                    table_data['footnotes'].append(footnote_text)

            # Extract table footnotes
            footnotes = self._find_elements_multi_method(
                table_element, 'footnote', [
                    './/ce:table-footnote', './/table-footnote']
            )

            for footnote in footnotes:
                footnote_id = footnote.get('id', '')
                note_para = self._find_element_multi_method(
                    footnote, ['.//ce:note-para', './/note-para']
                )

                if note_para is not None:
                    footnote_text = self._extract_text_with_formatting(
                        note_para)
                    if footnote_text.strip():
                        table_data['footnotes'].append(
                            f"[{footnote_id}] {footnote_text}")

        except Exception as e:
            self.logger.error(f"Failed to extract table footnotes: {e}")

    # ==================== File Output ====================

    def _save_table_files(self, table_data: Dict[str, Any], table_title: str,
                          uncertainty: str, doi: str, output_folder: Path,
                          table_name: str) -> bool:
        """Save table data as CSV and metadata as TXT"""
        try:
            csv_success = self._save_table_csv(
                table_data, output_folder, table_name)
            txt_success = self._save_table_info(
                table_data, table_title, uncertainty, doi, output_folder, table_name
            )
            return csv_success and txt_success

        except Exception as e:
            self.logger.error(f"Failed to save table files: {e}")
            return False

    def _save_table_csv(self, table_data: Dict[str, Any], output_folder: Path,
                        table_name: str) -> bool:
        """Save table data as CSV file"""
        try:
            csv_file = output_folder / f"{table_name}_table_data.csv"
            matrix = self._create_table_matrix(table_data)

            if not matrix:
                self.logger.warning("No data to save in CSV file.")
                return True

            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                for row in matrix:
                    cleaned_row = [
                        str(cell or "").strip().replace(
                            '\n', ' ').replace('\r', '')
                        for cell in row
                    ]
                    writer.writerow(cleaned_row)

            self.logger.info(f"CSV file saved: {csv_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save CSV file: {e}")
            return False

    def _save_table_info(self, table_data: Dict[str, Any], table_title: str,
                         uncertainty: str, doi: str, output_folder: Path,
                         table_name: str) -> bool:
        """Save table metadata as TXT file"""
        try:
            txt_file = output_folder / f"{table_name}_table_info.txt"

            lines = [
                "=" * 80,
                f"Paper DOI: {doi}",
                f"Table Title: {table_title}",
                "=" * 80,
                ""
            ]

            # Add table metadata
            if table_data['label']:
                lines.append(f"Table Label: {table_data['label']}")
            if table_data['caption']:
                lines.append(f"Table Caption: {table_data['caption']}")
            lines.append("")

            # Add uncertainty info
            if uncertainty:
                lines.extend([f"Uncertainty Information: {uncertainty}", ""])

            # Add footnotes
            if table_data['footnotes']:
                lines.extend([
                    "FOOTNOTES:",
                    "-" * 40
                ])
                for i, footnote in enumerate(table_data['footnotes'], 1):
                    lines.append(f"  {i}. {footnote}")
                lines.append("")

            # Add file information
            lines.extend([
                "FILE INFORMATION:",
                "-" * 40,
                f"CSV data file: {table_name}_table_data.csv",
                f"Info file: {table_name}_table_info.txt",
                f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "=" * 80
            ])

            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))

            self.logger.info(f"TXT file saved: {txt_file}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save TXT file: {e}")
            return False

    def _create_table_matrix(self, table_data: Dict[str, Any]) -> List[List[str]]:
        """Create matrix representation of table data"""
        try:
            total_rows = len(table_data['headers']) + len(table_data['rows'])
            max_cols = self._calculate_max_columns(table_data)

            if total_rows == 0 or max_cols == 0:
                return []

            # Create empty matrix
            matrix = [[None for _ in range(max_cols)]
                      for _ in range(total_rows)]

            # Fill matrix with data
            current_row = 0
            for header_row in table_data['headers']:
                self._fill_matrix_row(
                    matrix, current_row, header_row, max_cols)
                current_row += 1

            for data_row in table_data['rows']:
                self._fill_matrix_row(matrix, current_row, data_row, max_cols)
                current_row += 1

            return matrix

        except Exception as e:
            self.logger.error(f"Failed to create table matrix: {e}")
            return []

    def _calculate_max_columns(self, table_data: Dict[str, Any]) -> int:
        """Calculate maximum number of columns"""
        max_cols = 0
        for row in table_data['headers'] + table_data['rows']:
            current_col = sum(int(cell.get('colspan', '1')) for cell in row)
            max_cols = max(max_cols, current_col)
        return max_cols

    def _fill_matrix_row(self, matrix: List[List[str]], row_idx: int,
                         row_data: List[Dict[str, str]], max_cols: int):
        """Fill matrix row with cell data handling rowspan/colspan"""
        try:
            col_idx = 0
            for cell in row_data:
                # Find next empty column
                while col_idx < max_cols and matrix[row_idx][col_idx] is not None:
                    col_idx += 1

                if col_idx >= max_cols:
                    break

                cell_text = cell['text'] or ""
                rowspan = int(cell.get('morerows', '0')) + 1
                colspan = int(cell.get('colspan', '1'))

                # Fill cell with rowspan/colspan consideration
                for r in range(rowspan):
                    for c in range(colspan):
                        target_row = row_idx + r
                        target_col = col_idx + c

                        if target_row < len(matrix) and target_col < max_cols:
                            matrix[target_row][target_col] = cell_text if (
                                r == 0 and c == 0) else ""

                col_idx += colspan

        except Exception as e:
            self.logger.error(f"Failed to fill matrix row: {e}")

    # ==================== Text Processing ====================

    def _extract_text_with_formatting(self, element) -> str:
        """Extract text from XML element with formatting preservation"""
        if element is None:
            return ""

        def process_element(elem):
            """Recursively process XML element to extract formatted text"""
            result = elem.text or ""

            for child in elem:
                tag_name = child.tag.split('}')[-1].lower()
                child_text = process_element(child)

                if tag_name in ['sup', 'superscript']:
                    result += f"^{{{child_text}}}" if child_text else ""
                elif tag_name in ['sub', 'subscript', 'inf']:
                    result += f"_{{{child_text}}}" if child_text else ""
                elif tag_name in ['math', 'formula', 'equation']:
                    result += f"${child_text}$" if child_text else ""
                elif tag_name in ['br', 'break']:
                    result += " "
                elif tag_name in self._get_greek_symbols():
                    result += self._get_greek_symbols().get(tag_name, tag_name) + child_text
                else:
                    result += child_text

                result += child.tail or ""

            return result

        try:
            text = process_element(element)
            return re.sub(r'\s+', ' ', text).strip()
        except Exception as e:
            self.logger.error(f"Failed to extract formatted text: {e}")
            return ''.join(element.itertext()).strip() if element is not None else ""

    @staticmethod
    def _get_greek_symbols() -> Dict[str, str]:
        """Get mapping of Greek letter names to Unicode symbols"""
        return {
            'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ',
            'epsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ',
            'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ',
            'nu': 'ν', 'xi': 'ξ', 'omicron': 'ο', 'pi': 'π',
            'rho': 'ρ', 'sigma': 'σ', 'tau': 'τ', 'upsilon': 'υ',
            'phi': 'φ', 'chi': 'χ', 'psi': 'ψ', 'omega': 'ω'
        }

    # ==================== Utility Methods ====================

    def _extract_doi(self, root) -> str:
        """Extract DOI from XML root element"""
        try:
            for xpath in ['.//dc:identifier', './/prism:doi', './/ce:doi']:
                doi_elem = root.find(xpath, self.namespaces)
                if doi_elem is not None and doi_elem.text:
                    return doi_elem.text.replace('doi:', '')
            return ""
        except Exception as e:
            self.logger.error(f"Failed to extract DOI: {e}")
            return ""

    def _find_elements_by_tag_name(self, root, tag_name: str) -> List:
        """Find elements by tag name, ignoring namespaces"""
        found_elements = []
        for elem in root.iter():
            local_tag = elem.tag.split(
                '}')[-1] if '}' in elem.tag else elem.tag
            if local_tag == tag_name:
                found_elements.append(elem)
        return found_elements

    def _find_element_multi_method(self, root, xpaths: List[str]):
        """Find single element using multiple XPath methods"""
        # Try with namespaces first
        for xpath in xpaths:
            try:
                element = root.find(xpath, self.namespaces)
                if element is not None:
                    return element
            except Exception:
                continue

        # Try without namespaces
        for xpath in xpaths:
            try:
                element = root.find(xpath)
                if element is not None:
                    return element
            except Exception:
                continue

        # Try with tag name search
        for xpath in xpaths:
            tag_name = xpath.split('/')[-1].split(':')[-1]
            elements = self._find_elements_by_tag_name(root, tag_name)
            if elements:
                return elements[0]

        return None

    def _find_elements_multi_method(self, root, element_type: str, xpaths: List[str]) -> List:
        """Find elements using multiple XPath methods"""
        found_elements = []

        # Try with namespaces first
        for xpath in xpaths:
            try:
                elements = root.findall(xpath, self.namespaces)
                if elements:
                    found_elements.extend(elements)
            except Exception:
                continue

        # If nothing found, try without namespaces
        if not found_elements:
            for xpath in xpaths:
                try:
                    elements = root.findall(xpath)
                    if elements:
                        found_elements.extend(elements)
                except Exception:
                    continue

        # If still nothing found, try tag name search
        if not found_elements:
            for xpath in xpaths:
                tag_name = xpath.split('/')[-1].split(':')[-1]
                elements = self._find_elements_by_tag_name(root, tag_name)
                if elements:
                    found_elements.extend(elements)

        return found_elements
