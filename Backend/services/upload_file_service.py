import chromadb
from openai import OpenAI
import os
import json
import hashlib
import re
from datetime import datetime

class UploadFileService:
    def __init__(self, chroma_path: str = "storage/chroma_db", collection_name: str = "files"):
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(collection_name)
        self.openai_api_key = os.getenv("AZOPENAI_EMBEDDING_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.openai_client_emb = OpenAI(api_key=self.openai_api_key)
        self.openai_client_chat = OpenAI(api_key=os.getenv("AZOPENAI_API_KEY"))

    def embed_text(self, text: str):
        # Use OpenAI's embedding endpoint
        response = self.openai_client_emb.embeddings.create(
            input=text,
            model=os.getenv("AZOPENAI_EMBEDDING_MODEL")
        )
        return response.data[0].embedding

    def generate_content_metadata(self, file_content: str, file_name: str, chunk_size: int = 2000):
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
            merged_metadata = self._merge_chunk_metadata(chunk_metadata_list, file_name, file_content)
            
            return merged_metadata
            
        except Exception as e:
            # Fallback to basic metadata if AI analysis fails
            return {
                "file_name": file_name,
                "file_size": len(file_content),
                "content_hash": hashlib.md5(file_content.encode()).hexdigest(),
                "upload_timestamp": datetime.now().isoformat(),
                "word_count": len(file_content.split()),
                "character_count": len(file_content),
                "error": f"AI metadata generation failed: {str(e)}"
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
                sentence_break = content.rfind('.', end - 200, end)
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
                temperature=0.1
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error analyzing chunk {chunk_num}: {str(e)}")
            return None

    def _merge_chunk_metadata(self, chunk_metadata_list: list, file_name: str, file_content: str):
        """
        Merge metadata from all chunks into final comprehensive metadata
        """
        if not chunk_metadata_list:
            return self.extract_basic_metadata(file_content, file_name)
        
        # Collect all data from chunks
        all_keywords = []
        all_topics = []
        all_summaries = []
        all_key_concepts = []
        all_action_items = []
        all_technical_terms = []
        content_types = []
        topic_categories = []
        difficulty_levels = []
        
        for chunk_meta in chunk_metadata_list:
            if chunk_meta:
                all_keywords.extend(chunk_meta.get("keywords", []))
                all_topics.extend(chunk_meta.get("topics", []))
                all_summaries.append(chunk_meta.get("chunk_summary", ""))
                all_key_concepts.extend(chunk_meta.get("key_concepts", []))
                
                if chunk_meta.get("action_items"):
                    all_action_items.extend(chunk_meta.get("action_items", []))
                if chunk_meta.get("technical_terms"):
                    all_technical_terms.extend(chunk_meta.get("technical_terms", []))
                
                content_types.append(chunk_meta.get("content_type", ""))
                topic_categories.append(chunk_meta.get("topic_category", ""))
                difficulty_levels.append(chunk_meta.get("difficulty_level", ""))
        
        # Deduplicate and rank by frequency
        def get_top_items(items_list, max_count=10):
            if not items_list:
                return []
            
            # Count frequency
            item_counts = {}
            for item in items_list:
                if item and item.strip():
                    clean_item = item.strip().lower()
                    item_counts[clean_item] = item_counts.get(clean_item, 0) + 1
            
            # Sort by frequency and return top items
            sorted_items = sorted(item_counts.items(), key=lambda x: x[1], reverse=True)
            return [item for item, count in sorted_items[:max_count]]
        
        def get_most_common(items_list):
            if not items_list:
                return "unknown"
            
            item_counts = {}
            for item in items_list:
                if item and item.strip():
                    item_counts[item] = item_counts.get(item, 0) + 1
            
            if not item_counts:
                return "unknown"
            
            return max(item_counts.items(), key=lambda x: x[1])[0]
        
        # Generate overall summary
        overall_summary = self._generate_overall_summary(all_summaries, file_content)
        
        # Calculate estimated read time
        word_count = len(file_content.split())
        estimated_read_time = f"{max(1, word_count // 200)} minutes"
        
        # Build final metadata - Convert lists to strings for ChromaDB compatibility
        keywords_list = get_top_items(all_keywords, 15)
        topics_list = get_top_items(all_topics, 10)
        key_concepts_list = get_top_items(all_key_concepts, 10)
        action_items_list = get_top_items(all_action_items, 8) if all_action_items else []
        technical_terms_list = get_top_items(all_technical_terms, 12) if all_technical_terms else []
        
        final_metadata = {
            "file_name": file_name,
            "file_size": len(file_content),
            "content_hash": hashlib.md5(file_content.encode()).hexdigest(),
            "upload_timestamp": datetime.now().isoformat(),
            "word_count": word_count,
            "character_count": len(file_content),
            "summary": overall_summary,
            "keywords": ", ".join(keywords_list) if keywords_list else "",
            "topics": ", ".join(topics_list) if topics_list else "",
            "key_concepts": ", ".join(key_concepts_list) if key_concepts_list else "",
            "content_type": get_most_common(content_types),
            "topic_category": get_most_common(topic_categories),
            "difficulty_level": get_most_common(difficulty_levels),
            "estimated_read_time": estimated_read_time,
            "chunks_analyzed": len(chunk_metadata_list),
            "action_items": ", ".join(action_items_list) if action_items_list else "",
            "technical_terms": ", ".join(technical_terms_list) if technical_terms_list else ""
        }
        
        return final_metadata

    def _generate_overall_summary(self, chunk_summaries: list, file_content: str):
        """
        Generate an overall summary from chunk summaries
        """
        try:
            if not chunk_summaries:
                return "No summary available"
            
            # If only one chunk, return its summary
            if len(chunk_summaries) == 1:
                return chunk_summaries[0]
            
            # Combine chunk summaries and ask AI to create overall summary
            combined_summaries = "\n".join([f"Chunk {i+1}: {summary}" for i, summary in enumerate(chunk_summaries) if summary.strip()])
            
            prompt = f"""
            Based on the following chunk summaries from a document, create a comprehensive 2-3 sentence overall summary:
            
            {combined_summaries}
            
            Provide a cohesive summary that captures the main purpose and key points of the entire document.
            """
            
            response = self.openai_client_chat.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback: just combine first few chunk summaries
            return ". ".join(chunk_summaries[:3]) if chunk_summaries else "Summary generation failed"

    def extract_basic_metadata(self, file_content: str, file_name: str):
        """
        Extract basic metadata without AI (faster, no API calls)
        """
        words = file_content.split()
        
        # Simple keyword extraction (most frequent words)
        word_freq = {}
        for word in words:
            word = word.lower().strip('.,!?";()[]{}')
            if len(word) > 3:  # Ignore short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [word for word, freq in keywords]
        
        # Estimate content type based on keywords
        content_type = "unknown"
        if any(word in file_content.lower() for word in ["troubleshoot", "error", "fix", "problem"]):
            content_type = "troubleshooting"
        elif any(word in file_content.lower() for word in ["faq", "question", "answer"]):
            content_type = "faq"
        elif any(word in file_content.lower() for word in ["guide", "tutorial", "how to"]):
            content_type = "guide"
        elif any(word in file_content.lower() for word in ["policy", "procedure", "rule"]):
            content_type = "policy"
        
        return {
            "file_name": file_name,
            "file_size": len(file_content),
            "content_hash": hashlib.md5(file_content.encode()).hexdigest(),
            "upload_timestamp": datetime.now().isoformat(),
            "word_count": len(words),
            "character_count": len(file_content),
            "keywords": ", ".join(keywords) if keywords else "",
            "content_type": content_type,
            "estimated_read_time": f"{max(1, len(words) // 200)} minutes"
        }

    def clean_json_string(json_string):
        pattern = r'^```json\s*(.*?)\s*```$'
        cleaned_string = re.sub(pattern, r'\1', json_string, flags=re.DOTALL)
        return cleaned_string.strip()

    def store_file_content(self, file_content: str, file_name: str, metadata: dict = None, use_ai_metadata: bool = True):
        try:
            embedding = self.embed_text(file_content)
            
            # Generate metadata from content if not provided
            if metadata is None:
                if use_ai_metadata:
                    metadata = self.generate_content_metadata(file_content, file_name)
                else:
                    metadata = self.extract_basic_metadata(file_content, file_name)
            else:
                # If metadata is provided, still add basic info
                basic_info = {
                    "file_name": file_name,
                    "file_size": len(file_content),
                    "upload_timestamp": datetime.now().isoformat(),
                    "word_count": len(file_content.split()),
                }
                metadata = {**basic_info, **metadata}
            print(metadata)
            self.collection.add(
                documents=[file_content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[file_name]
            )
            return {"status": "success", "file_name": file_name, "metadata": metadata}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Note: Ensure your virtual environment is activated before running code that uses chromadb.
