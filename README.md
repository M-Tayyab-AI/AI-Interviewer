# 🎯 AI Interview Assistant

An intelligent interview practice platform that conducts personalized interview sessions based on your CV/resume using advanced AI technology.

## ✨ Features

- **📄 Smart CV Analysis** - Upload PDF, DOCX, or TXT files for personalized questions
- **🔴 Voice Recording** - Record your responses with automatic speech-to-text transcription
- **🗣️ AI Text-to-Speech** - Listen to interview questions with natural voice synthesis
- **💬 Interactive Chat** - Type responses directly or edit transcribed audio
- **📊 Progress Tracking** - Monitor your interview progress and review chat history
- **🎯 Personalized Questions** - AI generates relevant questions based on your background

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **LLM**: Google Gemini 2.5 Flash
- **Speech-to-Text**: Deepgram API
- **Text-to-Speech**: Deepgram API  
- **Document Processing**: PyMuPDF (PDF), docx2txt (DOCX)
- **Audio Processing**: SoundDevice, SciPy

## 📋 Prerequisites

- Python 3.8+
- Deepgram API Key ([Get one here](https://deepgram.com/))
- Google Gemini API Key ([Get one here](https://ai.google.dev/))

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI-Interviewer.git
   cd AI-Interviewer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   DEEPGRAM_API_KEY=your_deepgram_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

##  Usage

1. **Start the application**
   ```bash
   streamlit run streamlit_app.py
   ```

2. **Upload your CV**
   - Use the sidebar to upload your resume (PDF, DOCX, or TXT)
   - Preview the extracted text to ensure it's correct

3. **Start interview**
   - Click "🚀 Start Interview" to begin
   - AI will generate the first question based on your CV

4. **Respond to questions**
   - **Voice**: Click "🔴 Start Recording" → speak → "⏹️ Stop Recording" → review & edit transcription → submit
   - **Text**: Type directly in the text area and click "📝 Submit Text Response"

5. **Continue the conversation**
   - AI generates follow-up questions based on your responses
   - Track your progress in the sidebar

6. **End interview**
   - Click "🔚 End Interview" when finished

## 📁 Project Structure

```
AI-Interviewer/
├── streamlit_app.py          # Main Streamlit application
├── functions.py              # Core functionality (STT, TTS, AI generation)
├── prompts.py               # AI prompt templates
├── constants.py             # All constants variables
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## 🔧 Configuration

### Audio Settings
- **Max Recording Time**: 90 seconds per response (for now)
- **Audio Format**: WAV, 44.1kHz, mono
- **Auto-stop**: Recording stops automatically at max duration

### AI Settings
- **Model**: Gemini 2.5 Flash
- **Temperature**: 0.2 (for consistent responses)
- **STT Model**: Deepgram Nova-3
- **TTS Voice**: Aura Luna (English)

## 📝 Requirements.txt

```txt
streamlit>=1.28.0
google-generativeai>=0.3.0
deepgram-sdk>=3.0.0
sounddevice>=0.4.6
scipy>=1.11.0
numpy>=1.24.0
PyMuPDF>=1.23.0
docx2txt>=0.8
python-dotenv>=1.0.0
httpx>=0.25.0
```

## 🎯 How It Works

1. **CV Processing**: Extracts text from uploaded documents using format-specific parsers
2. **AI Question Generation**: Uses Gemini AI to create personalized interview questions based on CV content and conversation history
3. **Voice Input**: Records audio using system microphone and converts to text via Deepgram STT
4. **Voice Output**: Converts AI questions to speech using Deepgram TTS
5. **Conversation Flow**: Maintains context through chat history for relevant follow-up questions

## 🔍 Troubleshooting

### Common Issues

- **"No audio detected"**: Check microphone permissions and speak clearly
- **API errors**: Verify your API keys are correct and have sufficient credits
- **Recording doesn't start**: Check microphone permissions in browser/system

### Performance Tips

- Keep CV files under 10MB for faster processing
- Use a quiet environment for better speech recognition
- Speak clearly and at moderate pace for best transcription results

## 🤝 Contributing

1. Clone the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Deepgram](https://deepgram.com/) for speech-to-text and text-to-speech APIs
- [Google AI](https://ai.google.dev/) for Gemini language model
- [Streamlit](https://streamlit.io/) for the amazing web framework

## 📞 Support

If you encounter any issues or have questions:
1. Check the [Issues](https://github.com/yourusername/AI-Interviewer/issues) page
2. Create a new issue with detailed description
3. Join our [Discussions](https://github.com/yourusername/AI-Interviewer/discussions) for community support

---

⭐ **Star this repository if you found it helpful!**