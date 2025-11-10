# LegalEagle Project - Knowledge Transfer Documentation

## 🚀 Project Overview

**LegalEagle** is an AI-powered legal Q&A chatbot platform built with FastAPI, MySQL, and Qdrant vector database. It allows users to upload legal documents and ask questions about them using advanced AI models.

### Key Features
- 📄 Document upload and processing (PDF support)
- 🤖 AI-powered chat interface with document context
- 👥 User management with role-based access
- 💳 Subscription plans and payment integration (Stripe)
- 📊 Admin dashboard with analytics
- 🔍 Vector search using Qdrant
- 🔒 Secure authentication system

---

## 🏗️ System Architecture

### Tech Stack
- **Backend**: FastAPI (Python)
- **Database**: MySQL (User data, plans, transactions)
- **Vector DB**: Qdrant Cloud (Document embeddings)
- **AI Models**: OpenAI GPT-3.5-turbo, text-embedding-ada-002
- **Frontend**: Jinja2 templates, Bootstrap 5, jQuery
- **Payments**: Stripe integration
- **File Processing**: PyMuPDF for PDF processing

### Project Structure
```
LegalEagle/
├── main.py                 # FastAPI app entry point
├── database.py            # Database setup and table creation
├── db_operations.py       # Database operations (CRUD)
├── template_config.py     # Jinja2 template configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── routes/               # FastAPI route modules
│   ├── admin_*.py        # Admin panel routes
│   ├── auth.py           # Authentication routes
│   ├── chat.py           # Chat functionality
│   ├── pages.py          # Public pages
│   ├── payments.py       # Payment processing
│   └── upload_simple.py  # Document upload
├── services/             # Business logic services
│   ├── pdf_utils.py      # PDF processing utilities
│   ├── rag.py            # RAG (Retrieval Augmented Generation)
│   └── vector_store.py   # Qdrant vector operations
├── templates/            # HTML templates
├── static/              # CSS, JS, images
└── utils/               # Utility functions
```

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- MySQL Server
- Qdrant Cloud account (or local Qdrant)
- OpenAI API key
- Stripe account (for payments)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd LegalEagle
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create `.env` file (copy from `.env.example`):

```env
# MySQL Database Configuration
DB_HOST=localhost
DB_NAME=legaleagle
DB_USER=root
DB_PASSWORD=your_mysql_password

# Qdrant Cloud connection
QDRANT_URL=https://your-qdrant-cluster-url:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=docs

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Embedding and LLM model config
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-3.5-turbo

# Stripe Configuration
STRIPE_PUBLIC_KEY=pk_test_your_stripe_public_key
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
```

### Step 5: Database Setup
```bash
# Create MySQL database
mysql -u root -p
CREATE DATABASE legaleagle;
exit

# Run database setup
python database.py
```

### Step 6: Run Application
```bash
python main.py
```

The application will be available at: `http://127.0.0.1:8005`

---

## 🔧 Configuration Details

### Database Schema
The application uses MySQL with the following main tables:
- `users` - User accounts and profiles
- `subscription_plans` - Available subscription plans
- `user_plans` - User's active plans
- `transactions` - Payment transactions
- `chat_history` - User chat sessions
- `contact_us` - Contact form submissions
- `general_settings` - Application settings
- `user_ai_settings` - User-specific AI configurations

### Default Admin Account
- **Email**: `admin@legaleagle.com`
- **Password**: `password` (hash: `5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8`)

### API Endpoints Structure
```
/ - Public homepage
/admin/* - Admin panel routes
/auth/* - Authentication (login/signup)
/chat - AI chat interface
/upload - Document upload
/payments/* - Stripe payment processing
```

---

## 🚀 Deployment Guide

### Production Environment Setup

1. **Server Requirements**:
   - Ubuntu 20.04+ or similar
   - Python 3.8+
   - MySQL 8.0+
   - Nginx (reverse proxy)
   - SSL certificate

2. **Environment Variables**:
   - Update `.env` with production values
   - Use strong database passwords
   - Use production Stripe keys
   - Set proper CORS origins

3. **Database Migration**:
   ```bash
   # Backup existing data if upgrading
   mysqldump -u root -p legaleagle > backup.sql
   
   # Run migrations
   python database.py
   ```

4. **Process Management**:
   ```bash
   # Using Gunicorn
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   
   # Or using systemd service
   sudo systemctl start legaleagle
   sudo systemctl enable legaleagle
   ```

5. **Nginx Configuration**:
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /static/ {
           alias /path/to/legaleagle/static/;
       }
   }
   ```

---

## 🔍 Key Components Deep Dive

### 1. Document Processing Pipeline
```python
# File: services/pdf_utils.py
1. PDF upload → 2. Text extraction → 3. Chunking → 4. Embedding generation → 5. Qdrant storage
```

### 2. Chat System Flow
```python
# File: services/rag.py
1. User query → 2. Query embedding → 3. Vector search → 4. Context retrieval → 5. GPT response
```

### 3. User Management
```python
# File: db_operations.py
- User CRUD operations
- Authentication & session management
- Role-based access control (user/admin)
```

### 4. Payment Integration
```python
# File: routes/payments.py
- Stripe checkout sessions
- Webhook handling
- Subscription management
```

### 5. Admin Dashboard Features
- User management
- Plan management
- Transaction monitoring
- Chat history analytics
- System settings
- Contact form management

---

## 🧪 Testing

### Unit Tests
```bash
# Run specific tests
python test_api_direct.py
python test_chat_api.py
python test_vector_db.py
python test_user_separation.py
```

### Integration Tests
```bash
# Test complete chat flow
python test_chat_api_direct.py

# Test MySQL collection integration
python test_mysql_collection_integration.py
```

### Manual Testing Checklist
- [ ] User registration/login
- [ ] Document upload
- [ ] Chat functionality
- [ ] Payment flow
- [ ] Admin panel operations
- [ ] Mobile responsiveness

---

## 🔧 Maintenance & Troubleshooting

### Common Issues

1. **Database Connection Issues**:
   ```bash
   # Check MySQL service
   sudo systemctl status mysql
   
   # Test connection
   python -c "from database import get_db_connection; print(get_db_connection())"
   ```

2. **Qdrant Connection Issues**:
   ```bash
   # Verify Qdrant credentials in .env
   # Check collection exists
   python test_vector_db.py
   ```

3. **File Upload Issues**:
   - Check `static/uploads/` directory permissions
   - Verify max file size settings
   - Check disk space

4. **Payment Issues**:
   - Verify Stripe webhook endpoints
   - Check webhook signatures
   - Monitor Stripe dashboard

### Database Migration Scripts
Located in project root:
- `migrate_*.py` - Various database migrations
- `setup_test_data.py` - Test data generation
- `verify_dashboard.py` - Dashboard verification

### Monitoring & Logs
```bash
# Application logs
tail -f logs/app.log

# MySQL logs
tail -f /var/log/mysql/error.log

# Nginx logs
tail -f /var/log/nginx/access.log
```

---

## 📚 Additional Resources

### Important Files to Review
1. `db_operations.py` - Core database operations
2. `services/rag.py` - AI chat logic
3. `routes/admin_main.py` - Admin functionality
4. `template_config.py` - Template helpers
5. Migration summary files (`*_SUMMARY.md`)

### External Dependencies
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Qdrant Documentation**: https://qdrant.tech/documentation/
- **OpenAI API Documentation**: https://platform.openai.com/docs
- **Stripe Documentation**: https://stripe.com/docs

### Development Best Practices
1. Always backup database before migrations
2. Test payment flows in Stripe test mode
3. Monitor API rate limits (OpenAI, Qdrant)
4. Use environment variables for secrets
5. Implement proper error handling
6. Add logging for debugging

---

## 🤝 Handover Checklist

### For New Developer
- [ ] Environment setup completed
- [ ] Database connection verified
- [ ] All external API keys configured
- [ ] Application runs successfully
- [ ] Admin panel accessible
- [ ] Test user account created
- [ ] Sample document uploaded and chat tested
- [ ] Payment flow tested (test mode)

### Knowledge Transfer Items
- [ ] Codebase walkthrough completed
- [ ] Database schema explained
- [ ] API integration points reviewed
- [ ] Deployment process demonstrated
- [ ] Troubleshooting guide reviewed
- [ ] Access to external services provided

### Future Enhancements
- Multi-language support
- Advanced document types (Word, Excel)
- Real-time notifications
- API rate limiting
- Enhanced analytics dashboard
- Mobile app development
- Advanced AI model integration

---

## 📞 Support & Contact

For technical questions or issues:
- Review this documentation first
- Check existing migration summary files
- Test with sample data before production changes
- Always backup before major changes

**Good luck with the project! 🚀**