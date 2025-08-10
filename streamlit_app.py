import streamlit as st
import os
import tempfile
import asyncio
import threading
import time
import io

# Import functions
from functions import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    STT,
    TTS,
    model_generation
)

# Audio recording imports
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write


class AudioRecorder:
    def __init__(self, max_duration=90, fs=44100):
        self.max_duration = max_duration
        self.fs = fs
        self.recording = False
        self.audio_data = []
        self.start_time = None
        self.stream = None

    def start_recording(self):
        """Start recording audio"""
        self.recording = True
        self.audio_data = []
        self.start_time = time.time()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"Recording status: {status}")
            if self.recording:
                self.audio_data.append(indata.copy())

        self.stream = sd.InputStream(
            samplerate=self.fs,
            channels=1,
            dtype='int16',
            callback=callback
        )
        self.stream.start()

    def stop_recording(self):
        """Stop recording and return audio file path"""
        if not self.recording:
            return None

        self.recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.audio_data:
            return None

        try:
            # Convert recorded chunks into a single NumPy array
            final_audio = np.concatenate(self.audio_data, axis=0)

            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav', mode='wb') as tmp_file:
                write(tmp_file.name, self.fs, final_audio)
                return tmp_file.name
        except Exception as e:
            print(f"Error saving recording: {e}")
            return None

    def get_recording_duration(self):
        """Get current recording duration"""
        if self.start_time and self.recording:
            return time.time() - self.start_time
        return 0

    def is_max_duration_reached(self):
        """Check if maximum duration is reached"""
        return self.get_recording_duration() >= self.max_duration


# Page configuration
st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'audio_recorder' not in st.session_state:
    st.session_state.audio_recorder = AudioRecorder()
if 'user_cv_text' not in st.session_state:
    st.session_state.user_cv_text = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'waiting_for_response' not in st.session_state:
    st.session_state.waiting_for_response = False
if 'recording_active' not in st.session_state:
    st.session_state.recording_active = False
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = None
if 'show_transcription' not in st.session_state:
    st.session_state.show_transcription = False
if 'audio_file_path' not in st.session_state:
    st.session_state.audio_file_path = None

# Main title
st.title("📋 AI Interview Assistant")
st.markdown("Upload your CV and start an interactive interview session!")

# Sidebar for file upload
with st.sidebar:
    st.header("📄 Upload Your CV")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt'],
        help="Upload your CV in PDF, DOCX, or TXT format"
    )

    if uploaded_file is not None:
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()

        if file_extension not in ['.pdf', '.docx', '.txt']:
            st.warning("⚠️ Please upload only PDF, DOCX, or TXT files!")
        else:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name

            # Process the file based on extension
            try:
                with st.spinner("Processing your CV..."):
                    if file_extension == '.pdf':
                        user_cv_text = asyncio.run(extract_text_from_pdf(temp_file_path))
                    elif file_extension == '.docx':
                        user_cv_text = asyncio.run(extract_text_from_docx(temp_file_path))
                    elif file_extension == '.txt':
                        user_cv_text = asyncio.run(extract_text_from_txt(temp_file_path))

                # Clean up temporary file
                os.unlink(temp_file_path)

                # Store in session state
                st.session_state.user_cv_text = user_cv_text
                st.success("✅ CV processed successfully!")

                # Show preview of extracted text
                with st.expander("Preview CV Text"):
                    preview_text = user_cv_text[:500] + "..." if len(user_cv_text) > 500 else user_cv_text
                    st.text_area("Extracted Text", value=preview_text, height=200, disabled=True)

            except Exception as e:
                st.error(f"❌ Error processing CV: {str(e)}")
                # Clean up on error
                try:
                    os.unlink(temp_file_path)
                except:
                    pass

# Main interview interface
col1, col2 = st.columns([2, 1])

with col1:
    st.header("💬 Interview Session")

    # Start interview button
    if st.session_state.user_cv_text and not st.session_state.interview_started:
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            st.session_state.interview_started = True
            st.session_state.chat_history = []
            st.session_state.current_question = None
            st.session_state.waiting_for_response = False
            st.rerun()

    # Interview in progress
    if st.session_state.interview_started:
        st.success("🎯 Interview in progress...")

        # Generate new question if not waiting for response
        if not st.session_state.waiting_for_response and st.session_state.current_question is None:
            with st.spinner("AI is preparing the next question..."):
                try:
                    response = asyncio.run(model_generation(
                        user_cv_text=st.session_state.user_cv_text,
                        chat_history=st.session_state.chat_history
                    ))
                    st.session_state.current_question = response
                    st.session_state.waiting_for_response = True
                    # Clean up any previous audio file
                    if st.session_state.audio_file_path:
                        try:
                            os.unlink(st.session_state.audio_file_path)
                        except:
                            pass
                        st.session_state.audio_file_path = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error generating question: {str(e)}")

        # Display current question
        if st.session_state.current_question:
            st.subheader("🤖 AI Interviewer:")
            st.write(st.session_state.current_question)

            # Convert to speech and play
            if not st.session_state.audio_file_path:
                try:
                    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    temp_audio_file.close()

                    result = TTS(text=st.session_state.current_question, filename=temp_audio_file.name)
                    if result and os.path.exists(temp_audio_file.name):
                        st.session_state.audio_file_path = temp_audio_file.name
                except Exception as e:
                    st.error(f"❌ Error generating speech: {str(e)}")

            # Play audio if available
            if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
                try:
                    with open(st.session_state.audio_file_path, 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    st.warning(f"Could not play audio: {str(e)}")

        # Recording controls
        if st.session_state.waiting_for_response:
            st.subheader("🎙️ Your Response")

            # Show transcription review if available
            if st.session_state.show_transcription and st.session_state.transcribed_text:
                st.success("✅ Recording transcribed successfully!")
                st.write("**Please review and edit your response if needed:**")

                # Editable transcription
                edited_response = st.text_area(
                    "Your Response (you can edit this):",
                    value=st.session_state.transcribed_text,
                    height=100,
                    key=f"edit_response_{len(st.session_state.chat_history)}"
                )

                col_submit, col_rerecord = st.columns(2)

                with col_submit:
                    if st.button("✅ Submit Response", type="primary", use_container_width=True):
                        if edited_response.strip():
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "AI": st.session_state.current_question,
                                "User": edited_response.strip()
                            })

                            # Reset states
                            st.session_state.current_question = None
                            st.session_state.waiting_for_response = False
                            st.session_state.transcribed_text = None
                            st.session_state.show_transcription = False

                            st.success("✅ Response submitted!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ Please enter a response.")

                with col_rerecord:
                    if st.button("🎤 Record Again", use_container_width=True):
                        # Reset transcription states
                        st.session_state.transcribed_text = None
                        st.session_state.show_transcription = False
                        st.rerun()

            else:
                # Recording interface
                if not st.session_state.recording_active:
                    # Start recording button
                    if st.button("🎤 Start Recording", type="primary", use_container_width=True):
                        try:
                            st.session_state.audio_recorder.start_recording()
                            st.session_state.recording_active = True
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error starting recording: {str(e)}")
                else:
                    # Show recording status
                    duration = st.session_state.audio_recorder.get_recording_duration()
                    remaining = st.session_state.audio_recorder.max_duration - duration

                    if remaining > 0:
                        st.info(
                            f"🔴 Recording... ({duration:.1f}s / Max: {st.session_state.audio_recorder.max_duration}s) - {remaining:.0f}s remaining")

                        # Stop recording button
                        if st.button("⏹️ Stop Recording", type="secondary", use_container_width=True):
                            # Stop recording and process
                            audio_file_path = st.session_state.audio_recorder.stop_recording()
                            st.session_state.recording_active = False

                            if audio_file_path and os.path.exists(audio_file_path):
                                # Process the recorded audio
                                with st.spinner("🔄 Transcribing your response..."):
                                    try:
                                        user_response_text = STT(audio_file_path=audio_file_path)

                                        # Clean up the temporary audio file
                                        try:
                                            os.unlink(audio_file_path)
                                        except:
                                            pass

                                        if user_response_text and user_response_text.strip():
                                            # Store transcription and show for review
                                            st.session_state.transcribed_text = user_response_text.strip()
                                            st.session_state.show_transcription = True
                                            st.rerun()
                                        else:
                                            st.error("❌ No speech detected. Please try again.")

                                    except Exception as e:
                                        st.error(f"❌ Error transcribing audio: {str(e)}")
                                        try:
                                            os.unlink(audio_file_path)
                                        except:
                                            pass
                            else:
                                st.error("❌ Recording failed. Please try again.")
                    else:
                        # Max duration reached
                        st.warning(
                            f"⏰ Maximum recording time ({st.session_state.audio_recorder.max_duration}s) reached. Stopping automatically...")
                        audio_file_path = st.session_state.audio_recorder.stop_recording()
                        st.session_state.recording_active = False

                        if audio_file_path and os.path.exists(audio_file_path):
                            # Process the recorded audio
                            with st.spinner("🔄 Transcribing your response..."):
                                try:
                                    user_response_text = STT(audio_file_path=audio_file_path)
                                    try:
                                        os.unlink(audio_file_path)
                                    except:
                                        pass

                                    if user_response_text and user_response_text.strip():
                                        st.session_state.transcribed_text = user_response_text.strip()
                                        st.session_state.show_transcription = True
                                        st.rerun()
                                    else:
                                        st.error("❌ No speech detected. Please try again.")

                                except Exception as e:
                                    st.error(f"❌ Error transcribing audio: {str(e)}")

                # Alternative text input (always available)
                st.markdown("---")
                st.markdown("**Or type your response directly:**")
                user_text_input = st.text_area(
                    "Type your answer here:",
                    key=f"direct_text_input_{len(st.session_state.chat_history)}",
                    height=100
                )

                col_text_submit, col_end = st.columns(2)

                with col_text_submit:
                    if st.button("📝 Submit Text Response", use_container_width=True):
                        if user_text_input.strip():
                            # Add to chat history
                            st.session_state.chat_history.append({
                                "AI": st.session_state.current_question,
                                "User": user_text_input.strip()
                            })

                            # Reset for next question
                            st.session_state.current_question = None
                            st.session_state.waiting_for_response = False

                            st.success("✅ Text response submitted!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.warning("⚠️ Please enter a response.")

                with col_end:
                    if st.button("🔚 End Interview", use_container_width=True):
                        # Stop any active recording
                        if st.session_state.recording_active:
                            st.session_state.audio_recorder.stop_recording()
                            st.session_state.recording_active = False

                        # Clean up audio file
                        if st.session_state.audio_file_path:
                            try:
                                os.unlink(st.session_state.audio_file_path)
                            except:
                                pass
                            st.session_state.audio_file_path = None

                        # Reset all states
                        st.session_state.interview_started = False
                        st.session_state.current_question = None
                        st.session_state.waiting_for_response = False
                        st.session_state.transcribed_text = None
                        st.session_state.show_transcription = False

                        st.success("✅ Interview ended!")
                        st.rerun()

with col2:
    st.header("📊 Interview Progress")

    if st.session_state.chat_history:
        st.metric("Questions Asked", len(st.session_state.chat_history))

        with st.expander("View Chat History", expanded=True):
            for i, exchange in enumerate(st.session_state.chat_history, 1):
                st.write(f"**Q{i}:** {exchange['AI'][:100]}...")
                st.write(f"**A{i}:** {exchange['User'][:100]}...")
                st.divider()
    else:
        st.info("No questions asked yet.")

# Footer
st.markdown("---")
st.markdown(
    "🚀 **Tips:** Start/stop recording manually (max 90s), review transcription before submitting, or use direct text input!"
)