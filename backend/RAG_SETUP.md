# RAG Integration Setup Guide

This document explains how to set up the enhanced RAG (Retrieval-Augmented Generation) capabilities with LangChain and Pinecone.

## 🚀 Features Added

### ✅ Enhanced Document Processing
- **LangChain Integration**: Intelligent document chunking with configurable sizes and overlap
- **Multiple File Types**: PDF, DOCX, TXT, and Markdown support
- **Smart Chunking**: Recursive character text splitting with proper separators
- **Metadata Preservation**: Document and chunk metadata stored with vectors

### ✅ Vector Database (Pinecone)
- **Pinecone Integration**: Scalable vector storage and similarity search
- **Auto-Index Creation**: Automatically creates Pinecone index if it doesn't exist
- **OpenAI Embeddings**: Uses `text-embedding-ada-002` for high-quality embeddings
- **Metadata Filtering**: Store document metadata for filtering and retrieval

### ✅ Enhanced Chat Service
- **Vector Search**: Query documents using semantic similarity
- **Context-Aware Responses**: Responses include relevant document chunks
- **Smart Citations**: Automatic citation of source documents
- **Fallback Handling**: Graceful degradation when services are unavailable

## 🔧 Setup Instructions

### 1. Install Dependencies

The required packages are already added to `requirements.txt`:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Get API Keys

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

#### Pinecone API Key
1. Visit [Pinecone Console](https://app.pinecone.io/)
2. Create a free account
3. Create a new project
4. Go to "API Keys" section
5. Copy your API key and environment name

### 3. Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Database
DATABASE_URL=sqlite:///./helpdesk.db

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# File Storage
UPLOAD_DIR=storage/uploads

# AI/RAG Services (Required for full RAG functionality)
OPENAI_API_KEY=sk-your-openai-api-key-here
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=helpdesk-documents

# LangChain Settings (Optional - defaults provided)
EMBEDDING_MODEL=text-embedding-ada-002
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 4. Verify Setup

1. **Start the backend**:
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Check logs** for initialization messages:
   - ✅ "OpenAI embeddings initialized successfully"
   - ✅ "Pinecone vector store initialized successfully"

3. **Upload a test document** through the admin interface
4. **Check processing logs** for:
   - ✅ "Successfully processed document X: Y chunks, Z vectors stored"

## 🧪 Testing the RAG System

### 1. Upload Documents
- Login as admin (`admin@ex.com` / `Admin123!`)
- Go to Documents page
- Upload PDF, DOCX, TXT, or MD files
- Check that status shows "parsed"

### 2. Test Chat with Vector Search
- Start a new chat conversation
- Ask questions related to your uploaded documents
- Look for responses that include:
  - Relevant document chunks
  - Source citations
  - Enhanced context

### 3. Search API (Admin Only)
Test the search endpoint directly:
```bash
curl -X GET "http://localhost:8000/api/docs/search/your-query-here" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔧 Configuration Options

### Chunking Settings
- `CHUNK_SIZE`: Maximum characters per chunk (default: 1000)
- `CHUNK_OVERLAP`: Overlap between chunks (default: 200)
- Larger chunks = more context, fewer pieces
- Smaller chunks = more precise matching, more pieces

### Pinecone Settings
- `PINECONE_INDEX_NAME`: Name of your Pinecone index
- `PINECONE_ENVIRONMENT`: Your Pinecone environment (e.g., "gcp-starter")
- The system automatically creates the index with:
  - Dimension: 1536 (OpenAI ada-002)
  - Metric: cosine similarity
  - Serverless configuration

### Embedding Model
- `EMBEDDING_MODEL`: OpenAI model for embeddings
- Default: `text-embedding-ada-002`
- Alternative: `text-embedding-3-small` (newer, smaller)

## 🚨 Troubleshooting

### Common Issues

1. **"OpenAI embeddings not initialized"**
   - Check your `OPENAI_API_KEY` in `.env`
   - Verify the API key is valid and has credits

2. **"Pinecone initialization failed"**
   - Check `PINECONE_API_KEY` and `PINECONE_ENVIRONMENT`
   - Ensure you have a Pinecone account and project

3. **"No relevant documents found"**
   - Make sure documents are successfully processed (status="parsed")
   - Try more specific or different search terms
   - Check that embeddings are being generated

4. **Processing fails with "Failed to extract text"**
   - Verify file format is supported (PDF, DOCX, TXT, MD)
   - Check file is not corrupted
   - Ensure sufficient disk space

### Graceful Degradation

The system is designed to work even without API keys:
- **Without OpenAI key**: Text extraction and storage still work, no embeddings
- **Without Pinecone key**: Documents are processed and stored in DB, no vector search
- **Search fallback**: Returns empty results instead of crashing

## 🎯 Next Steps for Full LLM Integration

The current implementation provides:
- ✅ Document chunking and embedding
- ✅ Vector similarity search
- ✅ Context retrieval for chat

For full LLM integration, add:
1. **LangChain LLM**: Add OpenAI ChatGPT or other LLM
2. **RAG Chain**: Create retrieval-augmented generation pipeline
3. **Streaming**: Implement streaming responses
4. **Memory**: Add conversation memory and context
5. **Advanced Prompting**: Custom prompts for IT support scenarios

## 📊 Monitoring and Analytics

Monitor your RAG system:
- **Document Processing**: Check logs for successful chunk/vector creation
- **Search Performance**: Monitor search latency and relevance
- **API Usage**: Track OpenAI API usage and costs
- **Pinecone Usage**: Monitor vector operations and storage

The enhanced system is now ready for production use with proper API keys configured!
