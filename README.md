# 📚 StoryBook Creator

A powerful AI-driven web application that generates personalized children's storybooks with consistent illustrations, narration, and PDF export capabilities.

## ✨ Features

- **🤖 AI Story Generation**: create engaging stories using advanced LLMs (Gemini, Llama) via OpenRouter.
- **🎨 Consistent Illustrations**: Generates beautiful, consistent character artwork using Freepik AI.
- **🗣️ Audio Narration**: Converts stories to audio using gTTS (Google Text-to-Speech).
- **📄 PDF Export**: detailed PDF generation with images and professionally formatted text.
- **🔐 User Authentication**: Secure signup and login system using MongoDB and JWT.
- **📱 Modern Frontend**: Responsive React-based dashboard with Tailwind CSS.
- **💾 History & Management**: Save and manage your generated stories.

## 🛠️ Tech Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: MongoDB (Atlas)
- **Authentication**: JWT (JSON Web Tokens)
- **AI Integration**: OpenRouter API, Freepik API
- **Utilities**: ReportLab (PDF), gTTS (Audio), Pillow (Image processing)

### Frontend
- **Framework**: React (Vite)
- **Styling**: Tailwind CSS, Lucide React (Icons)
- **State/Routing**: React Router DOM, Axios

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js & npm
- MongoDB Atlas Account (or local MongoDB)
- API Keys for OpenRouter and Freepik

### 1. Backend Setup

1.  **Clone the repository** and navigate to the root directory.
2.  **Create a virtual environment** (optional but recommended):
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**:
    Create a `.env` file in the root directory with the following credentials:
    ```env
    MONGO_URI=your_mongodb_connection_string
    JWT_SECRET_KEY=your_jwt_secret_key
    OPENROUTER_API_KEY=your_openrouter_api_key
    FREEPIK_API_KEY=your_freepik_api_key
    SECRET_KEY=your_flask_secret_key
    ```
5.  **Run the Backend**:
    ```bash
    python app.py
    ```
    The backend will start on `http://127.0.0.1:5000`.

### 2. Frontend Setup

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```
2.  **Install dependencies**:
    ```bash
    npm install
    ```
3.  **Run the Development Server**:
    ```bash
    npm run dev
    ```
    The frontend will typically start on `http://localhost:5173`.

## 🏗️ Project Structure

```
Story-Book/
├── app.py                 # Main Flask Application & API Routes
├── requirements.txt       # Python Dependencies
├── uploads/               # Directory for generated assets (images, audio, PDFs)
└── frontend/             # React Frontend Application
    ├── src/
    │   ├── components/    # Reusable React Components
    │   ├── pages/         # Page Components (Home, Dashboard, etc.)
    │   ├── App.jsx        # Main App Component
    │   └── main.jsx       # Entry Point
    ├── package.json       # Node Dependencies
    └── vite.config.js     # Vite Configuration
```

## 🔌 API Endpoints

- **Auth**:
    - `POST /api/auth/signup`: Register a new user.
    - `POST /api/auth/login`: Authenticate user.
    - `GET /api/auth/me`: Get current user profile.
- **Story**:
    - `POST /api/generate`: Generate a new story (text, images, audio).
    - `GET /api/story/<story_id>`: Retrieve specific story data.
- **Downloads**:
    - `GET /api/download-pdf/<story_id>`: Download story as PDF.
    - `GET /api/download-audiobook/<story_id>`: Download narration as ZIP.

## 📝 Configuration

- **Story Lengths**: Configurable in `app.py` (short, normal, long, extended).
- **Models**:
    - Text: `google/gemini-2.0-flash-exp:free` (Default), with fallbacks to Llama/Mistral.
    - Image: Freepik API (Primary).

 