# Cfact - Real-Time Debate Fact Checker 🎯

Cfact is an AI-powered tool designed to supervise and fact-check statements made during political debates between two people in real-time. Never miss another misleading claim!

## What It Does

Have you ever watched a political debate and wondered "Is that actually true?" Cfact listens to live debates, identifies who's speaking, transcribes their statements, and instantly fact-checks them using advanced AI models. The results are displayed in a clean, color-coded interface so you can see which claims are accurate, which are false, and which need more investigation.

## Features

- **Real-time audio recording** and processing
- **Speaker identification** - distinguishes between two debate participants
- **Automatic transcription** using Groq's Whisper API
- **AI-powered fact checking** using Llama and Mixtral models
- **Live web dashboard** with color-coded results:
  - 🔴 Red: False/Incorrect statements
  - 🟢 Green: Verified accurate statements  
  - ⚪ Gray: Statements that couldn't be verified
- **Double-check feature** - click any fact to verify it against Wikipedia using MultiOn
- **Reset functionality** to clear results between debates

## Prerequisites

Before you get started, you'll need API keys for:

- **Groq API** (for speech transcription)
- **Hugging Face** (for speaker diarization models)  
- **MultiOn API** (for Wikipedia fact verification)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Alex44lel/Cfact.git
   cd Cfact
   ```

2. **Set up the Python backend**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   HUGGING_FACE_TOKEN=your_hugging_face_token_here
   MULTION_API_KEY=your_multion_api_key_here
   ```

4. **Set up the React frontend**
   ```bash
   cd front/my-app
   npm install
   ```

## Usage

### Starting the Application

1. **Launch the backend server**
   ```bash
   python main.py
   ```
   This starts the Flask API server on `http://localhost:5000` and begins listening for audio input.

2. **Start the frontend** (in a new terminal)
   ```bash
   cd front/my-app
   npm start
   ```
   This opens the web interface at `http://localhost:3000`

### During a Debate

1. Make sure your microphone is working and positioned to capture both speakers
2. The system automatically records 30-second audio chunks
3. Watch the web interface as facts appear in real-time
4. Click on any fact to get a detailed Wikipedia-based verification
5. Use the "Reset" button to clear results between different debates

## How It Works

### Architecture

```
Audio Input → Recording → Transcription → Speaker ID → Fact Check → Web Display
     ↓            ↓           ↓            ↓            ↓           ↓
  PyAudio    30s chunks   Groq/Whisper  Pyannote.ai  Llama/Mixtral  React UI
```

### Technical Details

- **Audio Processing**: Records in 30-second chunks at 16kHz sample rate
- **Speaker Diarization**: Uses PyAnnote.audio models to identify up to 2 speakers
- **Transcription**: Groq's Whisper-large-v3 model for accurate speech-to-text
- **Fact Checking**: Two-stage process:
  1. Extract factual claims using Llama3-70B
  2. Verify accuracy using Mixtral-8x7B
- **Frontend**: React with Tailwind CSS for responsive design

## API Endpoints

- `GET /api/fact-check` - Retrieves latest fact-check results
- `POST /api/multion` - Double-checks facts against Wikipedia

## File Structure

```
Cfact/
├── main.py              # Main application and Flask server
├── utils.py             # Speaker diarization utilities
├── requirements.txt     # Python dependencies
├── front/my-app/        # React frontend application
│   ├── src/
│   │   ├── App.js       # Main React component
│   │   └── components/
│   │       └── FactCheckUI.js  # Fact checking interface
│   └── package.json     # Node.js dependencies
└── README.md            # This file
```

## Limitations

- Currently supports only 2 speakers maximum
- Requires good audio quality for accurate transcription
- Fact-checking accuracy depends on AI model capabilities
- Real-time processing requires decent computing resources (GPU recommended)

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements. This project is still in development and welcomes contributions!

## Troubleshooting

**Audio not recording?**
- Check your microphone permissions
- Ensure PyAudio is properly installed for your system

**Transcription not working?**
- Verify your Groq API key is correctly set
- Check your internet connection

**Speaker identification issues?**
- Make sure speakers are clearly audible
- Try repositioning the microphone

**Frontend not connecting?**
- Ensure the backend is running on port 5000
- Check that CORS is properly configured

## License

This project is open source. Please check the license file for details.

---

*Built with ❤️ for transparent political discourse*