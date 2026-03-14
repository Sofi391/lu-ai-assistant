# 🤖 LU AI Chat Assistant

[![Python](https://img.shields.io/badge/Python-3.x-blue)](https://www.python.org/)  
[![Django](https://img.shields.io/badge/Django-5.x-green)](https://www.djangoproject.com/)  
[![Django REST Framework](https://img.shields.io/badge/DRF-REST--API-red)](https://www.django-rest-framework.org/)  
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue)](https://www.postgresql.org/)  
[![Pytest](https://img.shields.io/badge/Testing-Pytest-green)](https://pytest.org/)  
[![Swagger](https://img.shields.io/badge/API-Docs-brightgreen)](#)

> 📸 **Visual Preview** — See the full UI and API screenshots in the [Screenshots Gallery](SCREENSHOTS.md)

A production-ready AI conversational backend built with Django REST Framework, implementing a complete **Retrieval-Augmented Generation (RAG)** pipeline powered by pgvector and Gemini AI. The system supports contextual chat through document retrieval, maintains conversation history, streams real-time responses, and includes features such as rate limiting, modular architecture, comprehensive pytest coverage, and production-grade security settings making it a scalable foundation for building intelligent, knowledge-aware chat applications.

All endpoints can be explored and tested at: `/api/docs/` or `/api/redoc/`

---

## 🚀 Key Highlights

- Built a **Retrieval-Augmented Generation (RAG)** AI assistant using **pgvector**
- Implemented **streaming AI responses** with Gemini 2.5 Flash Lite
- Designed a **service-oriented Django architecture**
- Achieved **full API test coverage using pytest**
- Implemented **production-grade security** (rate limiting, JWT, SSL)

---

## ✨ Project Overview

LU AI Chat Assistant is designed to simulate a real-world conversational AI system with enterprise-grade architecture.

It handles:

- **Advanced RAG Implementation**: pgvector-powered document retrieval with cosine similarity
- **Real-time AI Streaming**: Gemini 2.5 Flash Lite integration with fallback mechanisms  
- **Session Management**: Persistent conversation history with configurable memory window (10 messages)
- **Comprehensive Testing**: Full pytest suite covering all functionalities
- **Production Security**: SSL/TLS, HSTS, secure cookies, and content security policies
- **Modular Architecture**: Separate settings, services, and prompts organization
- **Rate Limiting & Monitoring**: Intelligent throttling with comprehensive logging

The goal was to build a scalable, intelligent chat system that reflects enterprise-grade AI application architecture with proper testing, security, and maintainability practices.

---

## 🛠 Core Features

### 🔐 Authentication & Security
- **JWT Authentication**: Secure token-based authentication with configurable lifetimes
- **Rate Limiting**: Intelligent throttling (10/min chat, 5/min ingest) with custom error messages
- **GDPR Compliance**: Email masking in logs for privacy protection
- **Production Security**: SSL redirect, HSTS headers, secure cookies, content type protection
- **Admin-Only Ingestion**: Document ingestion restricted to admin users
- **Input Validation**: Comprehensive validation with 2000 character limits

---

### 🧠 Advanced RAG System
- **pgvector Integration**: PostgreSQL vector database with L2 distance similarity search
- **Gemini 2.5 Flash Lite**: Lightning-fast AI responses with streaming capabilities
- **Smart Context Retrieval**: Top-k document retrieval with follow-up query enhancement
- **Memory Window**: Configurable conversation context (10 messages) for coherent responses
- **Fallback Mechanisms**: Automatic fallback from streaming to standard responses
- **Prompt Engineering**: Structured system and RAG prompts for consistent AI behavior

---

### 📚 Knowledge Management & Document Processing
- **Text Chunking**: RecursiveCharacterTextSplitter with 600-character chunks and 60-character overlap
- **Embedding Generation**: Gemini embedding model for document vectorization
- **Bulk Operations**: Efficient bulk creation of knowledge base entries
- **Metadata Support**: JSON metadata storage for enhanced document organization
- **Follow-up Detection**: Intelligent detection of follow-up questions for context enhancement

> Note: Complete RAG pipeline with pgvector database integration and Gemini AI processing.

---

### 🧪 Comprehensive Testing Suite
- **pytest Framework**: Full test coverage with fixtures and parametrized tests
- **Test Categories**: Authentication, chat functionality, rate limiting, session management, ingestion
- **Mock Services**: RAG service mocking for isolated testing
- **Database Testing**: Django database fixtures with proper test isolation
- **API Testing**: Complete API endpoint testing with various scenarios
- **Configuration**: Dedicated test settings and pytest.ini configuration

---

### 📊 Production-Ready Monitoring
- **Structured Logging**: Separate app.log and errors.log with custom formatters
- **Performance Tracking**: Request/response timing and chunk counting
- **Error Handling**: Comprehensive exception handling with specific error codes
- **User Activity**: Detailed user action logging with privacy compliance
- **Service Monitoring**: RAG service, LLM service, and database operation tracking

---

### 🏗️ Modular Architecture
The project follows a modular service-based structure:

- **Settings Management**: Separate base, development, and production configurations
- **Service Layer**: Dedicated RAG and LLM services with proper separation of concerns
- **Prompt Management**: External prompt files for easy AI behavior modification
- **Test Organization**: Comprehensive test suite with fixtures and utilities
- **Frontend Separation**: Modern vanilla JavaScript with glass morphism design

---

### 📄 Interactive API Documentation
- **drf-spectacular Integration**: Auto-generated OpenAPI 3.0 documentation
- **Custom Serializers**: Detailed request/response schemas for all endpoints
- **Interactive Testing**: Swagger UI with built-in API testing capabilities
- **Response Examples**: Comprehensive error response documentation

Access via: `/api/docs/` or `/api/redoc/`

---

## ⚙️ Tech Stack

### Backend Architecture
- **Framework**: Django 5.x with Django REST Framework
- **Database**: PostgreSQL with pgvector extension for vector operations
- **AI Integration**: Google Gemini 2.5 Flash Lite with embedding models
- **Authentication**: JWT with django-rest-framework-simplejwt
- **Documentation**: drf-spectacular with Swagger UI sidecar
- **Testing**: pytest with Django integration and comprehensive fixtures

### Frontend Stack
- **Core**: Vanilla JavaScript (ES6+) with modern async/await patterns
- **Styling**: CSS3 with custom properties, glass morphism design
- **Architecture**: Modular JS with separate auth, chat, and admin modules
- **UI/UX**: Responsive design with chat widget, streaming responses, and real-time updates

### Database & Vector Operations
- **Primary DB**: PostgreSQL with advanced indexing
- **Vector Storage**: pgvector extension for embedding storage and similarity search
- **ORM**: Django ORM with custom vector field operations
- **Migrations**: Proper database schema management

### AI & Machine Learning
- **RAG Implementation**: Custom retrieval-augmented generation pipeline
- **Vector Search**: pgvector L2 distance for document similarity
- **Text Processing**: LangChain text splitters for optimal chunking
- **AI Models**: Gemini embedding (3072 dimensions) and Gemini 2.5 Flash Lite
- **Streaming**: Real-time response streaming with chunk management

### Security & Production
- **SSL/TLS**: Full HTTPS enforcement with HSTS headers
- **Session Security**: Secure cookies with proper domain configuration
- **Content Security**: X-Frame-Options, content type protection
- **Rate Limiting**: Scoped throttling with custom error responses
- **Environment Management**: Secure environment variable handling

---

## 🚀 Setup & Installation

### 🔧 Environment Setup

1️⃣ **Clone the repository**
```bash
git clone <repository-url>
cd ChatBot
```

2️⃣ **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3️⃣ **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your specific configuration values including:
# - GOOGLE_API_KEY for Gemini AI
# - Database credentials for PostgreSQL with pgvector
# - JWT secret keys and lifetimes
```

4️⃣ **Database Setup**
```bash
# Ensure PostgreSQL with pgvector extension is installed
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5️⃣ **Run Tests**
```bash
pytest  # Runs the complete test suite
pytest chat/tests/test_chat.py -v  # Run specific test file
```

6️⃣ **Run Backend Server**
```bash
python manage.py runserver
```

### 🌐 Access Points
- **Frontend Interface**: Open `frontend/index.html` in your browser
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs/ or http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/
- **Admin Dashboard**: `frontend/admin.html`

---

## 🧱 Project Architecture

### Backend Structure
```
backend/
├── lu_backend/
│   ├── settings/          # Decentralized settings management
│   │   ├── base.py       # Common settings
│   │   ├── development.py # Development configuration
│   │   └── production.py  # Production security settings
│   └── urls.py           # URL routing
├── chat/
│   ├── services/         # Service layer architecture
│   │   ├── rag_service.py    # RAG implementation
│   │   └── llm_service.py    # LLM integration
│   ├── prompts/          # External prompt management
│   │   ├── system_prompt.txt # AI system behavior
│   │   └── rag_prompt.txt    # RAG-specific prompts
│   ├── tests/            # Comprehensive test suite
│   │   ├── conftest.py       # Test fixtures
│   │   ├── test_chat.py      # Chat functionality tests
│   │   ├── test_chat_ratelimit.py # Rate limiting tests
│   │   └── test_*.py         # Additional test modules
│   ├── models.py         # Database models with vector fields
│   ├── views.py          # API endpoints with documentation
│   └── serializers.py    # API serialization
└── logs/                 # Structured logging output
```

### Frontend Structure
```
frontend/
├── js/
│   ├── chat.js          # Chat functionality with streaming
│   ├── auth.js          # Authentication handling
│   └── admin.js         # Admin interface
├── css/
│   └── style.css        # Modern CSS with glass morphism
├── index.html           # Landing page with chat widget
├── login.html           # Authentication interface
└── admin.html           # Admin dashboard
```

This architecture promotes:
- **Separation of Concerns**: Clear boundaries between services, views, and business logic
- **Testability**: Isolated components with comprehensive test coverage
- **Maintainability**: Modular structure with external configuration
- **Scalability**: Service-oriented design for easy extension

---

## 🛡 Production Security Features

### SSL/TLS Configuration
```python
# Production settings include:
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Session & Cookie Security
```python
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

### Database Security
- SSL-required database connections in production
- Connection pooling with conn_max_age for performance
- Proper database URL configuration with environment variables

---

## 🧪 Testing Architecture

### Test Coverage
- **Authentication Tests**: User registration, JWT token generation
- **Chat Functionality**: Streaming responses, session management, memory window
- **Rate Limiting**: Throttling behavior and custom error messages
- **Ingestion Tests**: Document processing and admin-only access
- **Session Tests**: Session creation, retrieval, and message history

### Test Configuration
```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = lu_backend.settings.development
testpaths = chat/tests
python_files = tests.py test_*.py *_tests.py
```

### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest chat/tests/test_chat_ratelimit.py
pytest chat/tests/test_session.py

# Run with coverage
pytest --cov=chat
```

---

## 🎯 Learning Outcomes

- **Advanced RAG Implementation**: Building production-ready retrieval systems with pgvector
- **AI Integration**: Implementing streaming AI responses with proper error handling
- **Testing Best Practices**: Comprehensive pytest suite with fixtures and mocking
- **Security Implementation**: Production-grade security configurations and practices
- **Architecture Design**: Service-oriented backend architecture
- **Performance Optimization**: Efficient vector operations and database queries
- **API Documentation**: Professional API documentation with interactive testing
- **Frontend Integration**: Modern JavaScript with real-time streaming capabilities

---

## 👨‍💻 About the Developer

Hi! I'm **Sofi (Sofoniyas)** — a **Backend Developer** and **Software Engineering student at AASTU**, and a **graduate of the ALX Backend Engineering Program**.

I specialize in building **secure, scalable, and production-ready backend systems** using modern backend technologies. I enjoy translating real-world business requirements into clean, maintainable, and efficient backend solutions.

I'm particularly interested in:

- **Backend System Architecture**: Designing scalable, maintainable backend systems
- **AI Integration**: Building production-ready AI-powered applications with RAG
- **Testing & Quality Assurance**: Comprehensive testing strategies and best practices
- **Security Implementation**: Authentication, authorization, and production security
- **Database Design**: Advanced database operations including vector databases
- **API Development**: RESTful API design with proper documentation and testing

This project showcases my growth in backend development and my ability to solve complex problems with clean, maintainable code while integrating cutting-edge AI technologies and following industry best practices.

---

### 🤝 Connect with Me

<p align="center">
  <a href="https://linkedin.com/in/sofoniyas-alebachew-bb876b33b">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" />
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/Sofi391">
    <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub" />
  </a>
</p>

---

*Built with ❤️ using Django REST Framework, PostgreSQL + pgvector, Gemini AI, and comprehensive testing practices*