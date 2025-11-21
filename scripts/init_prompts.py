"""
Script to initialize or reset prompts in MongoDB
"""
import sys
sys.path.append('.')

from database import PromptRepository

def main():
    print("Initializing prompts in MongoDB...")
    repo = PromptRepository()
    
    print("\nAvailable prompts:")
    for prompt_name in repo.list_prompts():
        print(f"  - {prompt_name}")
    
    print("\nPrompts initialized successfully!")
    print("\nYou can now:")
    print("  - View prompts: GET http://localhost:9000/prompts")
    print("  - Update prompts: PUT http://localhost:9000/prompts/{prompt_name}")

if __name__ == "__main__":
    main()
