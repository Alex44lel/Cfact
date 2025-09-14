# Cfact - Real-Time Debate Fact Checker 🎯

Cfact is an AI-powered tool designed to supervise and fact-check statements made during political debates between two people in real-time. 

## What It Does

Have you ever watched a political debate and wondered "Is that actually true?" Cfact listens to live debates, identifies who's speaking, transcribes their statements, and instantly fact-checks them. The results are displayed in a interface on the web so you can see which claims are accurate, which are false, and which need more investigation.

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

- **Groq API** (for speech transcription) - [Get it here](https://console.groq.com/)
- **Hugging Face** (for speaker diarization models) - [Get it here](https://huggingface.co/settings/tokens)
- **MultiOn API** (for Wikipedia fact verification) - [Get it here](https://www.multion.ai/)



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



## Limitations & Known Issues

- Currently supports only 2 speakers maximum
- Requires good audio quality for accurate transcription  
- Fact-checking accuracy depends on AI model capabilities and training data
- Real-time processing requires decent computing resources (GPU recommended for best performance)
- May struggle with heavily accented speech or overlapping conversations
- Internet connection required for all AI API calls
