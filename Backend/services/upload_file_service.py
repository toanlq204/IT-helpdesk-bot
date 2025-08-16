import chromadb
from openai import OpenAI
import os
import json
import hashlib
import re
from datetime import datetime
from pinecone import ServerlessSpec, Pinecone
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains.combine_documents import create_stuff_documents_chain


class UploadFileService:
    def __init__(self):
        self.openai_api_key = os.getenv("AZOPENAI_EMBEDDING_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.openai_client_emb = OpenAI(
            api_key=os.getenv("AZOPENAI_EMBEDDING_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
        self.openai_client_chat = OpenAI(
            api_key=os.getenv("AZOPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = "helpdesk-kb"

        # Get embedding model and determine dimensions
        self.embedding_model = os.getenv(
            "AZOPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
        )

        # Set dimension based on the embedding model
        if "text-embedding-3-small" in self.embedding_model:
            self.embedding_dimension = 1536
        elif "text-embedding-3-large" in self.embedding_model:
            self.embedding_dimension = 3072
        elif "text-embedding-ada-002" in self.embedding_model:
            self.embedding_dimension = 1536
        else:
            # Default to text-embedding-3-small dimension
            self.embedding_dimension = 1536
        #self.pinecone_client.delete_index(self.index_name)
        if not self.pinecone_client.has_index(self.index_name):
            self.pinecone_client.create_index(
                name=self.index_name,
                dimension=self.embedding_dimension,
                metric="cosine",
                spec=ServerlessSpec(region="us-east-1", cloud="aws"),
            )

    def embed_text(self, text: str):
        # Use OpenAI's embedding endpoint
        response = self.openai_client_emb.embeddings.create(
            input=text, model=self.embedding_model
        )
        return response.data[0].embedding

    def generate_content_metadata(
        self, file_content: str, file_name: str, chunk_size: int = 2000
    ):
        """
        Generate metadata based on file content using OpenAI with chunking for large files
        """
        try:
            # Split content into chunks
            chunks = self._split_content_into_chunks(file_content, chunk_size)

            # Analyze each chunk
            chunk_metadata_list = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = self._analyze_chunk(chunk, i + 1, len(chunks))
                if chunk_metadata:
                    chunk_metadata_list.append(chunk_metadata)

            # Merge all chunk metadata into final result
            # merged_metadata = self._merge_chunk_metadata(chunk_metadata_list, file_name, file_content)

            return {"chunk": chunks, "metadata": chunk_metadata_list}

        except Exception as e:
            # Fallback to basic metadata if AI analysis fails
            return {
                "file_name": file_name,
                "file_size": len(file_content),
                "content_hash": hashlib.md5(file_content.encode()).hexdigest(),
                "upload_timestamp": datetime.now().isoformat(),
                "word_count": len(file_content.split()),
                "character_count": len(file_content),
                "error": f"AI metadata generation failed: {str(e)}",
            }

    def _split_content_into_chunks(self, content: str, chunk_size: int = 2000):
        """
        Split content into overlapping chunks to preserve context
        """
        if len(content) <= chunk_size:
            return [content]

        chunks = []
        overlap = chunk_size // 4  # 25% overlap to preserve context

        start = 0
        while start < len(content):
            end = start + chunk_size

            # Try to break at sentence boundaries
            if end < len(content):
                # Look for sentence endings within the last 200 characters
                sentence_break = content.rfind(".", end - 200, end)
                if sentence_break != -1 and sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1

            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = max(start + chunk_size - overlap, end)

            if start >= len(content):
                break

        return chunks

    def _analyze_chunk(self, chunk: str, chunk_num: int, total_chunks: int):
        """
        Analyze a single chunk and return metadata
        """
        try:
            prompt = f"""
            Analyze chunk {chunk_num} of {total_chunks} from a document and provide metadata in JSON format. Do not include markdown, code fences, or any text before/after the JSON:
            
            Chunk content: {chunk}
            
            Please provide the following metadata for this chunk:
            {{
                "chunk_summary": "Brief summary of this chunk's content",
                "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
                "topics": ["topic1", "topic2", "topic3"],
                "content_type": "documentation/faq/guide/policy/troubleshooting/code/other",
                "topic_category": "IT/HR/Finance/Security/Network/Hardware/Software/General",
                "difficulty_level": "beginner/intermediate/advanced",
                "key_concepts": ["concept1", "concept2", "concept3"],
                "action_items": ["action1", "action2"] or null if none,
                "technical_terms": ["term1", "term2", "term3"] or null if none
            }}
            
            Return only valid JSON. If chunk is too short or irrelevant, return null values for optional fields.
            """

            response = self.openai_client_chat.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"Error analyzing chunk {chunk_num}: {str(e)}")
            return None

        pattern = r"^```json\s*(.*?)\s*```$"
        cleaned_string = re.sub(pattern, r"\1", json_string, flags=re.DOTALL)
        return cleaned_string.strip()

    def store_file_content(
        self,
        file_content: str,
        file_name: str,
        metadata: dict = None,
        use_ai_metadata: bool = True,
    ):
        try:
            raw_docs = [
                Document(
                    page_content=file_content,
                    metadata={"file_name": file_name},
                )
            ]
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
            docs = splitter.split_documents(raw_docs)
            index = self.pinecone_client.Index(self.index_name)
            embeddings = OpenAIEmbeddings(
                api_key=os.getenv("AZOPENAI_EMBEDDING_API_KEY"),
                base_url=os.getenv("OPENAI_BASE_URL"),
                model=self.embedding_model)
            vector_store = PineconeVectorStore(
                index=index, 
                embedding=embeddings
            )
            vector_store.add_documents(docs)
            return {
                "status": "success",
                "file_name": file_name,
            }
        except Exception as e:
            print(f"Error storing file content: {str(e)}")
            return {"status": "error", "message": str(e)}


# Note: Ensure your virtual environment is activated before running code that uses chromadb.
