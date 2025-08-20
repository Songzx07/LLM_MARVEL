import re
import json
from groq import Groq
from typing import List, Optional
from config.settings import GROQ_API_KEY, GROQ_MODEL


class KeywordExtractor:
    """Uses LLM to extract academic search keywords from user input"""

    def __init__(self, use_groq: bool = True):
        self.use_groq = use_groq

        if use_groq:
            api_key = GROQ_API_KEY
            print("\nInitializing Groq API service for keyword extraction...")
            if not api_key:
                print(
                    "Failed to initialize Groq API service for KeywordExtractor: GROQ_API_KEY not set")
                self.use_groq = False
            else:
                try:
                    self.client = Groq(api_key=api_key)
                    self.model = GROQ_MODEL
                    print(f"Groq API service initialized successfully")
                except Exception as e:
                    print(f"Groq API service initialization failed: {e}")
                    self.use_groq = False
        else:
            self.client = None
            self.model = None

    def extract_keywords(self, molecular_name: str, molecular_formula: str, molecular_isotope: Optional[str] = None) -> List[str]:
        """Extract academic search keywords from user input"""

        system_prompt = f"""You are an academic literature search expert in the domain of molecular spectroscopy. Extract suitable keywords for academic literature search based on the user's description.

            Requirements:
                1. Extract ONLY English keywords (academic papers are mostly in English)
                2. Return ONLY a JSON format: {{"keywords": ["keyword1", "keyword2", ...]}}
                3. Control the number of keywords to around 6-10, and ensure they are comprehensive and semantically diverse
                4. Prioritize terms commonly used in academic literature related to experimental spectroscopy of {molecular_name} ({molecular_formula}) and its isotopologues if mentioned by user
                5. Focus on molecular spectroscopy research of {molecular_name} ({molecular_formula}) only, and should be related to MARVEL algorithm
                6. Include terms like "rotational", "vibrational" or other terms that are commonly used in molecular spectroscopy research of MARVEL algorithm

            IMPORTANT:
                - Return ONLY the JSON object, no additional text.
                - The keywords must be suitable for academic database search (e.g., Crossref)
                - Only focus on {molecular_name} and its isotopologues if mentioned by user, not other molecules.
                """

        if molecular_isotope:
            user_prompt = f"Extract academic search keywords from this description:\n\nI am looking for research papers that provide high-quality experimental spectroscopic data suitable for input into the MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm in the domain of molecular spectroscopy. The focus should be on {molecular_name} ({molecular_formula}), especially the {molecular_isotope} isotope. Papers must include assigned experimental transitions with well-defined quantum numbers, measured transition frequencies (e.g., derived from FTIR, laser spectroscopy, or microwave spectroscopy), and explicitly reported measurement uncertainties. Please exclude studies that are purely theoretical or reporting calculated line lists without being tied to or validated by new experimental measurements. The primary requirement is to form a dataset of data within papers that can be used as input of MARVEL."
        else:
            user_prompt = f"Extract academic search keywords from this description:\n\nI am looking for research papers that provide high-quality experimental spectroscopic data suitable for input into the MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm in the domain of molecular spectroscopy. The focus should be on {molecular_name} ({molecular_formula}). Papers must include assigned experimental transitions with well-defined quantum numbers, measured transition frequencies (e.g., derived from FTIR, laser spectroscopy, or microwave spectroscopy), and explicitly reported measurement uncertainties. Please exclude studies that are purely theoretical or reporting calculated line lists without being tied to or validated by new experimental measurements. The primary requirement is to form a dataset of data within papers that can be used as input of MARVEL."

        return self._extract_with_groq(system_prompt, user_prompt)

    def _extract_with_groq(self, system_prompt: str, user_prompt: str) -> List[str]:
        """Use Groq API to extract keywords"""
        try:
            print("\nExtracting keywords...")

            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.1,
                max_tokens=300
            )

            response_text = chat_completion.choices[0].message.content.strip()

            try:
                result = json.loads(response_text)
                keywords = result.get("keywords", [])
                print(f"{keywords}")
                return keywords
            except json.JSONDecodeError:
                json_match = re.search(
                    r'\{[^}]*"keywords"[^}]*\}', response_text)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        keywords = result.get("keywords", [])
                        print(
                            f"\nKeywords extracted from regex match: {keywords}")
                        return keywords
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            print(f"No response from LLM using Groq API: {e}")
            return []
