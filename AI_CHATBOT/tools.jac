
import os;
import requests;
import from langchain_community.document_loaders {PyPDFDirectoryLoader, PyPDFLoader}
import from langchain_text_splitters {RecursiveCharacterTextSplitter}
import from langchain.schema.document {Document}
import from langchain_google_genai {GoogleGenerativeAIEmbeddings}
import from langchain_chroma {Chroma}
import from langchain_community.retrievers {BM25Retriever}
import from langchain.retrievers {EnsembleRetriever}
import from duckduckgo_search {DDGS}

glob SERPER_API_KEY: str = os.getenv('SERPER_API_KEY', '');

obj RagEngine {
    has file_path: str = "uploads/user_session_123";
    has chroma_path: str = "chroma";
    has mode: str = "hybrid";

    def postinit {
        if not os.path.exists(self.file_path) {
            os.makedirs(self.file_path);
        }
        documents: list = self.load_documents();
        chunks: list = self.split_documents(documents);
        self.add_to_chroma(chunks);
    }

    def get_retriever(docs: list[Document]) {
    if self.mode == "dense" {
        return Chroma(
            persist_directory=self.chroma_path,
            embedding_function=self.get_embedding_function()
        ).as_retriever();
    } elif self.mode == "sparse" {
        return self.get_sparse_retriever(docs);
    } elif self.mode == "hybrid" {
        return self.get_hybrid_retriever(docs);
    } else {
        raise ValueError(f"Invalid mode '{self.mode}'. Choose from 'dense', 'sparse', or 'hybrid'.");
    }
    }
    def get_sparse_retriever(docs: list[Document]) {
    return BM25Retriever.from_documents(docs);
    } 

    def get_hybrid_retriever(docs: list[Document]) {
    dense = Chroma(
        persist_directory=self.chroma_path,
        embedding_function=self.get_embedding_function()
    ).as_retriever();

    sparse = self.get_sparse_retriever(docs);
    hybrid = EnsembleRetriever(retrievers=[dense, sparse], weights=[0.6, 0.4]);
    return hybrid;
    }

    def hybrid_search(query: str, chunk_nos: int=5) {
    docs = self.load_documents();
    retriever = self.get_hybrid_retriever(docs);
    results = retriever.get_relevant_documents(query);

    summary = "";
    for doc in results[:chunk_nos] {
        source = doc.metadata.get('source');
        page = doc.metadata.get('page');
        chunk_txt = doc.page_content[0:400] if len(doc.page_content) > 400 else doc.page_content;
        summary += f"{source} page {page}: {chunk_txt}\n";
    }
    return summary;
} 

    def load_documents {
        document_loader = PyPDFDirectoryLoader(self.file_path);
        docs = document_loader.load();
        for i in range(min(3, len(docs))) {
            doc = docs[i];
            source = doc.metadata.get('source', 'unknown');
            page = doc.metadata.get('page', 'unknown');
        }
        return docs;
    }

    def load_document(file_path: str) {
        loader = PyPDFLoader(file_path);
        return loader.load();
    }

    def add_file(file_path: str) {
        documents = self.load_document(file_path);
        chunks = self.split_documents(documents);
        self.add_to_chroma(chunks);
    }

    def split_documents(documents: list[Document]) {
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False);
        return text_splitter.split_documents(documents);
    }

    def get_embedding_function {
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001");
        return embeddings;
    }

    def add_chunk_id(chunks: str) {
        last_page_id = None;
        current_chunk_index = 0;

        for chunk in chunks {
            source = chunk.metadata.get('source');
            page = chunk.metadata.get('page');
            current_page_id = f'{source}:{page}';

            if current_page_id == last_page_id {
                current_chunk_index +=1;
            } else {
                current_chunk_index = 0;
            }

            chunk_id = f'{current_page_id}:{current_chunk_index}';
            last_page_id = current_page_id;

            chunk.metadata['id'] = chunk_id;
        }

        return chunks;
    }

    def add_to_chroma(chunks: list[Document]) {
        db = Chroma(persist_directory=self.chroma_path, embedding_function=self.get_embedding_function());
        chunks_with_ids = self.add_chunk_id(chunks);

        existing_items = db.get(include=[]);
        existing_ids = set(existing_items['ids']);

        new_chunks = [];
        for chunk in chunks_with_ids {
            if chunk.metadata['id'] not in existing_ids {
                new_chunks.append(chunk);
            }
        }

        if len(new_chunks) {
            print('adding new documents');
            new_chunk_ids = [chunk.metadata['id'] for chunk in new_chunks];
            db.add_documents(new_chunks, ids=new_chunk_ids);
        } else {
            print('no new documents to add');
        }
    }

    def get_from_chroma(query: str,chunck_nos: int=5) {
        db = Chroma(
            persist_directory=self.chroma_path,
            embedding_function=self.get_embedding_function()
        );
        results = db.similarity_search_with_score(query,k=chunck_nos);
        return results;
    }

    def search(query: str, chunck_nos: int=5) {
    docs = self.load_documents();
    retriever = self.get_retriever(docs);
    results = retriever.get_relevant_documents(query);

    summary = "";
    for doc in results[:chunck_nos] {
        source = doc.metadata.get('source');
        page = doc.metadata.get('page');
        chunk_txt = doc.page_content[0:400] if len(doc.page_content) > 400 else doc.page_content;
        summary += f"{source} page {page}: {chunk_txt}\n";
    }
    return summary;
    }
}

obj WebSearch {
    has api_key: str = SERPER_API_KEY;
    has base_url: str = "https://google.serper.dev/search";

    def search(query: str) {
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"};
        payload = {"q": query};
        resp = requests.post(self.base_url, headers=headers, json=payload);
        if resp.status_code == 200 {
            data = resp.json();
            summary = "";
            results = data.get("organic", []) if isinstance(data, dict) else [];
            for r in results[:3] {
                summary += f"{r.get('title', '')}: {r.get('link', '')}\n";
                if r.get('snippet') {
                    summary += f"{r['snippet']}\n";
                }
            }
            return summary;
        }
        return f"Serper request failed: {resp.status_code}";
    }
}
obj DuckDuckGoSearch {
    def search(query: str, max_results: int = 3) {
        api_url = "https://api.duckduckgo.com/";
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        };
        
        resp = requests.get(api_url, params=params);
        
        if resp.status_code == 200 {
            data = resp.json();
            summary = "";
            
            if data.get("AbstractText") {
                summary += f"Summary: {data.AbstractText}\n";
                if data.get("AbstractURL") {
                    summary += f"Source: {data.AbstractURL}\n\n";
                }
            }
            
            if data.get("RelatedTopics") and len(data.RelatedTopics) > 0 {
                summary += "Related information:\n";
                topics = data.RelatedTopics[:max_results];
                for topic in topics {
                    if topic.get("Text") {
                        summary += f"- {topic.Text}\n";
                    }
                }
            }
            
            if summary {
                return summary;
            } else {
                return "No information found on DuckDuckGo";
            }
        } else {
            return "Failed to access DuckDuckGo API";
        }
    }
}