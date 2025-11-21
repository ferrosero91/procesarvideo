"""
Script to force update prompts in MongoDB with the corrected templates
"""
from database import PromptRepository

def update_prompts():
    """Force update all prompts in MongoDB"""
    prompt_repo = PromptRepository()
    
    print("Forcing update of all prompts in MongoDB...")
    
    # Get MongoDB collection
    if not prompt_repo.db_client.is_connected():
        print("ERROR: Cannot connect to MongoDB")
        return
    
    collection = prompt_repo.db_client.database[prompt_repo.collection_name]
    
    # Delete all existing prompts
    result = collection.delete_many({})
    print(f"Deleted {result.deleted_count} existing prompts")
    
    # Insert updated prompts from DEFAULT_PROMPTS
    collection.insert_many(list(prompt_repo.DEFAULT_PROMPTS.values()))
    print(f"Inserted {len(prompt_repo.DEFAULT_PROMPTS)} updated prompts")
    
    # Verify
    count = collection.count_documents({})
    print(f"Total prompts in database: {count}")
    
    # List prompts
    prompts = [doc["name"] for doc in collection.find({}, {"name": 1})]
    print(f"Prompts: {prompts}")
    
    print("\n✅ Prompts updated successfully!")

if __name__ == "__main__":
    update_prompts()
