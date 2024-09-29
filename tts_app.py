import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from PyPDF2 import PdfReader
import toml
import sys

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

# Function to convert text to speech with detailed error logging
def text_to_speech(text):
    try:
        # Configure the speech service
        speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

        # Create a speech synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Synthesize the text to speech
        result = synthesizer.speak_text_async(text).get()

        # Check the result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            st.success("Speech synthesized successfully.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            st.error(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                st.error(f"Error details: {cancellation_details.error_details}")
                st.error(f"Did you set the correct API key and region?")
    except Exception as e:
        st.error(f"An error occurred during speech synthesis: {str(e)}")

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

    # File uploader for text or PDF
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
                text_to_speech(text)
        else:
            st.error("Unable to extract text from the uploaded file.")

if __name__ == "__main__":
    main()