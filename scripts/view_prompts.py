"""
Script to view all prompts stored in MongoDB
"""
import sys
sys.path.append('.')

from database import PromptRepository

def main():
    print("=" * 80)
    print("PROMPTS STORED IN MONGODB")
    print("=" * 80)
    
    repo = PromptRepository()
    prompts = repo.list_prompts()
    
    print(f"\nTotal prompts: {len(prompts)}\n")
    
    for prompt_name in prompts:
        print(f"\n{'=' * 80}")
        print(f"PROMPT: {prompt_name}")
        print(f"{'=' * 80}")
        
        template = repo.get_prompt(prompt_name)
        
        # Show first 500 characters
        if len(template) > 500:
            print(template[:500] + "...")
            print(f"\n[Total length: {len(template)} characters]")
        else:
            print(template)
    
    print(f"\n{'=' * 80}")
    print("To update a prompt, use:")
    print("  PUT http://localhost:9000/prompts/{prompt_name}")
    print("=" * 80)

if __name__ == "__main__":
    main()
