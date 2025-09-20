from fastapi import BackgroundTasks, Depends, APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime, timezone
from models.chat_model import ChatRequest, DeleteChatRequest
from configurations.db import chat_collection, checkpoint_writes_collection, checkpoints_collection, deleted_chat_collection
from utils.chat_agent_utils import respond, save_history
from utils.voice_utils import speech_to_text, text_to_speech
from dotenv import load_dotenv
import os
import uuid

load_dotenv()
chat_router = APIRouter()

# Get base URL from environment variable, default to localhost for development
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

@chat_router.post("/api/chat")
async def chat_endpoint(
    background_tasks: BackgroundTasks,
    input_type: str = Form(..., description="Either 'text' or 'voice'"),
    user_id: str = Form(...),
    message: str = Form(None),  # text input if input_type=text
    audio: UploadFile = File(None)  # voice input if input_type=voice
):
    try:
        # Step 1: Handle input
        if input_type == "voice" and audio is not None:
            temp_audio_path = f"temp_{user_id}.wav"
            with open(temp_audio_path, "wb") as f:
                f.write(await audio.read())
            user_message = speech_to_text(temp_audio_path)
            os.remove(temp_audio_path)
        elif input_type == "text" and message:
            user_message = message
        else:
            return JSONResponse(status_code=400, content={"error": "Invalid input."})

        # Step 2: Get agent response
        bot_response = await respond(user_id, user_message)

        # Step 3: Generate unique audio filename and TTS file
        audio_id = str(uuid.uuid4())
        audio_filename = f"tts_{user_id}_{audio_id}.mp3"
        print(f"Generating audio for response length: {len(bot_response)} characters")
        audio_path = text_to_speech(bot_response, save_path=audio_filename)
        
        # Check if audio file was created and has content
        if os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"Audio file created: {audio_path}, size: {file_size} bytes")
        else:
            print(f"Warning: Audio file not created: {audio_path}")

        # Step 4: Save history with audio URL in background
        audio_url = f"{BASE_URL}/api/chat/audio/{user_id}/{audio_id}"
        background_tasks.add_task(save_history, user_id, user_message, bot_response, audio_url)

        return JSONResponse(
            status_code=200,
            content={
                "response": bot_response,
                "audio_url": audio_url
            }
        )
    except Exception as e:
        print("Error while working on chat request: ", str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})


# New endpoint to serve audio files
@chat_router.get("/api/chat/audio/{user_id}/{audio_id}")
async def get_audio(user_id: str, audio_id: str):
    file_path = f"tts_{user_id}_{audio_id}.mp3"
    print(f"Requesting audio file: {file_path}")
    
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        print(f"Audio file found: {file_path}, size: {file_size} bytes")
        
        if file_size > 0:
            return FileResponse(file_path, media_type="audio/mpeg", filename="response.mp3")
        else:
            print(f"Warning: Audio file is empty: {file_path}")
            return JSONResponse(status_code=404, content={"error": "Audio file is empty."})
    else:
        print(f"Audio file not found: {file_path}")
        return JSONResponse(status_code=404, content={"error": "Audio file not found."})

@chat_router.get("/api/chatHistory/{user_id}")
async def get_chat_history(user_id: str):
    try:
        record = chat_collection.find_one({"user_id": user_id})
        if not record or "history" not in record:
            return JSONResponse(status_code=200, content={"history": []})
        history=[
            {
                "role": msg["role"], 
                "content": msg["content"],
                "audio_url": msg.get("audio_url")  # Include audio_url if it exists
            } for msg in record["history"]
        ]
        history.reverse()
        return JSONResponse(status_code=200, content={"history": history})
    except Exception as e:
        print("Error while working on chatHistory request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})

@chat_router.delete("/api/chat")
async def delete_and_archive_chat(delete_request: DeleteChatRequest):
    try:
        user_id = delete_request.user_id
        record = chat_collection.find_one({"user_id": user_id})

        if not record or "history" not in record:
            return JSONResponse(status_code=404, content={"message": "User chat history not found"})

        if not record["history"]:
            return JSONResponse(status_code=200, content={"message": "Chat history is already reset"})

        try:
            checkpoint_writes_collection.delete_many({ "thread_id": user_id })
            checkpoints_collection.delete_many({ "thread_id": user_id })
        except Exception as e:
            print("error while deleting=",e)
        record["deleted_at"] = datetime.now(timezone.utc)
        record.pop("_id", None)
        deleted_chat_collection.insert_one(record)
        chat_collection.update_one({"user_id": user_id}, {"$set": {"history": []}})

        return JSONResponse(status_code=200, content={"message": "Chat history reset successfully."})
    except Exception as e:
        print("Error while working on chat delete request: ",str(e))
        return JSONResponse(status_code=500, content={"error": "We are facing an error. Please try again later."})
