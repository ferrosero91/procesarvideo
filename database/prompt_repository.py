from typing import Optional
from .mongodb import MongoDBClient


class PromptRepository:
    """Repository for managing AI prompts in MongoDB"""
    
    # Cache for prompts to avoid repeated DB queries
    _prompt_cache = {}
    
    DEFAULT_PROMPTS = {
        "profile_extraction": {
            "name": "profile_extraction",
            "description": "Extract profile information from transcribed text",
            "template": (
                "Analyze the following transcribed text from a personal presentation video and extract profile information.\n\n"
                "Return ONLY a valid JSON object with these fields:\n"
                "- name: Person's name\n"
                "- profession: Current occupation, position or specialty\n"
                "- experience: Areas or topics with work practice or applied knowledge\n"
                "- education: Degrees, studies or academic training. If not explicitly mentioned, infer logically from profession\n"
                "- technologies: Tools, software, languages or specific techniques mentioned\n"
                "- languages: List of spoken or understood languages\n"
                "- achievements: Recognition, milestones or relevant contributions\n"
                "- soft_skills: Social or personal skills\n\n"
                "If any field is not present and cannot be inferred, use 'Not specified'.\n\n"
                "Text to analyze:\n{text}\n\n"
                "Respond ONLY with JSON, no additional text."
            ),
            "variables": ["text"]
        },
        "cv_generation": {
            "name": "cv_generation",
            "description": "Generate professional CV profile from transcription and extracted data",
            "template": (
                "Based on the following transcription and extracted profile information, write an optimized professional profile for a CV in the style of concise and impactful executive summaries. The profile must be in Spanish, professional and formal, written in impersonal third person (without mentioning the name at the beginning), structured in short and focused paragraphs. Follow this approximate structure: - First paragraph: Profession and key experience, highlighting specialties and areas of expertise. - Second paragraph: Academic training and technical knowledge/technologies. - Third paragraph: Capabilities, languages and soft skills. - Fourth paragraph: Recognition, achievements and professional commitment. Use impactful phrases, persuasive language and avoid redundancies. Integrate all relevant information coherently.\n\n"
                "Transcription: {transcription}\n\n"
                "Extracted information: {profile_data}\n\n"
                "If any data is unavailable or 'Not specified', integrate it subtly or omit it if it doesn't add value. Don't use Markdown format, placeholders or additional text outside the profile. The profile must be concise, persuasive and suitable for a professional CV."
            ),
            "variables": ["transcription", "profile_data"]
        },
        "technical_test_generation": {
            "name": "technical_test_generation",
            "description": "Generate technical test for job candidate based on profile",
            "template": (
                "Generate a comprehensive technical test in Spanish for a job candidate with the following profile:\n\n"
                "**Profession:** {profession}\n"
                "**Technologies/Skills:** {technologies}\n"
                "**Experience Level:** {experience}\n"
                "**Education:** {education}\n\n"
                "Create a technical assessment that includes:\n\n"
                "1. **Theoretical Questions (30%)**: 5-7 multiple choice or short answer questions about fundamental concepts\n"
                "2. **Practical Exercises (50%)**: 2-3 hands-on coding/problem-solving exercises appropriate to the role\n"
                "3. **Case Study/Scenario (20%)**: 1 real-world scenario that tests analytical and decision-making skills\n\n"
                "**Requirements:**\n"
                "- Adjust difficulty based on experience level\n"
                "- Focus on technologies and skills mentioned in the profile\n"
                "- Include clear instructions and expected deliverables\n"
                "- Provide estimated time for completion (total: 2-3 hours)\n"
                "- Format the entire test in Markdown with proper headings, code blocks, and formatting\n"
                "- Include a section at the end for evaluation criteria\n\n"
                "**Format Structure:**\n"
                "```markdown\n"
                "# Prueba Técnica - [Profession]\n\n"
                "## Información General\n"
                "- Duración estimada: X horas\n"
                "- Tecnologías evaluadas: [list]\n\n"
                "## Parte 1: Preguntas Teóricas (30%)\n"
                "...\n\n"
                "## Parte 2: Ejercicios Prácticos (50%)\n"
                "...\n\n"
                "## Parte 3: Caso de Estudio (20%)\n"
                "...\n\n"
                "## Criterios de Evaluación\n"
                "...\n"
                "```\n\n"
                "Generate a professional, fair, and comprehensive technical test that accurately assesses the candidate's capabilities."
            ),
            "variables": ["profession", "technologies", "experience", "education"]
        }
    }
    
    def __init__(self):
        """Initialize prompt repository with MongoDB connection"""
        self.db_client = MongoDBClient()
        self.collection_name = "prompts"
        self._initialize_prompts()
    
    def _initialize_prompts(self):
        """Initialize default prompts in MongoDB if not present"""
        if not self.db_client.is_connected():
            return
        
        collection = self.db_client.database[self.collection_name]
        
        # Check if prompts exist
        if collection.count_documents({}) == 0:
            print("Initializing default prompts in MongoDB...")
            collection.insert_many(list(self.DEFAULT_PROMPTS.values()))
            print("Default prompts initialized")
        else:
            # Update existing prompts and add new ones
            for prompt_name, prompt_data in self.DEFAULT_PROMPTS.items():
                existing = collection.find_one({"name": prompt_name})
                if not existing:
                    print(f"Adding new prompt: {prompt_name}")
                    collection.insert_one(prompt_data)
    
    def get_prompt(self, prompt_name: str) -> Optional[str]:
        """
        Get prompt template by name
        
        Args:
            prompt_name: Name of the prompt
            
        Returns:
            Prompt template string or None if not found
        """
        # Check cache first
        if prompt_name in self._prompt_cache:
            return self._prompt_cache[prompt_name]
        
        if not self.db_client.is_connected():
            # Fallback to default prompts
            template = self.DEFAULT_PROMPTS.get(prompt_name, {}).get("template")
            self._prompt_cache[prompt_name] = template
            return template
        
        collection = self.db_client.database[self.collection_name]
        prompt_doc = collection.find_one({"name": prompt_name})
        
        if prompt_doc:
            template = prompt_doc.get("template")
            self._prompt_cache[prompt_name] = template
            return template
        
        # Fallback to default
        template = self.DEFAULT_PROMPTS.get(prompt_name, {}).get("template")
        self._prompt_cache[prompt_name] = template
        return template
    
    def update_prompt(self, prompt_name: str, new_template: str) -> bool:
        """
        Update prompt template
        
        Args:
            prompt_name: Name of the prompt to update
            new_template: New template string
            
        Returns:
            True if successful, False otherwise
        """
        if not self.db_client.is_connected():
            return False
        
        collection = self.db_client.database[self.collection_name]
        result = collection.update_one(
            {"name": prompt_name},
            {"$set": {"template": new_template}},
            upsert=True
        )
        
        # Clear cache
        if prompt_name in self._prompt_cache:
            del self._prompt_cache[prompt_name]
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    def list_prompts(self) -> list:
        """
        List all available prompts
        
        Returns:
            List of prompt names
        """
        if not self.db_client.is_connected():
            return list(self.DEFAULT_PROMPTS.keys())
        
        collection = self.db_client.database[self.collection_name]
        return [doc["name"] for doc in collection.find({}, {"name": 1})]
    
    def get_prompt_with_variables(self, prompt_name: str, **kwargs) -> str:
        """Get prompt with variables replaced"""
        template = self.get_prompt(prompt_name)
        if not template:
            raise ValueError(f"Prompt '{prompt_name}' not found")
        
        return template.format(**kwargs)
