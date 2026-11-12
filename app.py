import streamlit as st
import asyncio
import edge_tts
import easyocr
from pypdf import PdfReader
from docx import Document
from PIL import Image
import io

# Page configuration
st.set_page_config(page_title="Telugu Dubbing Voice Generator", page_icon="🎬", layout="wide")
st.title("🎬 Telugu Document to Cinema Dubbing Voice Converter")
st.write("Convert Telugu text from images, PDFs, and documents into humanized theatrical voices.")

# ----------------- Telugu Dubbing Presets -----------------
VOICE_STYLES = {
    "🎭 Cinema Hero / Heavy Dubbing Artist (Deep Baritone)": {
        "voice": "te-IN-MohanNeural",
        "rate": "-10%",
        "pitch": "-22Hz",
        "desc": "Deep, theatrical voice suited for dramatic narrations and dialogues."
    },
    "🎙️ Classic Movie Narrator / Audiobook": {
        "voice": "te-IN-MohanNeural",
        "rate": "-6%",
        "pitch": "-10Hz",
        "desc": "Calm, rich tone suited for historical stories and book reading."
    },
    "⚡ Radio Jockey / Fast Dialogue": {
        "voice": "te-IN-MohanNeural",
        "rate": "+12%",
        "pitch": "+4Hz",
        "desc": "Energetic, sharp and fast pacing."
    },
    "👩 Telugu Serial / Melodramatic Dubbing (Female)": {
        "voice": "te-IN-ShrutiNeural",
        "rate": "-8%",
        "pitch": "-6Hz",
        "desc": "Softer, emotive tone for storytelling."
    },
    "📢 Standard Newsreader / Assistant (Neutral)": {
        "voice": "te-IN-MohanNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
        "desc": "Clear, neutral tone for documents and articles."
    }
}

# ----------------- Helpers -----------------
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['te', 'en'], gpu=False)

reader = load_ocr()

def extract_from_file(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    file_bytes = uploaded_file.read()
    if ext in ["jpg", "jpeg", "png"]:
        img = Image.open(io.BytesIO(file_bytes))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        res = reader.readtext(buf.getvalue(), detail=0)
        return " ".join(res)
    elif ext == "pdf":
        pdf = PdfReader(io.BytesIO(file_bytes))
        text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
        if not text:
            # Fallback for scanned image-only PDF
            img = Image.open(io.BytesIO(file_bytes))
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            res = reader.readtext(buf.getvalue(), detail=0)
            text = " ".join(res)
        return text
    elif ext == "docx":
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])
    elif ext == "txt":
        return file_bytes.decode("utf-8")
    return ""

async def generate_audio(text, voice, rate, pitch, outfile="telugu_dubbing.mp3"):
    comm = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    await comm.save(outfile)

# ----------------- Layout -----------------
col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.subheader("1. Input Document or Image")
    up_file = st.file_uploader("Upload Image, PDF, DOCX or TXT", type=["png", "jpg", "jpeg", "pdf", "docx", "txt"])
    extracted = ""
    if up_file:
        with st.spinner("Extracting Telugu text..."):
            extracted = extract_from_file(up_file)
            
    final_text = st.text_area("Telugu Text Editor (Review/Edit text here):", value=extracted, height=220)

with col2:
    st.subheader("2. Select Dubbing Artist Persona")
    style_choice = st.selectbox("Choose Dubbing Style:", list(VOICE_STYLES.keys()))
    selected_preset = VOICE_STYLES[style_choice]
    
    st.info(f"**Style Details:** {selected_preset['desc']}")

    # Fine-tuning sliders
    with st.expander("🎛️ Advanced Voice Tuning (Optional)"):
        st.write("Manually adjust if you want it deeper or faster:")
        fine_pitch = st.slider("Pitch (Lower = Deeper Voice)", -40, 20, int(selected_preset["pitch"].replace("Hz", "")))
        fine_rate = st.slider("Speed / Pacing", -30, 30, int(selected_preset["rate"].replace("%", "")))
        
        final_pitch_str = f"{'+' if fine_pitch >= 0 else ''}{fine_pitch}Hz"
        final_rate_str = f"{'+' if fine_rate >= 0 else ''}{fine_rate}%"

    if st.button("🎙️ Generate Dubbing Audio", type="primary"):
        if not final_text.strip():
            st.warning("Please upload a file or write some Telugu text first!")
        else:
            with st.spinner("Synthesizing Telugu dubbing artist speech..."):
                asyncio.run(generate_audio(
                    text=final_text,
                    voice=selected_preset["voice"],
                    rate=final_rate_str,
                    pitch=final_pitch_str
                ))
                st.success("Dubbing Generated Successfully!")
                
                with open("telugu_dubbing.mp3", "rb") as f:
                    audio_data = f.read()
                    st.audio(audio_data, format="audio/mp3")
                    st.download_button("⬇️ Download Dubbed Audio (MP3)", audio_data, "telugu_dubbing.mp3", "audio/mp3")