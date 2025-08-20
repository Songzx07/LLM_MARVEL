import re
import json
import logging
from openai import OpenAI
from typing import Dict, Any
from config.settings import GEMINI_API_KEY, GEMINI_MODEL


class LLMClient:

    def __init__(self, use_gemini: bool = True):
        self.use_gemini = use_gemini
        if self.use_gemini:
            gemini_key = GEMINI_API_KEY
            print("Initializing Gemini API service for paper filtering...")
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

        self.logger = logging.getLogger(__name__)

    def analyze_paper(self, paper_content: str) -> Dict[str, Any]:
        """
        Use Gemini API to analyze paper content for MARVEL relevance

        Args:
            paper_content: The content of the paper to analyze
        Returns:
            A dictionary containing the analysis results
        """
        try:
            user_prompt = f"""
                      MARVEL is an algorithm that reconstructs molecular energy level structures from experimental spectroscopic data. Its key inputs include:
                        - Experimentally measured **transition wavenumbers** (or line positions, frequencies)
                        - **Quantum number assignments** for both the **upper** and **lower** states of the transition (e.g., P, J, symmetry C, sublevel index α)
                        - **Uncertainties** associated with each measured wavenumber
                        - These data are typically presented in tables or appendices, or described as structured lists in the text.

                      To ensure accurate and reliable output, follow a multi-step reasoning strategy. At each step, explicitly consider all relevant aspects 
                      before proceeding to the next.

                      ### STEP 1: Determine the paper's **relevance to MARVEL goals**
                      Think carefully:  
                      - Does the paper involve contents that are relevant to MARVEL, such as high-resolution spectroscopy, rovibrational analysis, 
                        transition assignment, or energy level modeling?    
                      - Is its content or objective **aligned** with MARVEL (e.g., similar research goals)?
                      - Even if the paper focuses on related measurements (e.g., line shape, broadening, lifetimes), 
                        does it employ experimental techniques, quantum assignments, 
                        or theoretical models that could conceptually support MARVEL's goal of reconstructing molecular energy levels?
                      
                      Write down your reasoning before deciding whether it is MARVEL-relevant.  
                      If the paper is **clearly not relevant** to MARVEL goals **based on the reasoning above**, return `"is_relevant": false` 
                      and keep the other fields empty or false to avoid key errors. 
                      Otherwise, even in uncertain cases, prefer to return `"is_relevant": true` and allow the next step to make further distinctions

                      ### STEP 2: If relevant, continue to evaluate whether the paper provides MARVEL-compatible **experimental data**
                      Think carefully:
                      - Does it contain **new** measured **transition wavenumber(/frequencies)** for the molecule of interest?  
                      - Are **quantum number assignments** for **both upper and lower states** clearly provided, 
                        i.e. are these data fully assigned with quantum numbers?
                      - Are **uncertainties** for transition wavenumbers stated or can they be inferred from resolution?

                      If all the above answers are yes, the paper can be considered to provide MARVEL-compatible experimental data.
                      The 'has_data' field should be set to true, and the 'data_format' field should describe how the data is presented.
                      If the paper does not meet these conditions, set 'has_data' to false and leave the other fields empty.

                      If tables are not complete, check whether:
                      - Sample tables or snippets demonstrate valid structure (e.g., wavenumber(/frequencies) + uncertainty + partial QNs)?
                      - The text claims that full data are in supplementary material?

                      Note:
                      - Do **not** accept computed energy levels without transitions.
                      - Do **not** accept quantum assignments without wavenumber.
                      - Do **not** accept data without full quantum assignment.
                      - Do **not** accept data that are old or from other papers without new measurements.
                      - It is acceptable to infer uncertainty from instrument resolution if not explicitly stated.
                      - If only part of the data meets the criteria, still consider it as providing MARVEL-compatible data, but note the limitations.

                      Now, after completing these two reasoning steps, summarize and output your findings in the following JSON format **exactly**:

                      Regardless of whether a paper contains useful content or not, and whether one or two task are exectued, you **must return all fields** in the JSON template below.  
                      Do not skip any subfields even if they are empty, false, or not applicable. All keys must exist to avoid downstream errors


                      {{
                          "marvel_relevance": {{
                              "is_relevant": True/False,
                              "explanation": "Explain why the paper is relevant or not relevant to MARVEL based on the content provided."
                          }},
                          
                          "experimental_data": {{
                              "has_data": True/False,
                              "data_format": "Specify how the data is presented if available (e.g., in tables or within the text). If the data exist in the paper, but cannot be obtained due to the content restriction, explain here.",
                              "need_pdf": True/False,
                              "has_uncertainty": True/False,
                              "uncertainty_description": "State the uncertainty information if available.",
                              "uncertainty_value": "If the value of line position uncertainty is available, directly state its value with unit. If not available, return 'not available'.", 
                              "table_info": {{
                                  "table_title": "List all the table titles containing MARVEL-compatible experimental data (wavenumber(/frequency) + uncertainty + upper/lower quantum numbers). If no table title is available, return an empty list.",
                                  "description": "Table descriptions corresponding to the above titles, if available."
                              }},
                              "has_supplementary_data": True/False
                          }},
                          
                          "summary": {{
                              "Evaluation": "Provide a summary of the paper's relevance to MARVEL, and comment on the existence of data."
                          }}
                      }}

                      Now, analyze the paper content below and follow the above reasoning steps. Return **only** the final JSON object.

                      Paper Content: {paper_content}
                      """

            response = self._call_gemini_api(user_prompt)
            raw_content = response.get('content', '')

            try:
                json_content = self._extract_json_from_response(raw_content)
                analysis_json = json.loads(json_content)

                return {
                    'success': True,
                    'analysis': analysis_json,
                    'model': self.model
                }
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to parse JSON from response: {e}")
                return {
                    'success': True,
                    'analysis': {
                        'raw_response': raw_content,
                        'parsing_error': f"Failed to parse JSON: {str(e)}"
                    },
                    'model': self.model
                }

        except Exception as e:
            self.logger.error(f"Failed to analyze using LLM: {e}")
            return {
                'success': False,
                'error': str(e),
                'analysis': None
            }

    def _extract_json_from_response(self, response_text: str) -> str:

        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*$', '', response_text)

        start_idx = response_text.find('{')
        if start_idx == -1:
            raise ValueError("No JSON object found in response")

        brace_count = 0
        end_idx = -1
        for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
                brace_count += 1
            elif response_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break

        if end_idx == -1:
            raise ValueError("Incomplete JSON object in response")

        return response_text[start_idx:end_idx]

    def _call_gemini_api(self, user_prompt: str) -> Dict[str, Any]:

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in molecular spectroscopy and data analysis. Based on the following content from a scientific paper, determine its relevance to the MARVEL (Measured Active Rotational-Vibrational Energy Levels) algorithm."
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
            )

            if not response or not response.choices:
                print("Error: Gemini API returned empty response or no choices")
                return

            choice = response.choices[0]
            if not choice.message:
                print("Error: Gemini API returned no message")
                return

            response_text = choice.message.content
            if response_text is None:
                print("Error: Gemini API returned None content")
                return

            response_text = response_text.strip()

            cleaned_text = re.sub(r'[\x00-\x1f\x7f]', '', response_text)

            return {
                'content': cleaned_text,
            }

        except Exception as e:
            raise Exception(f"Gemini API call failed: {e}")
