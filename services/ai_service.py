import json
import re
from abc import ABC, abstractmethod
from config import Config
from database import PromptRepository


class AIService(ABC):
    """Abstract base class for AI services"""
    
    def __init__(self):
        self.prompt_repo = PromptRepository()
    
    @abstractmethod
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file to text"""
        pass
    
    @abstractmethod
    def extract_profile(self, text: str) -> dict:
        """Extract profile information from text"""
        pass
    
    @abstractmethod
    def generate_cv_profile(self, transcription: str, profile_data: dict) -> str:
        """Generate professional CV profile"""
        pass
    
    @abstractmethod
    def generate_technical_test(self, profile_data: dict) -> str:
        """Generate technical test based on profile"""
        pass


class GroqService(AIService):
    """Groq AI service implementation"""
    
    def __init__(self):
        super().__init__()
        from groq import Groq
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        print("Groq AI service initialized")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Groq Whisper"""
        try:
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_path, file.read()),
                    model=Config.GROQ_TRANSCRIPTION_MODEL,
                    prompt="Transcribe this audio in Spanish. It's a personal or professional presentation.",
                    response_format="text",
                    language="es"
                )
            return transcription.strip() if transcription else "Unable to transcribe audio."
        except Exception as e:
            raise Exception(f"Groq transcription error: {str(e)}")
    
    def extract_profile(self, text: str) -> dict:
        """Extract profile information using Groq"""
        prompt = self.prompt_repo.get_prompt_with_variables("profile_extraction", text=text)
        
        try:
            try:
                response = self.client.chat.completions.create(
                    model=Config.GROQ_CHAT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an assistant that extracts professional profile information from transcribed texts. You MUST respond in SPANISH. You MUST respond with ONLY valid JSON. Do NOT use markdown code blocks. Do NOT add any text before or after the JSON. Start your response with { and end with }. Your entire response must be parseable JSON. ALL field values must be in SPANISH."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1200,
                    top_p=0.9,
                    stream=False,
                    response_format={"type": "json_object"}
                )
            except Exception as e:
                # Fallback without response_format if not supported
                if "response_format" in str(e).lower() or "not supported" in str(e).lower():
                    response = self.client.chat.completions.create(
                        model=Config.GROQ_CHAT_MODEL,
                        messages=[
                            {"role": "system", "content": "You are an assistant that extracts professional profile information from transcribed texts. You MUST respond in SPANISH. You MUST respond with ONLY valid JSON. Do NOT use markdown code blocks. Do NOT add any text before or after the JSON. Start your response with { and end with }. Your entire response must be parseable JSON. ALL field values must be in SPANISH."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.1,
                        max_tokens=1200,
                        top_p=0.9,
                        stream=False
                    )
                else:
                    raise
            
            response_text = response.choices[0].message.content.strip()
            print(f"[Groq] Raw response (first 200 chars): {response_text[:200]}")
            parsed = self._parse_json_response(response_text)
            print(f"[Groq] Successfully parsed JSON with keys: {list(parsed.keys())}")
            return parsed
        except Exception as e:
            print(f"[Groq] Profile extraction failed: {str(e)}")
            raise Exception(f"Groq profile extraction error: {str(e)}")
    
    def generate_cv_profile(self, transcription: str, profile_data: dict) -> str:
        """Generate CV profile using Groq"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "cv_generation",
            transcription=transcription,
            profile_data=json.dumps(profile_data, ensure_ascii=False)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=Config.GROQ_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an assistant specialized in creating professional CV profiles. Generate persuasive and professional texts in Spanish."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1800,
                top_p=0.95,
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Groq CV generation error: {str(e)}")
    
    def generate_technical_test(self, profile_data: dict) -> str:
        """Generate technical test using Groq"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "technical_test_generation",
            profession=profile_data.get("profession", ""),
            technologies=profile_data.get("technologies", ""),
            experience=profile_data.get("experience", ""),
            education=profile_data.get("education", "")
        )
        
        try:
            response = self.client.chat.completions.create(
                model=Config.GROQ_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert in creating technical assessments for job candidates. Generate comprehensive and fair technical tests in Spanish, formatted in Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=4000,
                top_p=0.95,
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Groq technical test generation error: {str(e)}")
    
    @staticmethod
    def _parse_json_response(response_text: str) -> dict:
        """Parse JSON from AI response with robust error handling"""
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        response_text = response_text.strip()
        
        # Try to parse directly first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"[JSON Parser] Direct parse failed: {str(e)}")
            print(f"[JSON Parser] Response text (first 300 chars): {response_text[:300]}")
        
        # Try to find JSON object in the response (greedy match)
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"[JSON Parser] Regex match parse failed: {str(e)}")
                print(f"[JSON Parser] Matched JSON (first 300 chars): {json_str[:300]}")
                
                # Try to fix common issues
                # Remove trailing commas before closing braces
                json_str_fixed = re.sub(r',(\s*[}\]])', r'\1', json_str)
                try:
                    return json.loads(json_str_fixed)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON in response: {str(e)}\nResponse: {response_text[:300]}")
        
        raise ValueError(f"No valid JSON found in response: {response_text[:300]}")


class GeminiService(AIService):
    """Gemini AI service implementation"""
    
    def __init__(self):
        super().__init__()
        import google.generativeai as genai
        genai.configure(api_key=Config.GEMINI_API_KEY)
        
        try:
            self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
            print(f"Gemini AI service initialized with {Config.GEMINI_MODEL}")
        except Exception:
            self.model = genai.GenerativeModel(Config.GEMINI_FALLBACK_MODEL)
            print(f"Gemini AI service initialized with {Config.GEMINI_FALLBACK_MODEL}")
        
        self.genai = genai
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio using Gemini"""
        try:
            audio_file = self.genai.upload_file(audio_path)
            response = self.model.generate_content([
                "Transcribe this audio in Spanish. Provide only the speech transcription, without additional comments or special formatting.",
                audio_file
            ])
            return response.text.strip() if response.text else "Unable to transcribe audio."
        except Exception as e:
            raise Exception(f"Gemini transcription error: {str(e)}")
    
    def extract_profile(self, text: str) -> dict:
        """Extract profile information using Gemini"""
        prompt = self.prompt_repo.get_prompt_with_variables("profile_extraction", text=text)
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            return GroqService._parse_json_response(response_text)
        except Exception as e:
            raise Exception(f"Gemini profile extraction error: {str(e)}")
    
    def generate_cv_profile(self, transcription: str, profile_data: dict) -> str:
        """Generate CV profile using Gemini"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "cv_generation",
            transcription=transcription,
            profile_data=json.dumps(profile_data, ensure_ascii=False)
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini CV generation error: {str(e)}")
    
    def generate_technical_test(self, profile_data: dict) -> str:
        """Generate technical test using Gemini"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "technical_test_generation",
            profession=profile_data.get("profession", ""),
            technologies=profile_data.get("technologies", ""),
            experience=profile_data.get("experience", ""),
            education=profile_data.get("education", "")
        )
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini technical test generation error: {str(e)}")


class HuggingFaceService(AIService):
    """Hugging Face Inference API service implementation"""
    
    def __init__(self):
        super().__init__()
        from huggingface_hub import InferenceClient
        self.client = InferenceClient(token=Config.HUGGINGFACE_API_KEY)
        self.model = Config.HUGGINGFACE_MODEL
        print(f"Hugging Face service initialized with {self.model}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """Hugging Face doesn't support audio transcription in free tier"""
        raise NotImplementedError("Hugging Face free tier does not support audio transcription. Use Groq or Gemini for this feature.")
    
    def extract_profile(self, text: str) -> dict:
        """Extract profile information using Hugging Face"""
        prompt = self.prompt_repo.get_prompt_with_variables("profile_extraction", text=text)
        
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that extracts professional profile information from transcribed texts. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            return GroqService._parse_json_response(response_text)
        except Exception as e:
            raise Exception(f"Hugging Face profile extraction error: {str(e)}")
    
    def generate_cv_profile(self, transcription: str, profile_data: dict) -> str:
        """Generate CV profile using Hugging Face"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "cv_generation",
            transcription=transcription,
            profile_data=json.dumps(profile_data, ensure_ascii=False)
        )
        
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant specialized in creating professional CV profiles. Generate persuasive and professional texts in Spanish."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Hugging Face CV generation error: {str(e)}")
    
    def generate_technical_test(self, profile_data: dict) -> str:
        """Generate technical test using Hugging Face"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "technical_test_generation",
            profession=profile_data.get("profession", ""),
            technologies=profile_data.get("technologies", ""),
            experience=profile_data.get("experience", ""),
            education=profile_data.get("education", "")
        )
        
        try:
            response = self.client.chat_completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in creating technical assessments for job candidates. Generate comprehensive and fair technical tests in Spanish, formatted in Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Hugging Face technical test generation error: {str(e)}")



class OpenRouterService(AIService):
    """OpenRouter AI service implementation (OpenAI-compatible)"""
    
    def __init__(self):
        super().__init__()
        from openai import OpenAI
        self.client = OpenAI(
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL
        )
        self.model = Config.OPENROUTER_MODEL
        print(f"OpenRouter service initialized with {self.model}")
    
    def transcribe_audio(self, audio_path: str) -> str:
        """OpenRouter doesn't support audio transcription"""
        raise NotImplementedError("OpenRouter service does not support audio transcription. Use Groq or Gemini for this feature.")
    
    def extract_profile(self, text: str) -> dict:
        """Extract profile information using OpenRouter"""
        prompt = self.prompt_repo.get_prompt_with_variables("profile_extraction", text=text)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that extracts professional profile information from transcribed texts. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            response_text = response.choices[0].message.content.strip()
            return GroqService._parse_json_response(response_text)
        except Exception as e:
            raise Exception(f"OpenRouter profile extraction error: {str(e)}")
    
    def generate_cv_profile(self, transcription: str, profile_data: dict) -> str:
        """Generate CV profile using OpenRouter"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "cv_generation",
            transcription=transcription,
            profile_data=json.dumps(profile_data, ensure_ascii=False)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant specialized in creating professional CV profiles. Generate persuasive and professional texts in Spanish."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenRouter CV generation error: {str(e)}")
    
    def generate_technical_test(self, profile_data: dict) -> str:
        """Generate technical test using OpenRouter"""
        prompt = self.prompt_repo.get_prompt_with_variables(
            "technical_test_generation",
            profession=profile_data.get("profession", ""),
            technologies=profile_data.get("technologies", ""),
            experience=profile_data.get("experience", ""),
            education=profile_data.get("education", "")
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in creating technical assessments for job candidates. Generate comprehensive and fair technical tests in Spanish, formatted in Markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=2500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenRouter technical test generation error: {str(e)}")
