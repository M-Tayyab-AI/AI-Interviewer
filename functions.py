import os
import httpx
import time

from deepgram import DeepgramClient, PrerecordedOptions, FileSource, SpeakOptions
import fitz
import docx2txt
from google import genai
from google.genai import types
from prompts import system_prompt
from dotenv import load_dotenv

from constants import SST_MODEL,TTS_MODEL,GEMINI_MODEL
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


async def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text") + "\n"
        return text
    except Exception as e:
        raise RuntimeError(f"Failed to extract text from PDF: {e}")


async def extract_text_from_docx(file_path: str):
    """Extracts text from a DOCX file using docx2txt."""
    try:
        text = docx2txt.process(file_path)
        return text
    except Exception as e:
        raise e


async def extract_text_from_txt(file_path: str):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        return text
    except Exception as e:
        raise e


def STT(audio_file_path, max_retries=3, timeout=60):
    """
    This function takes the path to an audio file, sends it to Deepgram for transcription,
    and returns the transcribed text. Includes retry logic to handle timeouts.
    """
    deepgram = DeepgramClient()
    retries = 0

    while retries < max_retries:
        try:
            # Read the audio file data
            with open(audio_file_path, "rb") as file:
                buffer_data = file.read()

            # Check if the file is too large (>10MB)
            file_size_mb = len(buffer_data) / (1024 * 1024)
            if file_size_mb > 10:
                print(f"Warning: Audio file is {file_size_mb:.2f}MB which may cause timeout issues.")

            payload: FileSource = {
                "buffer": buffer_data,
            }

            options = PrerecordedOptions(
                model=SST_MODEL,
                smart_format=True,
            )

            response = deepgram.listen.rest.v("1").transcribe_file(
                payload,
                options,
                timeout=timeout
            )

            return response["results"]["channels"][0]["alternatives"][0]["transcript"]

        except (httpx.WriteTimeout, httpx.ReadTimeout) as e:
            retries += 1
            if retries >= max_retries:
                print(f"Failed after {max_retries} attempts due to timeout.")
                return "Sorry, the transcription service timed out. Please try a shorter recording."

            print(f"Timeout occurred. Retrying ({retries}/{max_retries})...")
            time.sleep(2 ** retries)

        except Exception as e:
            print(f"Exception during transcription: {e}")
            return f"Error transcribing audio: {str(e)}"


def TTS(text, filename):
    """
    Converts the given text into speech and saves it as a WAV file.
    """
    try:
        deepgram = DeepgramClient()
        options = SpeakOptions(
            model=TTS_MODEL,
        )

        deepgram.speak.rest.v("1").save(filename, {"text": text}, options)
        return filename

    except Exception as e:
        print(f"TTS Exception: {e}")
        return None


async def model_generation(user_cv_text: str, chat_history: list):
    main_prompt = system_prompt(user_cv=user_cv_text, chat_history=chat_history)

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(system_instruction=main_prompt, temperature=0.2)
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(
                text=f"Please start the interview. This is Chat history: '{chat_history}' Now ask me next questions please")]
        )
    ]

    try:
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )
        return response.text

    except Exception as e:
        raise e