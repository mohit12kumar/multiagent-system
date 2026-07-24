import os
import sys
import uuid
import jwt
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Add parent directory to path so config and state can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from graph import build_graph

app = FastAPI(
    title="Medical Research Assistant API",
    description="Exposes the multi-agent clinical literature assistant with JWT auth, STT, and TTS.",
    version="1.0.0"
)

# JWT Security Setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Generate a JWT access token encoding the subject username and expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Extract and validate username from JWT bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate token credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None or username != config.API_USERNAME:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception


# Request/Response schemas
class ResearchRequest(BaseModel):
    query: str


# Compile the LangGraph application
app_graph = build_graph()


@app.get("/health")
def health():
    """Public health-check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate credentials and return JWT bearer token."""
    if form_data.username != config.API_USERNAME or form_data.password != config.API_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/research")
def run_research(request: ResearchRequest, username: str = Depends(get_current_user)):
    """Run the multi-agent LangGraph workflow for a text query."""
    if not config.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GROQ_API_KEY is not configured on this server. Please check the .env setup."
        )
        
    try:
        initial_state = {
            "query": request.query,
            "subtasks": [],
            "covered_subtasks": [],
            "pubmed_evidence": [],
            "kb_evidence": [],
            "draft_answer": "",
            "verification_notes": "",
            "verified": None,
            "revision_count": 0,
            "final_report": "",
            "next": ""
        }
        
        # Execute graph (max 50 recursion depth)
        result = app_graph.invoke(initial_state, config={"recursion_limit": 50})
        
        return {
            "query": request.query,
            "final_report": result.get("final_report", "Failed to generate report.")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing agent workflow: {str(e)}"
        )


@app.post("/research/audio")
async def run_research_audio(file: UploadFile = File(...), username: str = Depends(get_current_user)):
    """Transcribe uploaded audio file using Groq Whisper, run research workflow, and synthesize response speech."""
    if not config.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GROQ_API_KEY is not configured on this server. Please check the .env setup."
        )
        
    # Write incoming file to disk temporarily
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio")
    os.makedirs(temp_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1] or ".wav"
    temp_filename = f"upload_{uuid.uuid4().hex}{file_ext}"
    temp_filepath = os.path.join(temp_dir, temp_filename)
    
    try:
        with open(temp_filepath, "wb") as f:
            f.write(await file.read())
            
        # Transcribe audio using Groq Whisper
        from groq import Groq
        groq_client = Groq(api_key=config.GROQ_API_KEY)
        
        with open(temp_filepath, "rb") as audio_file:
            transcription = groq_client.audio.transcriptions.create(
                file=(temp_filepath, audio_file.read()),
                model="whisper-large-v3",
                response_format="json"
            )
            
        query_text = transcription.text
        if not query_text or not query_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract audio query text. Please ensure audio has clear speech."
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Audio transcription failed: {str(e)}"
        )
    finally:
        # Always clean up the temporary upload file
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass
                
    # Run the research workflow with the transcribed text query
    try:
        initial_state = {
            "query": query_text,
            "subtasks": [],
            "covered_subtasks": [],
            "pubmed_evidence": [],
            "kb_evidence": [],
            "draft_answer": "",
            "verification_notes": "",
            "verified": None,
            "revision_count": 0,
            "final_report": "",
            "next": ""
        }
        
        result = app_graph.invoke(initial_state, config={"recursion_limit": 50})
        final_report = result.get("final_report", "")
        draft_answer = result.get("draft_answer", "No research output was generated.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow execution failed: {str(e)}"
        )
        
    # Generate TTS audio file from final synthesis
    try:
        from gtts import gTTS
        
        audio_filename = f"report_{uuid.uuid4().hex}.mp3"
        output_filepath = os.path.join(temp_dir, audio_filename)
        
        # Construct narrative text
        tts_narration = f"Transcribed medical query: {query_text}. Here are the synthesized literature findings: {draft_answer}"
        
        tts = gTTS(text=tts_narration, lang="en")
        tts.save(output_filepath)
        
        audio_url = f"/audio/{audio_filename}"
    except Exception as e:
        # Log error but return text response since agent completed successfully
        audio_url = None
        print(f"TTS Synthesis failed: {e}", file=sys.stderr)
        
    return {
        "transcribed_query": query_text,
        "final_report": final_report,
        "audio_url": audio_url
    }


@app.get("/audio/{filename}")
def serve_audio(filename: str):
    """Serve synthesized MP3 speech reports."""
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_audio")
    filepath = os.path.join(temp_dir, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found or has expired."
        )
        
    return FileResponse(filepath, media_type="audio/mpeg")
