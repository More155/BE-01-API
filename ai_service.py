import os
import time
import httpx
from google import genai
from google.genai import types
from google.genai.errors import APIError
from fastapi import HTTPException
from schemas import ClassificationResult

GEMINI_INPUT_COST_PER_M = 0.075
GEMINI_OUTPUT_COST_PER_M = 0.30

class AIService:
    def __init__(self):
        self.provider = os.getenv("AI_PROVIDER", "gemini").lower()
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        
        if self.provider == "gemini" and self.gemini_key:
            self.client = genai.Client(api_key=self.gemini_key)

    def analyze_text(self, text: str) -> ClassificationResult:
        if self.provider == "gemini":
            return self._call_gemini_with_retry(text)
        else:
            raise HTTPException(status_code=500, detail=f"Provider {self.provider} not implemented.")

    def _call_gemini_with_retry(self, text: str, retries=1):
        prompt = f"Analyze the following user input and classify it accurately: {text}"
        
        for attempt in range(retries + 1):
            try:
                response = self.client.models.generate_content(
                    model='gemini-flash-latest',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a strict data extraction API. You must respond ONLY with a raw JSON object matching the requested schema.",
                        response_mime_type="application/json",
                        response_schema=ClassificationResult,
                    ),
                )
                
                usage = response.usage_metadata
                input_tokens = usage.prompt_token_count if usage else 0
                output_tokens = usage.candidates_token_count if usage else 0
                
                cost = ((input_tokens / 1_000_000) * GEMINI_INPUT_COST_PER_M) + ((output_tokens / 1_000_000) * GEMINI_OUTPUT_COST_PER_M)
                
                print(f"[AI LOG - Feature: Text Classification] Input Tokens: {input_tokens} | Output Tokens: {output_tokens} | Estimated Cost: ${cost:.6f}")
                
                return ClassificationResult.model_validate_json(response.text)

            except APIError as e:
                if e.code in [429, 500, 502, 503, 504] and attempt < retries:
                    print(f"Temporary AI failure ({e.code}). Retrying in 2 seconds...")
                    time.sleep(2)
                    continue
                raise HTTPException(status_code=502, detail=f"AI Provider error: {e.message}")
            except Exception as e:
                if attempt < retries:
                    print(f"Malformed structure or unknown error: {e}. Retrying execution...")
                    continue
                raise HTTPException(status_code=502, detail="Failed to retrieve a schema-valid response from AI.")