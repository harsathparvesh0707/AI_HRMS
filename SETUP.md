# AI HRMS Setup Guide

## Prerequisites

### System Requirements
- **Operating System**: Linux/macOS/Windows
- **Python**: 3.8 or higher
- **Node.js**: 20.x or higher (for frontend)
- **PostgreSQL**: 12.x or higher
- **RAM**: Minimum 8GB (16GB recommended)
- **Storage**: 10GB free space

### Required Software

#### 1. PostgreSQL Database
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS (using Homebrew)
brew install postgresql
brew services start postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

#### 2. Ollama (LLM Runtime)
```bash
# Linux/macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download/windows
#serve ollama
ollama serve

#open antehr terminal and pull the model
ollama pull qwen2:7b


```

#### 3. Python Dependencies
```bash
pip install -r requirements.txt
```

## Installation Steps

### 1. Clone Repository
```bash
git clone <repository-url>
cd AI_HRMS
```

### 2. Database Setup

#### Create Database
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE DATABASE hrms_vector_db;
CREATE USER postgres WITH PASSWORD 'vvdn';
GRANT ALL PRIVILEGES ON DATABASE hrms_vector_db TO postgres;
\q
```

#### Initialize Schema
```bash
cd AIHRMS/hrms_ai
python3 -c "from database_new import init_database; init_database()"
```

### 3. Environment Configuration

#### Create .env file
```bash
cd AIHRMS/hrms_ai
cp .env.example .env
```

#### Configure .env
```env
DATABASE_URL=postgresql://postgres:vvdn@localhost:5432/hrms_vector_db
VECTOR_PERSIST_DIR=./chroma_db
OLLAMA_MODEL=qwen2:7b
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### 4. Install Python Dependencies
```bash
cd AI_HRMS
pip install -r requirements.txt
```

#### Core Dependencies
- **FastAPI**: Web framework and API
- **ChromaDB**: Vector database for semantic search
- **Sentence Transformers**: Embedding generation
- **Gemini AI**: Advanced query understanding
- **Scikit-learn**: ML ranking model
- **Redis**: High-performance caching
- **PostgreSQL**: Structured data storage

### 5. Setup Ollama Models
```bash
# Pull required model
ollama pull qwen2:7b

# Verify installation
ollama list
```

### 6. Initialize Vector Database
```bash
# Create ChromaDB directory
mkdir -p chroma_db

# The vector database will be initialized automatically on first data upload
```

## Running the Application

### 1. Start Backend Server
```bash
cd AIHRMS/hrms_ai
python3 main_new.py
```

The server will start on `http://localhost:8000`

### 2. Verify Installation
```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status": "healthy", "message": "HRMS AI Backend is running"}
```

### 3. Upload Sample Data (Fully Automated)
```bash
# Upload HRMS data - everything happens automatically!
curl -X POST "http://localhost:8000/api/v1/upload/hrms-data" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_data.csv" \
  -F "description=Sample HRMS data"

# System automatically:
# ✅ Processes data
# ✅ Builds performance cache (10x faster)
# ✅ Learns skill relationships
# ✅ Learns query patterns
# ✅ Trains ML ranking model
# ✅ Ready for intelligent search!
```

### 4. Check Intelligence Status
```bash
# Check ML model status
curl http://localhost:8000/api/v1/ml-stats

# Check cache performance
curl http://localhost:8000/api/v1/cache-stats
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /stats` - System statistics
- `POST /search` - Employee search with NLP intelligence
- `POST /query` - Advanced employee query with ML ranking
- `POST /upload/hrms-data` - Upload data (auto-learns patterns)
- `POST /init-database` - Initialize database tables

### Intelligence Endpoints
- `POST /index-employees` - Index for semantic search
- `POST /precompute-embeddings` - Build performance cache
- `GET /cache-stats` - Cache performance metrics
- `GET /ml-stats` - ML model statistics
- `DELETE /clear-cache` - Clear performance cache

### Example Usage

#### Intelligent Search (NLP + ML)
```bash
# Natural language search with learned intelligence
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python developers with 5+ years in Bangalore who are available"}'

# System automatically understands:
# - Skills: Python
# - Experience: 5+ years
# - Location: Bangalore  
# - Status: Available/Free
# - Uses ML ranking for best results
```

#### Advanced Query with ML Ranking
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Senior React developers for frontend team",
    "max_results": 10
  }'

# Features:
# ✅ Context-aware skill matching
# ✅ ML-learned ranking preferences
# ✅ Business-aware scoring
# ✅ 10x faster with caching
```

## Data Format

### Employee CSV Format
```csv
employee_id,display_name,designation,employee_department,emp_location,deployment,skill_set,total_exp,pm,rm_name,tech_group,sub_department,vvdn_exp
VVDN/12345,John Doe,Sr Engineer (Software),Cloud and Mobile Apps,Bangalore,Free,"Java,Spring Boot,React",5Y 2M,Manager Name,RM Name,Backend,Cloud,3Y 1M
```

### Required Columns
- `employee_id`: Unique identifier
- `display_name`: Employee full name
- `designation`: Job title
- `employee_department`: Department name
- `emp_location`: Work location
- `deployment`: Status (Free, Billable, Budgeted, etc.)
- `skill_set`: Comma-separated skills
- `total_exp`: Experience (format: XY YM)

## Troubleshooting

### Common Issues

#### 1. Database Connection Error
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart if needed
sudo systemctl restart postgresql
```

#### 2. Ollama Model Not Found
```bash
# Pull the model
ollama pull qwen2:7b

# Check available models
ollama list
```

#### 3. Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

#### 4. ChromaDB Permission Issues
```bash
# Fix permissions
chmod -R 755 chroma_db/
```

### Logs and Debugging
```bash
# View application logs
tail -f server.log

# Enable debug mode
export DEBUG=true
python3 main_new.py
```

## Performance Features

### Automated Performance Optimization
- **10x Faster Search**: Auto-cached embeddings
- **ML Ranking**: Learned preferences vs hardcoded rules
- **Smart Caching**: Redis-based with semantic matching
- **Batch Processing**: Efficient bulk operations

### Performance Metrics
```bash
# Check current performance
curl http://localhost:8000/api/v1/cache-stats

# Expected improvements:
# Simple queries: 300ms → 50ms (6x faster)
# Complex queries: 500ms → 100ms (5x faster) 
# Cached queries: 300ms → 10ms (30x faster)
```

### Database Optimization
```sql
-- Recommended indexes (auto-created)
CREATE INDEX idx_employees_deployment ON employees(deployment);
CREATE INDEX idx_employees_skills ON employees USING gin(to_tsvector('english', skill_set));
```

## Security Considerations

### Database Security
- Use strong passwords
- Enable SSL connections
- Restrict database access

### API Security
- Implement authentication (not included in basic setup)
- Use HTTPS in production
- Rate limiting recommended

## Production Deployment

### Using Docker (Optional)
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main_new.py"]
```

### Environment Variables
```bash
export DATABASE_URL=postgresql://user:pass@host:5432/db
export OLLAMA_BASE_URL=http://ollama-server:11434
export DEBUG=false
```

## Support

For issues and questions:
1. Check logs in `server.log`
2. Verify all prerequisites are installed
3. Ensure database is running and accessible
4. Check Ollama service status

## Version Information
- **Backend**: FastAPI 0.104.1
- **Database**: PostgreSQL 12+
- **Vector DB**: ChromaDB 0.4.18
- **LLM**: Ollama with qwen2:7b
- **Python**: 3.8+