import json
import re
from typing import List, Dict
from openai import OpenAI
from config.settings import GEMINI_API_KEY, GEMINI_MODEL
from tqdm import tqdm


class LLMPaperFilter:
    """Uses LLM to filter academic papers based on user input"""

    def __init__(self, use_gemini: bool):
        self.use_gemini = use_gemini

        if self.use_gemini:
            gemini_key = GEMINI_API_KEY
            print("\nInitializing Gemini API service for paper filtering...")
            if not gemini_key:
                print(
                    "Failed to initialize Gemini API service: GEMINI_API_KEY not set")
                self.use_gemini = False
            else:
                try:
                    self.client = OpenAI(
                        api_key=gemini_key,
                        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                    )
                    self.model = GEMINI_MODEL
                    print("Gemini API service initialized successfully")
                except Exception as e:
                    print(f"Gemini API service initialization failed: {e}")
                    self.use_gemini = False

        if not self.use_gemini:
            print(
                "No LLM service available for paper filtering. Please check your configuration.")
            self.use_gemini = False
            self.client = None
            self.model = None

    def filter_papers_by_title(self, papers: List[Dict], molecular_name: str, molecular_formula: str, molecular_isotope: str,
                               batch_size: int = 20, min_score: float = 0.6) -> List[Dict]:
        """
        Filter papers based on their titles using LLM analysis.
        """
        if not self.use_gemini or not papers:
            print("\nLLM service not available, returning original papers.")
            return papers

        print(
            f"\nTitle-based relevance screening for {len(papers)} papers...\n")

        filtered_papers = []

        with tqdm(total=len(papers), desc="Title Analysis",
                  bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{percentage:3.0f}%] ') as pbar:

            for i in range(0, len(papers), batch_size):
                batch = papers[i:i + batch_size]
                current_batch = i // batch_size + 1

                try:
                    batch_results = self._analyze_titles_batch(
                        batch, molecular_name, molecular_formula, molecular_isotope, min_score)
                    filtered_papers.extend(batch_results)
                    pbar.update(len(batch))

                except Exception as e:
                    filtered_papers.extend(batch)
                    pbar.update(len(batch))
                    pbar.set_postfix_str(
                        f"Batch {current_batch} failed, keeping original papers. Error: {str(e)}")

        retention_rate = len(filtered_papers) / len(papers) * 100
        print(
            f"Stage completed: {len(filtered_papers)} papers passed title screening (Retention: {retention_rate:.1f}%)")

        return filtered_papers

    def _analyze_titles_batch(self, papers: List[Dict], molecular_name: str, molecular_formula: str,
                              molecular_isotope: str, min_score: float) -> List[Dict]:
        """ Analyze a batch of paper titles for relevance using LLM."""
        if molecular_isotope:
            user_query = f"I am compiling a dataset of all available experimental spectroscopic data on {molecular_name} ({molecular_formula}), especially the {molecular_isotope} isotope with the goal of applying the MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm. Papers must include assigned experimental transitions with well-defined quantum numbers, measured transition frequencies and explicitly reported measurement uncertainties. Please exclude studies that are purely theoretical or reporting calculated line lists without being tied to or validated by new experimental measurements. And do not restrict the papers to any single field (e.g., do not assume only rotational spectroscopy). Include relevant papers from other disciplines if they contain such data that can be used to form an input dataset for MARVEL algorithm."
        else:
            user_query = f"I am compiling a dataset of all available experimental spectroscopic data on {molecular_name} ({molecular_formula}), with the goal of applying the MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm. Papers must include assigned experimental transitions with well-defined quantum numbers, measured transition frequencies and explicitly reported measurement uncertainties. Please exclude studies that are purely theoretical or reporting calculated line lists without being tied to or validated by new experimental measurements. And do not restrict the papers to any single field (e.g., do not assume only rotational spectroscopy). Include relevant papers from other disciplines if they contain such data that can be used to form an input dataset for MARVEL algorithm."

        system_prompt = f"""You are an expert academic literature reviewer. Analyze if research papers are relevant to the user's research needs.

        User's Research Query: "{user_query}"

        Your Task:
            1. For each paper, analyze based on the title (and abstract/methods/results if available and pointed).
            2. Determine relevance based on:
            - **Field Alignment**: molecular spectroscopy
            - **Molecule**: {molecular_name}({molecular_formula} {f'with isotope {molecular_isotope}' if molecular_isotope else ''})
            - **Data type**: **experimental** spectral measurements (only need real measured spectral data, exclude computed or ambiguous entries)
            - **Data Requirement for MARVEL Algorithm**: 
                    - MARVEL requires experimentally measured spectroscopic transitions with clear quantum state assignments, precise frequency values, 
                      and reported uncertainties.
                    - Each transition must connect two well-defined energy levels to form a consistent and connected spectroscopic network
            3. For each paper, generate 5 different relevance analyses with reasoning. Assign a relevance score from 0.0 to 1.0 to each result, 
               compare the results and select the most consistent relevance score only.
            4. Return ONLY a JSON array with paper analyses
            5. Provide a brief reasoning for the selected relevance score, focusing on if the paper potentially has experimental data
               that are usable as input for MARVEL algorithm.


            JSON Format:
            [
              {{
                "paper_index": 0,
                "title": "paper title",
                "relevance_score": 0.8,
                "reasoning": "brief explanation of relevance",
                "is_relevant": true
              }},
              ...
            ]

            Scoring Guidelines:
            - 0.8-1.0: Highly relevant — paper under the given title may directly provide experimental data of {molecular_name}(only) that are usable as input of MARVEL algorithm (such data must include: assigned transitions, uncertainties, quantum state assignments or high-res spectra of {molecular_name})
            - 0.6-0.7: Relevant — experimental paper on {molecular_name}(only) spectroscopy, but may require minor post-processing for MARVEL
            - 0.4-0.5: Somewhat relevant — general spectroscopy paper with potential indirect value or on {molecular_name} isotopologues
            - 0.2-0.3: Weakly relevant — tangential spectroscopy work or primarily simulation-based
            - 0.0-0.1: Not relevant — paper does not focus on experimental spectroscopy of molecules, or only discusses simulations, theory, or general chemical properties unrelated to spectra
            
            IMPORTANT: 
            - Given cases that only title is available, you may need to rely on the title alone to determine relevance. If the title suggests potential experimental data or high-quality spectral measurements that can be used in MARVEL of {molecular_name}, consider it highly relevant.
            - Return ONLY the required JSON array, no additional text.
            - All property names and string values must be enclosed in **double quotes** (").
            - The JSON must be **strictly valid**, so that it can be parsed directly using `json.loads()` in Python without any pre-processing.
            """

        papers_info = []
        for idx, paper in enumerate(papers):
            title = paper.get('title', 'N/A')
            venue = paper.get('venue', '')
            year = paper.get('year', 'N/A')

            paper_text = f"Title: {title}"
            if venue:
                paper_text += f" | Journal: {venue}"
            if year != 'N/A':
                paper_text += f" | Year: {year}"

            papers_info.append({
                "index": idx,
                "title": title,
                "text": paper_text
            })

        user_prompt = f"Analyze these {len(papers)} paper titles for relevance:\n\n"
        for paper_info in papers_info:
            user_prompt += f"Paper {paper_info['index']}: {paper_info['text']}\n"

        return self._execute_analysis(system_prompt, user_prompt, papers, papers_info, min_score, "title")

    def _execute_analysis(self, system_prompt: str, user_prompt: str, papers: List[Dict],
                          papers_info: List[Dict], min_score: float, analysis_type: str) -> List[Dict]:
        """Execute the LLM analysis based on the provided system and user prompts"""

        return self._analyze_with_gemini(system_prompt, user_prompt, papers, papers_info, min_score, analysis_type)

    def _analyze_with_gemini(self, system_prompt: str, user_prompt: str,
                             papers: List[Dict], papers_info: List[Dict], min_score: float, analysis_type: str) -> List[Dict]:
        """Use Gemini API to analyze paper relevance"""
        print("\nUsing Gemini API for analysis...")
        try:
            print(f"Gemini model: {self.model}")
            print(f"Request will analyze {len(papers)} papers")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
            )

            if not response or not response.choices:
                print("Error: Gemini API returned empty response or no choices")
                return papers

            choice = response.choices[0]
            if not choice.message:
                print("Error: Gemini API returned no message")
                return papers

            response_text = choice.message.content
            if response_text is None:
                print("Error: Gemini API returned None content")
                return papers

            response_text = response_text.strip()

            print(
                f"Gemini raw response (first 500 chars): {response_text[:500]}")

            cleaned_text = re.sub(r'[\x00-\x1f\x7f]', '', response_text)

            analyses = None

            # Method 1: Direct JSON parsing
            try:
                analyses = json.loads(cleaned_text)
                print("Successfully parsed JSON directly")
            except json.JSONDecodeError as e:
                pass

            # Method 2: Find JSON array
            if analyses is None:
                json_match = re.search(
                    r'\[\s*\{.*?\}\s*\]', cleaned_text, re.DOTALL)
                if json_match:
                    try:
                        analyses = json.loads(json_match.group())
                        print("Successfully extracted JSON array")
                    except json.JSONDecodeError as e:
                        pass

            # Method 3: Find JSON with brackets
            if analyses is None:
                start_idx = cleaned_text.find('[')
                end_idx = cleaned_text.rfind(']')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_candidate = cleaned_text[start_idx:end_idx+1]
                    try:
                        analyses = json.loads(json_candidate)
                        print("Successfully extracted JSON with bracket matching")
                    except json.JSONDecodeError as e:
                        pass

            # Method 4: Fix common JSON format issues
            if analyses is None:
                cleaned_text = re.sub(r'```json\s*', '', cleaned_text)
                cleaned_text = re.sub(r'```\s*$', '', cleaned_text)

                lines = cleaned_text.split('\n')
                json_lines = []
                in_json = False

                for line in lines:
                    line = line.strip()
                    if line.startswith('[') or in_json:
                        in_json = True
                        json_lines.append(line)
                        if line.endswith(']'):
                            break

                if json_lines:
                    json_candidate = '\n'.join(json_lines)
                    try:
                        analyses = json.loads(json_candidate)
                        print("Successfully parsed JSON after cleanup")
                    except json.JSONDecodeError as e:
                        pass

            # Method 5: Manual parsing
            if analyses is None:
                print("Attempting manual parsing...")
                try:
                    object_pattern = r'\{\s*"paper_index":\s*\d+.*?\}'
                    matches = re.findall(
                        object_pattern, cleaned_text, re.DOTALL)

                    if matches:
                        analyses = []
                        for match in matches:
                            try:
                                obj = json.loads(match)
                                analyses.append(obj)
                            except json.JSONDecodeError:
                                continue

                        if analyses:
                            print(
                                f"Successfully parsed {len(analyses)} objects manually")
                except Exception as e:
                    print(f"Manual parsing failed: {e}")

            if analyses is None:
                print("All JSON parsing methods failed.")
                print(f"Raw response: '{response_text}'")
                print(f"Response length: {len(response_text)}")
                print("Possible issues:")
                print("1. DeepSeek API quota exceeded")
                print("2. Invalid API key or model name")
                print("3. Request content filtered")
                print("4. Service temporarily unavailable")
                print("Returning original papers...")
                return papers

            if not isinstance(analyses, list):
                print(f"Expected list, got {type(analyses)}. Converting...")
                if isinstance(analyses, dict):
                    analyses = [analyses]
                else:
                    print("Cannot convert to list, returning original papers")
                    return papers

            relevant_papers = []
            for analysis in analyses:
                try:
                    paper_idx = analysis.get('paper_index', 0)
                    relevance_score = analysis.get('relevance_score', 0.0)
                    reasoning = analysis.get('reasoning', '')

                    if paper_idx >= len(papers) or paper_idx >= len(papers_info):
                        print(f"Invalid paper index {paper_idx}, skipping...")
                        continue

                    if relevance_score >= min_score:
                        paper = papers[paper_idx].copy()
                        paper['llm_analysis'] = {
                            'relevance_score': relevance_score,
                            'reasoning': reasoning,
                            'is_relevant': True,
                            'analysis_type': analysis_type,
                            'llm_service': 'gemini'
                        }
                        relevant_papers.append(paper)

                except (KeyError, TypeError, IndexError) as e:
                    print(f"Failed to parse Gemini analysis result: {e}")
                    continue

            print(
                f"Gemini analysis completed: {len(relevant_papers)} papers passed")
            return relevant_papers

        except Exception as e:
            print(f"Gemini analysis failed with exception: {e}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return papers
