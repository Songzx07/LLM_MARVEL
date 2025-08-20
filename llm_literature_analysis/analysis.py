import os
import sys
import json
from datetime import datetime
from pathlib import Path
from src.core.paper_analyzer import PaperAnalyzer
from src.core.xml_processor import XMLProcessor
from config.settings import GEMINI_API_KEY, GEMINI_MODEL

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))


def initialize_analysis_service():
    """Initialize the LLM analysis service"""
    print("=" * 70)
    print("LLM-enhanced Academic Paper Analysis Tool")
    print("=" * 70)
    print("Supports comprehensive XML paper analysis with natural language queries")
    print()

    gemini_api_key = GEMINI_API_KEY
    if not gemini_api_key:
        print("\nError: Gemini API key not found!")
        print(
            "Please set GEMINI_API_KEY in your environment variables or config/settings.py")
        return None

    try:
        analyzer = PaperAnalyzer(use_gemini=True)
        return analyzer
    except Exception as e:
        print(f"Failed to initialize analysis service: {e}")
        return None


def get_output_settings():

    print("\n" + "=" * 70)
    print("Output settings:")

    save_to_file = True

    output_file = None
    if save_to_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"paper_analysis_results_{timestamp}.json"
        output_file = input(
            f"Output filename (defaults to {default_filename}): ").strip()
        if not output_file:
            output_file = default_filename

    return {
        'save_to_file': save_to_file,
        'output_file': output_file,
    }


def display_analysis_config(file_path, output_settings):

    print("\n" + "=" * 70)
    print("ANALYSIS CONFIGURATION:")
    print(f"LLM Service: Gemini API using model {GEMINI_MODEL}")

    xml_count = len(list(Path(file_path).glob("*.xml")))
    print(f"Target Folder: {file_path}")
    print(f"XML Files Found: {xml_count}")

    print(f"Output File: {output_settings['output_file']}")

    print("=" * 70)


def perform_batch_analysis(analyzer, folder_path, output_settings):

    start_time = datetime.now()

    try:
        xml_files = list(Path(folder_path).glob("*.xml"))
        print(f"\nAnalyzing {len(xml_files)} papers from: {folder_path}")
        print("This may take several minutes...")

        results = analyzer.batch_analyze(folder_path)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        if results.get('success'):
            successful_analyses = [r for r in results['results']
                                   if r.get('llm_analysis', {}).get('success')]

            print(f"\n{'='*70}")
            print(f"Batch analysis completed! (Time: {duration:.1f}s)")
            print(f"{'='*70}\n")
            print(f"Total files processed: {results['total_files']}")
            print(f"Successful analyses: {len(successful_analyses)}")
            print(
                f"Failed analyses: {results['total_files'] - len(successful_analyses)}")

            paper_base = dict()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, item in enumerate(successful_analyses):
                print(f"\n{'='*70}")
                paper_base[i] = {
                    'file_path': item['file_path'],
                    'is_relevant': False,
                    'has_data': False,
                    'need_pdf': False,
                    'need_supplementary': False,
                }
                if item['llm_analysis']['analysis']['marvel_relevance']['is_relevant'] == True:
                    paper_base[i]['is_relevant'] = True

                    if item['llm_analysis']['analysis']['experimental_data']['has_data'] == True:
                        target_file = item['file_path']
                        paper_base[i]['has_data'] = True
                        print(
                            f"\nTarget file: {target_file} is relevant and has data")

                        if item['llm_analysis']['analysis']['experimental_data']['table_info']['table_title']:

                            if item['llm_analysis']['analysis']['experimental_data']['has_uncertainty'] == True:
                                target_uncertainty = item['llm_analysis']['analysis']['experimental_data']['uncertainty_value']
                                print(f"\nUncertainty: {target_uncertainty}")
                            else:
                                print("\nNo uncertainty data found for this paper.")
                                target_uncertainty = None

                            target_table = item['llm_analysis']['analysis']['experimental_data']['table_info']['table_title']
                            print(f"\nTarget table of data: {target_table}")

                            processor = XMLProcessor()

                            # Handle case where target_table is a list
                            if isinstance(target_table, list):
                                for table_title in target_table:
                                    processor.extract_table_data_by_title(
                                        xml_file_path=target_file,
                                        table_title=table_title,
                                        uncertainty=target_uncertainty,
                                        timestamp=timestamp
                                    )
                            else:
                                # Handle single table title
                                processor.extract_table_data_by_title(
                                    xml_file_path=target_file,
                                    table_title=target_table,
                                    uncertainty=target_uncertainty,
                                    timestamp=timestamp
                                )

                            if item['llm_analysis']['analysis']['experimental_data']['has_supplementary_data'] == True:
                                print(
                                    f"\nNEED SUPPLEMENTARY DATA FILE")
                                paper_base[i]['need_supplementary'] = True

                        else:
                            print('\nPDF file needed for this paper')
                            item['llm_analysis']['analysis']['experimental_data']['need_pdf'] = True

                    else:
                        print(
                            f"\nTarget file: {item['file_path']} is relevant but has no data provided directly in the provided content.")
                        if item['llm_analysis']['analysis']['experimental_data']['has_supplementary_data'] == True:
                            print(
                                f"\nFurther check of supplementary data is suggested")
                            paper_base[i]['need_supplementary'] = True

                else:
                    print(
                        f"\nTarget file: {item['file_path']} is not relevant")

                paper_status_file = Path(
                    "analysis_results") / timestamp / 'paper_status.json'
                paper_status_file.parent.mkdir(parents=True, exist_ok=True)
                with open(paper_status_file, 'w', encoding='utf-8-sig') as f:
                    json.dump(paper_base, f, ensure_ascii=False, indent=2)

            if output_settings['save_to_file']:
                save_analysis_results(
                    results, timestamp, output_settings['output_file'])

        else:
            print(
                f"\nBatch analysis failed: {results.get('message', 'Unknown error')}")

    except Exception as e:
        print(f"\nError during batch analysis: {e}")
        import traceback
        traceback.print_exc()


def save_analysis_results(results, timestamp, filename):

    try:
        output_dir = Path("analysis_results")
        output_dir.mkdir(exist_ok=True)

        output_path = output_dir / timestamp / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Failed to save results: {e}")


def main():
    """ Main function to run the LLM-based paper analysis tool"""

    analyzer = initialize_analysis_service()
    if analyzer is None:
        return

    while True:
        try:
            folder_name = input(
                "\nEnter the folder path containing XML files (or press Enter to use default '../article_xmls'): ").strip()
            file_path = '../article_xmls'
            if folder_name:
                file_path = file_path + '/' + folder_name
            if file_path is None:
                continue

            output_settings = get_output_settings()

            display_analysis_config(file_path, output_settings)

            print(f"\nStarting analysis...")

            perform_batch_analysis(
                analyzer, file_path, output_settings)

        except KeyboardInterrupt:
            print("\n\nAnalysis interrupted by user.")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 70)
        print("\nThank you for using the LLM-enhanced Academic Paper Analysis Tool!")
        print("Goodbye!")
        break


if __name__ == "__main__":
    main()
