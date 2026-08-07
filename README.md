# Nordpet

**[View the Full NordPet Case Study & Project Presentation](https://pratesdev.com/nordpet)**

A modern, robust Veterinary Clinic Management System powered by autonomous AI.

Nordpet is a comprehensive, production-ready web application designed to streamline veterinary clinic operations. Beyond traditional patient and appointment management, it acts as a digital medical assistant. The system leverages a multi-agent AI architecture (powered by LangChain, LanceDB, and OpenAI) to automate complex clinical workflows: transcribing voice consultations, parsing PDF lab results via OCR, searching the FDA for medication safety, and performing intelligent medical triage. Built with Django, Docker, and Tailwind CSS, Nordpet is engineered for scalability, robust background processing, and a premium user experience.

## Key Features

- **FDA API Integration:** Automated tool to query the official FDA veterinary database for medication adverse events, providing vets with real-time pharmacological safety data.
- **Patient & Client Management:** Keep detailed records of pet owners and their pets.
- **Appointment Scheduling:** Track and manage clinic schedules effectively.
- **AI Triage & Agents:** Intelligent agents powered by LangChain and OpenAI to provide deep medical insights, reasoning, and smart chat assistance for veterinary professionals.
- **Voice-to-Text Consultations:** Integrated with OpenAI Whisper API to automatically transcribe audio recordings of veterinary consultations.
- **Vector Search & RAG:** Built-in semantic search and memory retention utilizing LanceDB as a high-performance vector database.
- **Background Processing:** Asynchronous task queue via Django-Q2 for heavy computations and background tasks.
- **Responsive UI:** A modern, beautiful, and mobile-friendly interface crafted with Tailwind CSS.


## Specialized AI Agents

Nordpet utilizes a multi-agent architecture built with LangChain and LanceDB to handle specific veterinary tasks autonomously:

- **TriageAgent:** Analyzes incoming patient vital signs (heart rate, temperature, weight) and symptoms to automatically assign a standardized clinical risk level (Green, Yellow, Orange, Red).
- **SummaryAgent:** Processes raw, unstructured audio transcriptions of veterinary consultations and distills them into concise, structured medical summaries for the patient's record.
- **ExamAnalysisAgent:** Parses OCR text from PDF laboratory results (bloodwork, etc.) to automatically extract abnormal parameters, issue critical life-threatening warnings, and suggest diagnostic hypotheses.
- **AssistantAgent:** A conversational medical assistant equipped with RAG (Retrieval-Augmented Generation via LanceDB) to query historical clinic knowledge, and armed with tools to search the official FDA database for real-time medication adverse events.

## Tech Stack

### Backend
- **Framework:** Django (Python 3.12)
- **Database:** PostgreSQL
- **Task Queue:** Django-Q2
- **Data Validation:** Pydantic for strict LLM structured outputs and schema validation
- **AI Orchestration & Vector DB:** LangChain and LanceDB
- **Generative AI Models:** OpenAI GPT (Text & Reasoning) and Whisper (Speech-to-Text)
- **Document Processing:** Docling and RapidOCR for PDF exam extraction

### Frontend
- **Styling:** Tailwind CSS
- **Structure:** Django Templates

### Infrastructure & Deployment
- **Containerization:** Docker and Docker Compose
- **Web Server (Production):** Gunicorn
- **Static Files:** WhiteNoise

## Project Structure

```text
nordpet-public/
├── core/                  # Main Django configuration & settings
├── clients/               # App handling pets, owners, and appointments
├── users/                 # Custom user models, dashboard & authentication
├── static/                # Static assets (CSS, JS, Images)
├── templates/             # Global HTML templates
├── .env.example           # Environment variables template
├── docker-compose.yml     # Docker services orchestration (Web, Worker, DB)
├── Dockerfile             # Multi-stage Dockerfile for production
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies for Tailwind CSS
└── start.sh               # Local development startup script
```

## Getting Started

### Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose
- [Node.js](https://nodejs.org/) (for local Tailwind CSS compilation)
- [Python 3.12+](https://www.python.org/)

### 1. Environment Setup

Clone the repository and set up your environment variables:

```bash
git clone https://github.com/your-username/nordpet-public.git
cd nordpet-public
cp .env.example .env
```
*Edit the `.env` file and insert your actual keys, such as `OPENAI_API_KEY` and database credentials.*

### 2. Local Development (Programming Mode)

If you want to edit the code with hot-reloading for CSS and Python:

1. Start the PostgreSQL database:
   ```bash
   docker compose up db -d
   ```
2. Install dependencies (Python & Node):
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   npm install
   ```
3. Run migrations and start the development server:
   ```bash
   python manage.py migrate
   npm run dev
   ```
   *Note: `npm run dev` executes `start.sh`, running both the Django server and Tailwind compiler simultaneously.*

4. In a separate terminal, start the background task worker:
   ```bash
   source venv/bin/activate
   python manage.py qcluster
   ```

### 3. Production Deployment (Dockerized)

To run the application exactly as it would run on a cloud server:

```bash
docker compose up --build -d
```
This command will:
1. Compile Tailwind CSS in a Node.js stage.
2. Build a lightweight Python image with Gunicorn and WhiteNoise.
3. Spin up the Database (`db`), the Web Server (`web`), and the Background Worker (`worker`).

Access the application at: `http://localhost:8000`
