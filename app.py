import streamlit as st
import asyncio
import edge_tts
import easyocr
from pypdf import PdfReader
from docx import Document
from PIL import Image
import io
import os

# Page configuration
st.set_page_config(page_title="Telugu Document to Speech Converter", page_icon="🎙️", layout="wide")

st.title("🎙️ Telugu OCR & Document to Speech Converter")
st.write("Convert Telugu text from Images, PDFs, and Word documents into customizable natural audio.")

# ----------------- Voice Configurations -----------------
VOICES = {
    "Female (Shruti Neural)": "te-IN-ShrutiNeural",
    "Male (Mohan Neural)": "te-IN-MohanNeural"
}

# ----------------- Helper Functions -----------------
@st.cache_resource
def load_ocr_reader():
    # Load EasyOCR for Telugu ('te') and English ('en')
    return easyocr.Reader(['te', 'en'], gpu=False)

reader = load_ocr_reader()

def extract_text_from_pdf(file_bytes):
    pdf = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()

def extract_text_from_docx(file_bytes):
    doc = Document(io.BytesIO(file_bytes))
    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return text

def extract_text_from_image(image_bytes):
    # OCR using EasyOCR
    image = Image.open(io.BytesIO(image_bytes))
    image_bytes_io = io.BytesIO()
    image.save(image_bytes_io, format="PNG")
    
    results = reader.readtext(image_bytes_io.getvalue(), detail=0)
    return " ".join(results)

async def generate_telugu_tts(text, voice, rate_str, pitch_str, output_path="output.mp3"):
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate_str,
        pitch=pitch_str
    )
    await communicate.save(output_path)

# ----------------- UI Layout -----------------
col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.subheader("1. Upload File")
    uploaded_file = st.file_uploader(
        "Upload an Image, PDF, DOCX, or TXT file", 
        type=["png", "jpg", "jpeg", "pdf", "docx", "txt"]
    )
    
    extracted_text = ""
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        file_bytes = uploaded_file.read()

        with st.spinner("Extracting Telugu text..."):
            try:
                if file_ext in ["jpg", "jpeg", "png"]:
                    st.image(file_bytes, caption="Uploaded Image", use_container_width=True)
                    extracted_text = extract_text_from_image(file_bytes)
                elif file_ext == "pdf":
                    extracted_text = extract_text_from_pdf(file_bytes)
                    if not extracted_text:
                        st.info("No selectable text found. Attempting OCR scan...")
                        # If digital extraction fails, treat pages as images
                        extracted_text = extract_text_from_image(file_bytes)
                elif file_ext == "docx":
                    extracted_text = extract_text_from_docx(file_bytes)
                elif file_ext == "txt":
                    extracted_text = file_bytes.decode("utf-8")
            except Exception as e:
                st.error(f"Error processing file: {e}")

    # Text Display / Editable Area
    st.subheader("2. Review & Edit Telugu Text")
    final_text = st.text_area(
        "Extracted Text (You can fix or modify the text here):",
        value=extracted_text,
        height=200
    )

with col2:
    st.subheader("3. Voice Customization")
    
    # Voice selection
    selected_voice_name = st.selectbox("Select Telugu Voice:", list(VOICES.keys()))
    selected_voice = VOICES[selected_voice_name]
    
    # Speed / Rate
    speed_percent = st.slider("Speech Rate / Speed", min_value=-50, max_value=50, value=0, step=5)
    rate_str = f"{'+' if speed_percent >= 0 else ''}{speed_percent}%"
    
    # Pitch
    pitch_hz = st.slider("Pitch (Tone)", min_value=-50, max_value=50, value=0, step=5)
    pitch_str = f"{'+' if pitch_hz >= 0 else ''}{pitch_hz}Hz"
    
    st.write(f"**Selected Parameters:** Voice: `{selected_voice}`, Speed: `{rate_str}`, Pitch: `{pitch_str}`")

    # Generate Audio Button
    if st.button("🔊 Convert to Telugu Audio", type="primary"):
        if not final_text.strip():
            st.warning("Please upload a file with Telugu text or enter text manually.")
        else:
            with st.spinner("Generating Telugu speech..."):
                try:
                    output_file = "telugu_audio.mp3"
                    # Run async TTS generator
                    asyncio.run(generate_telugu_tts(
                        text=final_text,
                        voice=selected_voice,
                        rate_str=rate_str,
                        pitch_str=pitch_str,
                        output_path=output_file
                    ))
                    
                    st.success("Audio generated successfully!")
                    
                    # Play Audio
                    with open(output_file, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/mp3")
                        
                        # Download Button
                        st.download_button(
                            label="⬇️ Download Telugu MP3",
                            data=audio_bytes,
                            file_name="telugu_speech.mp3",
                            mime="audio/mp3"
                        )
                except Exception as e:
                    st.error(f"TTS Error: {e}")