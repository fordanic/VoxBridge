# VoxBridge

This project provides a solution for providing real-time speech translation using Docker-based Python services. The project includes services for speech-to-text (STT), translation, text-to-speech (TTS), and streaming. An admin interface is also provided for managing the services.

## Building and Running VoxBridge

### Prerequisites
- Docker and Docker Compose installed
- Git (optional, for cloning the repository)

### Setup Instructions

1. Clone or download the VoxBridge repository:
   git clone <repository-url>
   cd voxbridge

2. Build and start all services:
   docker-compose up --build

3. For running in detached mode:
   docker-compose up -d

4. To view logs of a specific service:
   docker-compose logs -f <service-name>
   (where <service-name> can be admin, stt, translation, tts, or streaming)

5. To stop all services:
   docker-compose down

### Individual Service Access
- Admin interface: http://localhost:8080
- STT service: http://localhost:8081
- Translation service: http://localhost:8082
- TTS service: http://localhost:8083
- Streaming service: http://localhost:8084

### Running Single Service
To run just one service (e.g., the STT service):
   docker-compose up -d stt

### Running Without Docker
If you want to run the application without Docker:
1. Create a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

2. Install dependencies:
   pip install -r requirements.txt

3. Run the main application:
   python main.py
