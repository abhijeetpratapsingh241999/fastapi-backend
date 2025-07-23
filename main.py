from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import ffmpeg
import os
import shutil

app = FastAPI(title="4kscaler API", description="4K/8K Video Upscaling Service")

TEMP_DIR = "temp"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to 4kscaler API - 4K/8K Video Upscaling Service"}

@app.get("/healthz")
def health_check():
    return {"status": "healthy"}

def upscale_video(input_path: str, output_path: str, scale_factor: int):
    try:
        probe = ffmpeg.probe(input_path)
        width = int(float(probe['streams'][0]['width']) * scale_factor)
        height = int(float(probe['streams'][0]['height']) * scale_factor)
        ffmpeg.input(input_path).output(output_path, vf=f'scale={width}:{height}', vcodec='libx264', crf=18).run()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg Error: {str(e)}")

@app.post("/upscale")
async def upscale(file: UploadFile = File(...), scale: int = 4):
    try:
        if not file.filename.endswith(('.mp4', '.mov', '.avi')):
            raise HTTPException(status_code=400, detail="Unsupported format")
        input_path = os.path.join(TEMP_DIR, file.filename)
        with open(input_path, "wb") as f:
            f.write(file.file.read())
        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])
        if duration > 10:
            raise HTTPException(status_code=400, detail="Video exceeds 10-second limit")
        output_path = os.path.join(TEMP_DIR, f"upscaled_{file.filename}")
        upscale_video(input_path, output_path, scale)
        return FileResponse(output_path, media_type="video/mp4", filename=f"upscaled_{file.filename}")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        for f in os.listdir(TEMP_DIR):
            os.remove(os.path.join(TEMP_DIR, f))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)