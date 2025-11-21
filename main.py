from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from config import Config
from services import VideoProcessor
from services.ai_factory import AIServiceFactory
import asyncio
from concurrent.futures import ThreadPoolExecutor

Config.validate()

app = FastAPI(
    title="Video Profile Extractor API",
    version="1.0.1"
)

# Add GZIP compression for faster responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

video_processor = VideoProcessor(
    sample_rate=Config.AUDIO_SAMPLE_RATE,
    channels=Config.AUDIO_CHANNELS
)

# Use load balancer for intelligent task distribution
ai_load_balancer = AIServiceFactory.create_load_balancer()
print(f"[Load Balancer] Initialized with {len(ai_load_balancer.services)} services")

# Thread pool for parallel AI operations
executor = ThreadPoolExecutor(max_workers=3)


@app.get("/", response_class=HTMLResponse)
async def get_upload_form():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Video Profile Extractor API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }
        .info { background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
        .endpoint { background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 15px; }
        pre { background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; font-size: 12px; }
        h2 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 5px; }
        .method { display: inline-block; padding: 3px 8px; border-radius: 3px; font-weight: bold; color: white; }
        .post { background: #4CAF50; }
        .get { background: #2196F3; }
    </style>
</head>
<body>
    <h1>🎥 Video Profile Extractor API</h1>
    
    <div class="info">
        <h3>📋 API for Job Recruitment Platform</h3>
        <p><strong>Workflow:</strong></p>
        <ol>
            <li><strong>Candidate:</strong> Uploads video presentation</li>
            <li><strong>API:</strong> Extracts profile and generates professional CV</li>
            <li><strong>Company:</strong> Reviews profiles and selects candidates</li>
            <li><strong>Company:</strong> Generates customized technical test for selected candidates</li>
        </ol>
    </div>

    <h2>1. Upload Video & Extract Profile</h2>
    <div class="endpoint">
        <p><span class="method post">POST</span> <code>/upload-video</code></p>
        <form action="/upload-video" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="video/*" required>
            <button type="submit">📤 Upload and Process Video</button>
        </form>
    </div>

    <h2>2. Generate Technical Test (For Companies)</h2>
    <div class="endpoint">
        <p><span class="method post">POST</span> <code>/generate-technical-test</code></p>
        <p><strong>Use Case:</strong> Company generates customized technical test for selected candidates based on job requirements.</p>
        <pre>{
  "profession": "Software Engineer",
  "technologies": "Python, FastAPI, PostgreSQL",
  "experience": "3 years in backend development",
  "education": "Computer Science degree"
}</pre>
        <p><strong>Response:</strong> Technical test in Markdown format ready to send to candidate.</p>
        <p><em>Note: This endpoint is used by companies after reviewing candidate profiles.</em></p>
    </div>

    <h2>3. Manage Prompts</h2>
    <div class="endpoint">
        <p><span class="method get">GET</span> <code>/prompts</code> - List all prompts</p>
        <p><span class="method get">GET</span> <code>/prompts/{name}</code> - Get specific prompt</p>
    </div>

    <p><em>💡 Tip: Use Postman, curl, or your application's HTTP client to interact with the API.</em></p>
    <p><a href="/health" target="_blank">Check API Health</a> | <a href="/prompts" target="_blank">View Prompts</a></p>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    video_path = None
    audio_path = None
    
    try:
        # Process video and extract audio
        print(f"[DEBUG] Processing video file: {file.filename}")
        video_path, audio_path = video_processor.process_video(file)
        print(f"[DEBUG] Video processed successfully. Audio path: {audio_path}")
        
        # Step 1: Transcribe audio (Groq - best for transcription)
        loop = asyncio.get_event_loop()
        transcription = await loop.run_in_executor(
            executor,
            ai_load_balancer.transcribe_audio,
            audio_path
        )
        
        # Step 2 & 3: Run profile extraction and CV generation in parallel
        profile_task = loop.run_in_executor(
            executor,
            ai_load_balancer.extract_profile,
            transcription
        )
        
        # Wait for profile extraction first
        profile_data = await profile_task
        
        # Step 3: Generate CV profile (can start immediately after profile extraction)
        cv_profile = await loop.run_in_executor(
            executor,
            ai_load_balancer.generate_cv_profile,
            transcription,
            profile_data
        )
        
        return JSONResponse(content={
            "cv_profile": cv_profile,
            "profile_data": profile_data
        })
    
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"[ERROR] {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)
    
    finally:
        if video_path and audio_path:
            video_processor.cleanup(video_path, audio_path)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/prompts")
async def list_prompts():
    """List all available prompts"""
    from database import PromptRepository
    prompt_repo = PromptRepository()
    prompts = prompt_repo.list_prompts()
    return {"prompts": prompts}


@app.get("/prompts/{prompt_name}")
async def get_prompt(prompt_name: str):
    """Get a specific prompt template"""
    from database import PromptRepository
    prompt_repo = PromptRepository()
    template = prompt_repo.get_prompt(prompt_name)
    
    if not template:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")
    
    return {"name": prompt_name, "template": template}


@app.put("/prompts/{prompt_name}")
async def update_prompt(prompt_name: str, new_template: dict):
    """Update a prompt template"""
    from database import PromptRepository
    prompt_repo = PromptRepository()
    
    if "template" not in new_template:
        raise HTTPException(status_code=400, detail="Field 'template' is required")
    
    success = prompt_repo.update_prompt(prompt_name, new_template["template"])
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update prompt")
    
    return {"message": f"Prompt '{prompt_name}' updated successfully"}


@app.post("/prompts/reset")
async def reset_prompts():
    """Reset all prompts to default values (useful after code updates)"""
    from database import PromptRepository
    prompt_repo = PromptRepository()
    
    if not prompt_repo.db_client.is_connected():
        raise HTTPException(status_code=500, detail="Cannot connect to MongoDB")
    
    collection = prompt_repo.db_client.database[prompt_repo.collection_name]
    
    # Delete all existing prompts
    result = collection.delete_many({})
    deleted_count = result.deleted_count
    
    # Insert updated prompts from DEFAULT_PROMPTS
    collection.insert_many(list(prompt_repo.DEFAULT_PROMPTS.values()))
    inserted_count = len(prompt_repo.DEFAULT_PROMPTS)
    
    # Clear cache
    prompt_repo._prompt_cache.clear()
    
    return {
        "message": "All prompts reset to default values",
        "deleted": deleted_count,
        "inserted": inserted_count,
        "prompts": list(prompt_repo.DEFAULT_PROMPTS.keys())
    }


@app.post("/generate-technical-test")
async def generate_technical_test(profile_data: dict):
    """
    Generate technical test based on job requirements
    
    This endpoint is used by companies to generate customized technical tests
    for candidates who have been selected after the initial profile review.
    
    The test is generated based on:
    - Job position requirements (profession)
    - Required technologies and skills
    - Expected experience level
    - Educational background
    """
    try:
        # Validate required fields
        required_fields = ["profession", "technologies"]
        missing_fields = [field for field in required_fields if field not in profile_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Generate technical test asynchronously
        loop = asyncio.get_event_loop()
        technical_test = await loop.run_in_executor(
            executor,
            ai_load_balancer.generate_technical_test,
            profile_data
        )
        
        return JSONResponse(content={
            "technical_test_markdown": technical_test,
            "profile_summary": {
                "profession": profile_data.get("profession"),
                "technologies": profile_data.get("technologies"),
                "experience": profile_data.get("experience", "Not specified")
            }
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.HOST, port=Config.PORT)
