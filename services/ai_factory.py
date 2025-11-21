from typing import Optional, Dict
from config import Config
from .ai_service import AIService, GroqService, GeminiService, HuggingFaceService, OpenRouterService
from .load_balancer import AILoadBalancer


class AIServiceFactory:
    """Factory for creating AI service instances with load balancing support"""
    
    @staticmethod
    def create_service() -> AIService:
        """Create AI service with automatic fallback (legacy method)"""
        services = AIServiceFactory.create_all_services()
        if not services:
            raise RuntimeError("No AI service available. Check your API keys and dependencies.")
        
        # Return first available service for backward compatibility
        return list(services.values())[0]
    
    @staticmethod
    def create_load_balancer() -> AILoadBalancer:
        """Create load balancer with all available services"""
        services = AIServiceFactory.create_all_services()
        if not services:
            raise RuntimeError("No AI service available. Check your API keys and dependencies.")
        
        return AILoadBalancer(services)
    
    @staticmethod
    def create_all_services() -> Dict[str, AIService]:
        """Create all available AI services"""
        services = {}
        
        # Try to create each service
        groq = AIServiceFactory._try_create_groq()
        if groq:
            services['groq'] = groq
        
        gemini = AIServiceFactory._try_create_gemini()
        if gemini:
            services['gemini'] = gemini
        
        openrouter = AIServiceFactory._try_create_openrouter()
        if openrouter:
            services['openrouter'] = openrouter
        
        hf = AIServiceFactory._try_create_huggingface()
        if hf:
            services['huggingface'] = hf
        
        return services
    
    @staticmethod
    def _try_create_groq() -> Optional[AIService]:
        """Try to create Groq service"""
        if not Config.GROQ_API_KEY:
            return None
        
        try:
            return GroqService()
        except ImportError:
            print("Warning: Groq library not installed. Install with: pip install groq")
            return None
        except Exception as e:
            print(f"Warning: Failed to initialize Groq service: {e}")
            return None
    
    @staticmethod
    def _try_create_gemini() -> Optional[AIService]:
        """Try to create Gemini service"""
        if not Config.GEMINI_API_KEY:
            return None
        
        try:
            return GeminiService()
        except ImportError:
            print("Warning: Google Generative AI library not installed. Install with: pip install google-generativeai")
            return None
        except Exception as e:
            print(f"Warning: Failed to initialize Gemini service: {e}")
            return None
    
    @staticmethod
    def _try_create_openrouter() -> Optional[AIService]:
        """Try to create OpenRouter service"""
        if not Config.OPENROUTER_API_KEY:
            return None
        
        try:
            return OpenRouterService()
        except ImportError:
            print("Warning: OpenAI library not installed. Install with: pip install openai")
            return None
        except Exception as e:
            print(f"Warning: Failed to initialize OpenRouter service: {e}")
            return None
    
    @staticmethod
    def _try_create_huggingface() -> Optional[AIService]:
        """Try to create Hugging Face service"""
        if not Config.HUGGINGFACE_API_KEY:
            return None
        
        try:
            return HuggingFaceService()
        except ImportError:
            print("Warning: Hugging Face Hub library not installed. Install with: pip install huggingface_hub")
            return None
        except Exception as e:
            print(f"Warning: Failed to initialize Hugging Face service: {e}")
            return None
