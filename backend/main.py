import os
import requests
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
from pydub import AudioSegment
from io import BytesIO

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Load API keys from environment variables
SILICON_FLOW_API_KEY = os.getenv("SILICON_FLOW_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")

# Check if keys are present
if not SILICON_FLOW_API_KEY or not LLM_API_KEY:
    raise RuntimeError("API keys SILICON_FLOW_API_KEY and LLM_API_KEY must be set as environment variables.")

SILICON_FLOW_API_URL = "https://api.siliconflow.cn/v1/audio/transcriptions"
LLM_API_URL = "https://api.siliconflow.cn/v1/chat/completions"
LLM_MODEL = "Qwen/Qwen3-235B-A22B"

def _correct_text_with_llm(text: str) -> str:
    """Calls the LLM to correct the given text."""
    prompt = f"请修正以下录音转录文本中的错别字、语病和不通顺之处，可以根据内容，适当修改，适当补充。删除语气词。直接返回修正后的纯文本，不要包含任何多余的解释或markdown格式:\n\n{text}"
    
    payload = {
        "model": LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "top_p": 0.7,
    }
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(LLM_API_URL, json=payload, headers=headers, timeout=120)
        response.raise_for_status()
        data = response.json()
        corrected_text = data["choices"][0]["message"]["content"].strip()
        return corrected_text
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        # Return original text if correction fails
        return text
    except (KeyError, IndexError) as e:
        print(f"Error parsing LLM response: {e}")
        return text


@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...), correct: bool = False):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        # Read file content into memory
        file_content = await file.read()

        # Determine the file format from the filename
        file_format = file.filename.split('.')[-1].lower()

        # If the file is not in a directly supported format, convert it to wav
        if file_format not in ['wav', 'mp3', 'pcm', 'opus', 'webm']:
            print(f"Unsupported format '{file_format}', attempting conversion to WAV...")
            try:
                # Create an in-memory file-like object for pydub
                audio_stream = BytesIO(file_content)
                audio = AudioSegment.from_file(audio_stream, format=file_format)
                
                # Export to an in-memory wav file
                output_stream = BytesIO()
                audio.export(output_stream, format="wav")
                output_stream.seek(0) # Rewind the stream to the beginning
                
                file_content = output_stream.read()
                filename = file.filename.rsplit('.', 1)[0] + ".wav"
                content_type = "audio/wav"
                print("Conversion to WAV successful.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to convert audio file: {e}. Make sure ffmpeg is installed.")
        else:
            filename = file.filename
            content_type = file.content_type

        files = {
            'file': (filename, file_content, content_type)
        }
        payload = {
            'model': 'FunAudioLLM/SenseVoiceSmall'
        }
        headers = {
            "Authorization": f"Bearer {SILICON_FLOW_API_KEY}"
        }
        
        response = requests.post(SILICON_FLOW_API_URL, headers=headers, data=payload, files=files)
        response.raise_for_status()
        
        transcription_data = response.json()
        raw_text = transcription_data.get("text", "")
        
        corrected_text = None
        if correct and raw_text:
            print("Correction enabled, calling LLM...")
            corrected_text = _correct_text_with_llm(raw_text)
        
        return {
            "raw_text": raw_text,
            "corrected_text": corrected_text or raw_text,
            "is_corrected": corrected_text is not None
        }

    except requests.exceptions.RequestException as e:
        # Attempt to get more detailed error from Silicon Flow response
        error_detail = "Could not retrieve detailed error from API."
        if e.response is not None:
            try:
                error_detail = e.response.json()
            except ValueError:
                error_detail = e.response.text
        raise HTTPException(status_code=500, detail=f"Error calling Silicon Flow API: {e}. Details: {error_detail}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        await file.close()

# Serve frontend static files
app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

@app.get("/")
async def read_index():
    return FileResponse('static/index.html')

@app.get("/{catchall:path}", response_class=FileResponse)
async def read_catchall(catchall: str):
    # This is a catch-all for Vue Router's history mode.
    # It serves index.html for any path that doesn't match an API route.
    return FileResponse('static/index.html')
