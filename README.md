# Receipt Lens 🧾🔍

Self-hosted web system for analyzing grocery receipts using Claude AI. Upload photos of your receipts, extract structured data, and gain insights into your shopping habits.

## 📋 Features

- **AI-Powered Analysis**: Uses Anthropic's Claude Sonnet 4 to extract detailed information from receipt images
- **Automatic Categorization**: Products are automatically categorized (beverages, meat, vegetables, dairy, bakery, cleaning, leisure, others)
- **Historical Tracking**: Store and search through all your receipts
- **Smart Analytics**:
  - Monthly spending summaries by category
  - Store price comparisons
  - Product price evolution tracking
  - Personalized savings recommendations
- **Multi-format Support**: JPG, PNG, and PDF receipts
- **Secure Authentication**: JWT-based user authentication
- **Duplicate Detection**: Prevents uploading the same receipt twice
- **Self-hosted**: Complete control over your data

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **AI**: Anthropic Claude API (Sonnet 4)
- **Authentication**: JWT with bcrypt

### Frontend
- **Stack**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js for data visualization
- **Design**: Responsive CSS Grid/Flexbox

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **Testing**: pytest with 70% minimum coverage

## 📁 Project Structure

```
receipt-lens/
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # Container image definition
├── .env.example               # Environment variables template
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Test configuration
├── backend/
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Application settings
│   ├── dependencies.py       # Dependency injection
│   ├── auth/                 # Authentication module
│   ├── receipts/             # Receipt processing module
│   ├── analytics/            # Analytics module
│   └── database/             # Database configuration and schema
├── frontend/
│   ├── static/               # CSS, JS, images
│   └── templates/            # HTML templates
├── tests/                    # Test suite
└── uploads/                  # Uploaded receipt images
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Anthropic API Key ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/receipt-lens.git
   cd receipt-lens
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**

   Edit `.env` and set the following required variables:

   ```bash
   # REQUIRED: Set a strong password for PostgreSQL
   POSTGRES_PASSWORD=your_strong_password_here

   # REQUIRED: Add your Anthropic API key
   ANTHROPIC_API_KEY=sk-ant-...

   # REQUIRED: Generate a secret key for JWT
   # Run: openssl rand -hex 32
   JWT_SECRET_KEY=your_generated_secret_key_here
   ```

4. **Start the application**
   ```bash
   docker-compose up -d
   ```

5. **Verify installation**

   Open your browser and navigate to:
   - Application: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/api/health

### First Time Setup

The database will be automatically initialized with:
- Schema creation (users, receipts, categories, items)
- Pre-populated product categories
- Indexes for performance optimization

## 📖 Usage

### Basic Workflow

1. **Register/Login**: Create an account or log in
2. **Upload Receipt**: Drag and drop or select a receipt image
3. **AI Processing**: Claude analyzes the receipt and extracts data
4. **View Dashboard**: See your spending analytics and insights
5. **Compare Stores**: Identify which stores offer better prices

### API Endpoints

#### Authentication
```http
POST /api/auth/register    # Create new user account
POST /api/auth/login       # Login and get JWT token
GET  /api/auth/me          # Get current user info
```

#### Receipts
```http
POST   /api/receipts/upload     # Upload new receipt
GET    /api/receipts            # List all receipts (paginated)
GET    /api/receipts/{id}       # Get receipt details
DELETE /api/receipts/{id}       # Delete receipt
```

#### Analytics
```http
GET /api/analytics/monthly-summary       # Monthly spending breakdown
GET /api/analytics/store-comparison      # Compare stores by price
GET /api/analytics/price-evolution       # Track product prices over time
```

For detailed API documentation, visit `/api/docs` when running in development mode.

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Browser   │─────▶│   FastAPI    │─────▶│ PostgreSQL  │
│  (Frontend) │      │   Backend    │      │  Database   │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Claude API  │
                     │  (Analysis)  │
                     └──────────────┘
```

### Data Flow

1. User uploads receipt image via frontend
2. Backend validates file (size, format, duplicates)
3. Image sent to Claude API with specialized prompt
4. Claude extracts structured data (products, prices, categories)
5. Data stored in PostgreSQL with transaction safety
6. Analytics queries aggregate data for insights

## 🧪 Testing

### Run all tests
```bash
docker-compose exec backend pytest
```

### Run specific test categories
```bash
# Authentication tests
pytest -m auth

# Receipt processing tests
pytest -m receipts

# Analytics tests
pytest -m analytics

# Integration tests
pytest -m integration
```

### Check code coverage
```bash
pytest --cov=backend --cov-report=html
# Open htmlcov/index.html in browser
```

## 🔒 Security Features

- **Password Hashing**: bcrypt with automatic salt generation
- **JWT Tokens**: 24-hour expiration by default
- **Input Validation**: Pydantic schemas for all requests
- **Rate Limiting**: Max 10 uploads per hour per user
- **File Validation**: Size limits, extension whitelist, hash-based duplicate detection
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **CORS**: Configurable allowed origins

## ⚙️ Configuration

All settings are managed via environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_PASSWORD` | PostgreSQL password | (required) |
| `ANTHROPIC_API_KEY` | Claude API key | (required) |
| `JWT_SECRET_KEY` | JWT signing key | (required) |
| `JWT_EXPIRATION_HOURS` | Token lifetime | 24 |
| `MAX_UPLOAD_SIZE_MB` | Max file size | 10 |
| `UPLOAD_RATE_LIMIT_PER_HOUR` | Upload limit | 10 |
| `ENVIRONMENT` | dev/production | development |
| `DEBUG` | Enable debug mode | true |
| `LOG_LEVEL` | Logging verbosity | INFO |

## 🗺️ Roadmap

### Phase 1 (MVP) ✅
- [x] Docker setup with PostgreSQL
- [x] Health check endpoint
- [ ] User authentication (JWT)
- [ ] Receipt upload and Claude integration
- [ ] Basic frontend (login, upload, list)

### Phase 2 (Analytics)
- [ ] Monthly spending analytics
- [ ] Store comparison
- [ ] Price evolution tracking
- [ ] Interactive dashboard with charts

### Phase 3 (Refinement)
- [ ] Advanced error handling
- [ ] Rate limiting implementation
- [ ] Email notifications
- [ ] Export data (CSV, PDF reports)
- [ ] Mobile-responsive improvements

### Future Features
- [ ] OCR fallback for receipts without Claude
- [ ] Receipt tagging system
- [ ] Budget alerts and goals
- [ ] Multi-user household support
- [ ] Shopping list recommendations
- [ ] API for third-party integrations

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run pre-commit checks
black backend/ --check
ruff check backend/

# Run tests with coverage
pytest --cov=backend
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Anthropic](https://www.anthropic.com/) for the Claude API
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent web framework
- [PostgreSQL](https://www.postgresql.org/) for reliable data storage
- [Chart.js](https://www.chartjs.org/) for beautiful visualizations

## 📧 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation at `/api/docs`
- Review the troubleshooting section below

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Claude API Errors
- Verify your API key is correct in `.env`
- Check API quota at https://console.anthropic.com/
- Review logs: `docker-compose logs backend`

### Upload Failures
- Ensure file is < 10MB
- Supported formats: JPG, PNG, PDF
- Check uploads directory permissions

---

**Made with ❤️ for smarter shopping**
