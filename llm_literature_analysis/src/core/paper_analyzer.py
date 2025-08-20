import os
from pathlib import Path
from typing import Dict, Any
from .llm_client import LLMClient
from .xml_processor import XMLProcessor
import logging


class PaperAnalyzer:
    """Paper Analyzer Class"""

    def __init__(self, use_gemini: bool = True):

        self.use_gemini = use_gemini
        if self.use_gemini:
            self.llm_client = LLMClient()
        else:
            self.llm_client = None
            print("Gemini API service is not available.")
            self.logger = logging.getLogger(__name__)
            return

        self.xml_processor = XMLProcessor()
        self.logger = logging.getLogger(__name__)

    def analyze_paper_from_xml(self, xml_file_path: str) -> Dict[str, Any]:
        """
        Analyze a paper from an XML file

        Args:
            xml_file_path: xml file path

        Returns:
            Analysis result as a dictionary
        """
        try:
            if not os.path.exists(xml_file_path):
                raise FileNotFoundError(
                    f"XML file does not exist: {xml_file_path}")

            self.logger.info(f"Analyzing paper: {xml_file_path}")

            # Extract content from XML
            self.logger.info("Extracting content from XML...")
            extracted_content = self.xml_processor.extract_content_from_xml(
                xml_file_path)

            if not extracted_content:
                analyze_result = False
                return analyze_result

            # Format content for LLM
            self.logger.info("Formatting content for LLM...")
            formatted_content = self.xml_processor.format_for_llm(
                extracted_content)

            # Call LLM for analysis
            self.logger.info("Calling LLM for analysis...")
            llm_result = self.llm_client.analyze_paper(
                formatted_content)

            # Check if LLM result is valid
            result = {
                'file_path': xml_file_path,
                'llm_analysis': llm_result,
            }

            return result

        except Exception as e:
            self.logger.error(f"Failed to analyze paper from XML: {e}")
            return {
                'file_path': xml_file_path,
                'error': str(e),
                'success': False
            }

    def batch_analyze(self, xml_folder_path: str) -> Dict[str, Any]:
        """
        Analyze multiple papers from a folder containing XML files

        Args:
            xml_folder_path: XML folder path

        Returns:
            A dictionary containing the results of the analysis
        """
        folder_path = Path(xml_folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(
                f"The folder does not exist: {xml_folder_path}")

        xml_files = list(folder_path.glob("*.xml"))
        if not xml_files:
            return {
                'success': False,
                'message': f"There are no XML files in the folder: {xml_folder_path}",
                'results': []
            }

        self.logger.info(
            f"Found {len(xml_files)} XML files in the folder: {xml_folder_path}")

        results = []
        for xml_file in xml_files:
            try:
                result = self.analyze_paper_from_xml(str(xml_file))
                if not result:
                    self.logger.warning(
                        f"The body content of {xml_file.name} is empty, skipping analysis.")
                    continue
                results.append(result)
                self.logger.info(f"Completed analysis for {xml_file.name}")
                print("=" * 70)
            except Exception as e:
                self.logger.error(f"Failed to analyze {xml_file.name}: {e}")
                results.append({
                    'file_path': str(xml_file),
                    'error': str(e),
                    'success': False
                })

        return {
            'success': True,
            'total_files': len(xml_files),
            'results': results,
        }
