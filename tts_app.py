import streamlit as st
import azure.cognitiveservices.speech as speechsdk
from PyPDF2 import PdfReader
import toml
import sys
import os

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

# Function to get available voices from Azure Speech Service
def get_available_voices(api_key, region):
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
    voices = synthesizer.get_voices_async().get().voices
    return voices

# Function to convert text to speech with progress bar and downloadable MP3
def text_to_speech(text, voice, output_filename="output.mp3"):
    try:
        speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
        speech_config.speech_synthesis_voice_name = voice

        # Create a speech synthesizer
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

        # Add progress bar
        progress_bar = st.progress(0)

        # Synthesize the text to speech with progress updates
        result = synthesizer.speak_text_async(text).get()

        # Update progress to 100% on completion
        progress_bar.progress(100)

        # Check the result
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            st.success("Speech synthesized successfully.")
            # Create download link for MP3 file
            with open(output_filename, "rb") as f:
                st.download_button(
                    label="Download MP3",
                    data=f,
                    file_name=output_filename,
                    mime="audio/mpeg"
                )
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

    # Step 1: Display available voices and allow user to select
    voices = get_available_voices(api_key, region)
    voice_options = {voice.short_name: f"{voice.local_name} ({voice.locale})" for voice in voices}
    selected_voice = st.selectbox("Select Voice", options=list(voice_options.keys()), format_func=lambda x: voice_options[x])

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
                output_filename = "output.mp3"
                # Convert text to speech and show progress
                text_to_speech(text, selected_voice, output_filename)
        else:
            st.error("Unable to extract text from the uploaded file.")

if __name__ == "__main__":
    main()