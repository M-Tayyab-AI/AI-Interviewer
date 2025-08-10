import streamlit as st
import os
import tempfile
import asyncio
import time

# Import functions
from functions import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    STT,
    TTS,
    model_generation
)


def _render_text_input():
    """Render text input interface"""
    user_text_input = st.text_area(
        "📝 Type your answer here:",
        key=f"text_input_{len(st.session_state.chat_history)}",
        height=150,
        placeholder="Share your thoughts, experiences, and examples relevant to this question...",
        help="💡 Tip: Provide specific examples and detailed explanations."
    )

    # Response metrics
    if user_text_input:
        word_count = len(user_text_input.split())
        char_count = len(user_text_input)

        col_words, col_chars = st.columns(2)
        with col_words:
            st.metric("Words", word_count)
        with col_chars:
            st.metric("Characters", char_count)

        if word_count < 10:
            st.warning("💬 Consider providing more detail for a better interview experience.")
        elif word_count > 200:
            st.info("📝 Great detail! You might want to be more concise in a real interview.")

    # Action buttons
    col_submit, col_skip, col_end = st.columns(3)

    with col_submit:
        if st.button("✅ Submit Response", type="primary", use_container_width=True):
            if user_text_input.strip():
                st.session_state.chat_history.append({
                    "AI": st.session_state.current_question,
                    "User": user_text_input.strip()
                })
                st.session_state.current_question = None
                st.session_state.waiting_for_response = False
                st.success("✅ Response submitted!")
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("⚠️ Please enter a response.")

    with col_skip:
        if st.button("⏭️ Skip Question", use_container_width=True):
            st.session_state.chat_history.append({
                "AI": st.session_state.current_question,
                "User": "[Skipped question]"
            })
            st.session_state.current_question = None
            st.session_state.waiting_for_response = False
            st.info("⏭️ Question skipped.")
            time.sleep(1)
            st.rerun()

    with col_end:
        if st.button("🔚 End Interview", use_container_width=True):
            if st.session_state.audio_file_path:
                try:
                    os.unlink(st.session_state.audio_file_path)
                except:
                    pass
                st.session_state.audio_file_path = None

            if st.session_state.chat_history:
                st.success(f"✅ Interview completed! You answered {len(st.session_state.chat_history)} questions.")

            st.session_state.interview_started = False
            st.session_state.current_question = None
            st.session_state.waiting_for_response = False
            st.session_state.transcribed_text = None
            st.session_state.show_transcription = False
            st.rerun()


# Page configuration
st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
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
if 'transcribed_text' not in st.session_state:
    st.session_state.transcribed_text = None
if 'show_transcription' not in st.session_state:
    st.session_state.show_transcription = False
if 'audio_file_path' not in st.session_state:
    st.session_state.audio_file_path = None

# Main title
st.title("🎯 AI Interview Assistant")
st.markdown(f"Upload your CV and start an interactive interview session!")

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
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_file_path = tmp_file.name

            try:
                with st.spinner("Processing your CV..."):
                    if file_extension == '.pdf':
                        user_cv_text = asyncio.run(extract_text_from_pdf(temp_file_path))
                    elif file_extension == '.docx':
                        user_cv_text = asyncio.run(extract_text_from_docx(temp_file_path))
                    elif file_extension == '.txt':
                        user_cv_text = asyncio.run(extract_text_from_txt(temp_file_path))

                os.unlink(temp_file_path)
                st.session_state.user_cv_text = user_cv_text
                st.success("✅ CV processed successfully!")

                with st.expander("Preview CV Text"):
                    preview_text = user_cv_text[:500] + "..." if len(user_cv_text) > 500 else user_cv_text
                    st.text_area("Extracted Text", value=preview_text, height=200, disabled=True)

            except Exception as e:
                st.error(f"❌ Error processing CV: {str(e)}")
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
        st.success("🎙️ Interview in progress...")

        # Generate new question
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
            st.subheader("🗣️ AI Interviewer:")

            # Styled question container
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                border-radius: 15px;
                color: white;
                margin: 15px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            ">
                <h4 style="margin: 0 0 10px 0; color: #ffffff;">❓ Interview Question:</h4>
                <p style="margin: 0; font-size: 16px; line-height: 1.5;">{st.session_state.current_question}</p>
            </div>
            """, unsafe_allow_html=True)

            # Generate TTS audio
            if not st.session_state.audio_file_path:
                try:
                    with st.spinner("🔊 Generating audio..."):
                        temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                        temp_audio_file.close()

                        result = TTS(text=st.session_state.current_question, filename=temp_audio_file.name)
                        if result and os.path.exists(temp_audio_file.name):
                            st.session_state.audio_file_path = temp_audio_file.name
                except Exception as e:
                    st.info("💡 Audio generation not available.")

            # Play audio if available
            if st.session_state.audio_file_path and os.path.exists(st.session_state.audio_file_path):
                try:
                    with open(st.session_state.audio_file_path, 'rb') as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/wav")
                except Exception as e:
                    pass

        # Response interface
        if st.session_state.waiting_for_response:
            st.subheader("💭 Your Response")
            st.markdown("**Choose your response method:**")

            tab1, tab2 = st.tabs(["🔴 Voice Recording", "📝 Text Input"])

            with tab1:
                st.info("🎤 Click the microphone button below to record your response")

                # Streamlit's built-in audio recorder (works everywhere!)
                audio_value = st.audio_input(
                    "Record your response:",
                    key=f"audio_input_{len(st.session_state.chat_history)}"
                )

                if audio_value is not None:
                    # Save the audio file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                        tmp_file.write(audio_value.getvalue())
                        temp_audio_path = tmp_file.name

                    with st.spinner("🔄 Transcribing your response..."):
                        try:
                            # Transcribe the audio
                            user_response_text = STT(audio_file_path=temp_audio_path)
                            os.unlink(temp_audio_path)  # Clean up temp file

                            if user_response_text and user_response_text.strip():
                                st.success("✅ Audio transcribed successfully!")

                                # Show transcribed text for editing
                                edited_response = st.text_area(
                                    "Review and edit your transcribed response:",
                                    value=user_response_text.strip(),
                                    height=100,
                                    key=f"edit_response_{len(st.session_state.chat_history)}"
                                )

                                col_submit, col_rerecord = st.columns(2)
                                with col_submit:
                                    if st.button("✅ Submit Audio Response", type="primary", use_container_width=True):
                                        if edited_response.strip():
                                            st.session_state.chat_history.append({
                                                "AI": st.session_state.current_question,
                                                "User": edited_response.strip()
                                            })
                                            # Reset states
                                            st.session_state.current_question = None
                                            st.session_state.waiting_for_response = False
                                            st.success("✅ Response submitted!")
                                            time.sleep(1)
                                            st.rerun()

                                with col_rerecord:
                                    if st.button("🎤 Record Again", use_container_width=True):
                                        # Clear the audio input by rerunning
                                        st.rerun()
                            else:
                                st.error("❌ No speech detected in the recording. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error transcribing audio: {str(e)}")
                            try:
                                os.unlink(temp_audio_path)
                            except:
                                pass

            with tab2:
                # Text input (always available)
                _render_text_input()

with col2:
    st.header("📊 Interview Progress")

    if st.session_state.chat_history:
        total_questions = len(st.session_state.chat_history)
        skipped = sum(1 for ex in st.session_state.chat_history if ex['User'] == "[Skipped question]")
        answered = total_questions - skipped

        col_ans, col_total = st.columns(2)
        with col_ans:
            st.metric("✅ Answered", answered)
        with col_total:
            st.metric("📋 Total", total_questions)

        with st.expander("📜 Chat History", expanded=False):
            for i, exchange in enumerate(st.session_state.chat_history, 1):
                if exchange['User'] == "[Skipped question]":
                    st.markdown(f"**Q{i}:** {exchange['AI'][:80]}...")
                    st.markdown("*⏭️ Skipped*")
                else:
                    st.markdown(f"**Q{i}:** {exchange['AI'][:80]}...")
                    st.markdown(f"**A{i}:** {exchange['User'][:80]}...")
                st.divider()
    else:
        st.info("📝 Upload CV and start interview!")

# Footer
st.markdown("---")
st.markdown("🚀 **AI Interview Assistant** | Your smart interview prep partner")