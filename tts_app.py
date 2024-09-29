import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from PyPDF2 import PdfReader
import toml
import sys
import os
import textwrap

# Log the current Python environment
st.write(f"Python executable: {sys.executable}")
st.write(f"Python version: {sys.version}")

# Load secrets from toml file
try:
    secrets = toml.load('secrets.toml')
    api_key = secrets['speech_service']['api_key']
    region = secrets['speech_service']['region']
except FileNotFoundError:
    st.error("The secrets.toml file was not found. Please ensure it is in the correct location.")
    st.stop()
except KeyError:
    st.error("The secrets.toml file does not have the correct keys. Please check your file.")
    st.stop()

# Map regions to full names for English and Spanish locales
REGION_MAPPING = {
    "en-US": "United States",
    "en-GB": "United Kingdom",
    "es-ES": "Spain",  # Limit Spanish voices to Spain
}

# Function to get available voices from Azure Speech Service
def get_available_voices(api_key, region):
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    voices = synthesizer.get_voices_async().get().voices
    return voices

# Organize voices by language and region (English and Spanish (Spain))
def organize_voices_by_language(voices):
    voices_by_language = {
        "English": [],
        "Spanish (Spain)": []
    }
    
    for voice in voices:
        if voice.locale == "es-ES":  # Spanish (Spain)
            voices_by_language["Spanish (Spain)"].append(voice)
        elif voice.locale.startswith("en"):  # English voices
            voices_by_language["English"].append(voice)

    return voices_by_language

# Function to preview selected voice with a greeting and introduction
def preview_voice(voice, language):
    if language == "English":
        preview_text = "Hello! My name is {} and I will be your voice.".format(voice)
    else:
        preview_text = "¡Hola! Me llamo {} y seré tu voz.".format(voice)
    output_filename = "preview.mp3"
    text_to_speech_in_chunks(preview_text, voice, output_filename)
    # Play the preview
    st.audio(output_filename)

# Function to split text into smaller chunks (less than 524288 bytes)
def split_text_into_chunks(text, max_chunk_size=5000):
    return textwrap.wrap(text, max_chunk_size)

# Function to synthesize text in chunks and concatenate them
def text_to_speech_in_chunks(text, voice, output_filename="output.mp3"):
    chunks = split_text_into_chunks(text)
    st.info(f"Text is split into {len(chunks)} chunks for processing.")

    audio_files = []
    for i, chunk in enumerate(chunks):
        st.info(f"Processing chunk {i + 1}...")
        audio_file = synthesize_chunk(chunk, voice, i + 1)
        if audio_file:
            audio_files.append(audio_file)

    # Combine the audio files into a single MP3 file
    if audio_files:
        with open(output_filename, "wb") as output:
            for audio_file in audio_files:
                with open(audio_file, "rb") as af:
                    output.write(af.read())
        st.success(f"All chunks synthesized successfully and saved as {output_filename}")
        # Create download link for the combined MP3 file
        with open(output_filename, "rb") as f:
            st.download_button(
                label="Download MP3",
                data=f,
                file_name=output_filename,
                mime="audio/mpeg"
            )

# Function to read a text file
def read_text_file(file):
    try:
        return file.read().decode("utf-8")
    except Exception as e:
        st.error(f"An error occurred while reading the text file: {str(e)}")
        return None

# Function to read a PDF file
def read_pdf(file):
    try:
        pdf = PdfReader(file)
        text = ""
        for page in range(len(pdf.pages)):
            text += pdf.pages[page].extract_text()
        return text
    except Exception as e:
        st.error(f"An error occurred while reading the PDF file: {str(e)}")
        return None

# Streamlit App
def main():
    st.title("Text-to-Speech Converter")

    # Step 1: Display available voices organized by language
    voices = get_available_voices(api_key, region)
    voices_by_language = organize_voices_by_language(voices)

    # Step 2: Let user select a language
    selected_language = st.selectbox("Select Language", options=["English", "Spanish (Spain)"])
    
    # Step 3: Let user select a voice from the selected language
    voice_options = {voice.short_name: f"{voice.local_name} ({REGION_MAPPING.get(voice.locale, voice.locale)})" for voice in voices_by_language[selected_language]}
    selected_voice = st.selectbox("Select Voice", options=list(voice_options.keys()), format_func=lambda x: voice_options[x])

    # Step 4: Voice preview
    if st.button("Preview Voice"):
        preview_voice(selected_voice, selected_language)

    # Step 5: File uploader for text or PDF
    uploaded_file = st.file_uploader("Upload a text or PDF file", type=["txt", "pdf"])

    if uploaded_file is not None:
        file_type = uploaded_file.type
        if file_type == "application/pdf":
            text = read_pdf(uploaded_file)
        else:
            text = read_text_file(uploaded_file)

        # Check if text was successfully extracted
        if text:
            if st.button("Convert to Speech"):
                output_filename = "output.mp3"
                # Convert text to speech in chunks
                text_to_speech_in_chunks(text, selected_voice, output_filename)
        else:
            st.error("Unable to extract text from the uploaded file.")

if __name__ == "__main__":
    main()