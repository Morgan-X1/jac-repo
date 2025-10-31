sem ChatType = """ChatType enum defines the types of chat interactions. ChatType must be one of:
- RAG: For interactions that require document retrieval.
- QA: For interactions that does not require document retrieval, or image-video-related questions.
- IMAGE: For interactions involving image analysis or anything related to images, and follow up questions.
- VIDEO: For interactions involving video analysis or video-related questions.
""";

sem Router.classify = """Classify the message as one of these exact words: RAG, QA, IMAGE, VIDEO. 
- RAG: For questions about documents, files, or retrieved knowledge
- QA: For general conversation without documents
- IMAGE: For image analysis or questions about images
- VIDEO: For video analysis or questions about videos

Return ONLY one of these four words: RAG, QA, IMAGE, or VIDEO.""";

sem ImageChat.respond_with_image = """Answer the user's message(text) by referring to the provided image. Always refer to the given image, answer relevant to the given image.""";

sem VideoChat.respond_with_video = """Answer the user's message using the provided video and text. Always refer to the given video, answer relevant to the given video.""";

sem RagChat.respond = """Generate a helpful response by USING the available tools. 
DO NOT generate code - ACTUALLY CALL THE TOOLS. 
For current information, use perform_web_search or perform_duckduckgo_search with a search query.
Available tools: list_mcp_tools, use_mcp_tool, perform_web_search, perform_duckduckgo_search.
Always pass arguments as flat dictionaries.""";

sem QAChat.respond = """Generate a helpful response to the user's message.""";


impl ImageChat.chat {
    img_path = visitor.file_path;
    response = self.respond_with_image(
        img=Image(img_path),
        text=visitor.message,
        chat_history=visitor.chat_history
    );

    visitor.chat_history.append({"role": "assistant", "content": response});
    self.chat_history = visitor.chat_history;
    visitor.response = response;
    report {"response": response, "chat_history": visitor.chat_history};
}

impl VideoChat.chat {
    video_path = visitor.file_path;
    response = self.respond_with_video(
        video=Video(video_path),
        text=visitor.message,
        chat_history=visitor.chat_history
    );

    visitor.chat_history.append({"role": "assistant", "content": response});
    self.chat_history = visitor.chat_history;
    visitor.response = response;
    report {"response": response, "chat_history": visitor.chat_history};
}


impl RagChat.chat {
    response = self.respond(
        message=visitor.message,
        chat_history=visitor.chat_history,
    );
    visitor.chat_history.append({"role": "assistant", "content": response});
    self.chat_history = visitor.chat_history;
    visitor.response = response;
    report {"response": response, "chat_history": visitor.chat_history};
}

impl QAChat.chat {
    response = self.respond(
        message=visitor.message,
        chat_history=visitor.chat_history,
    );
    visitor.chat_history.append({"role": "assistant", "content": response});
    self.chat_history = visitor.chat_history;
    visitor.response = response;
    report {"response": response, "chat_history": visitor.chat_history};
}

impl upload_file.save_doc {
    upload_dir = os.path.join("uploads", self.session_id);
    if not os.path.exists(upload_dir) {
        os.makedirs(upload_dir);
    }

    file_path = os.path.join(upload_dir, self.file_name);
    data = base64.b64decode(self.file_data.encode('utf-8'));

    with open(file_path, 'wb') as f {
        f.write(data);
    }

    # Only add text-based documents to rag_engine
    lower_name = self.file_name.lower();
    if lower_name.endswith(".pdf") or lower_name.endswith(".txt") {
        rag_engine.add_file(file_path);
    }

    report {
        "status": "uploaded",
        "file_path": file_path,
        "added_to_rag": lower_name.endswith(".pdf") or lower_name.endswith(".txt")
    };
}
"""Perform web search using DuckDuckGo for current information, recent news, or general web queries."""
def perform_duckduckgo_search(query: str) -> str {
    return duckduckgo_searcher.search(query);
}

"""PERFORM ACTUAL WEB SEARCH - DO NOT GENERATE CODE. Execute this function to search the web for current information. 
Input: search query string.
Returns: actual web search results as text.
Example: perform_web_search("current vice chancellor of Kenyatta University")"""
def perform_web_search(query: str) -> str {
    return web_searcher.search(query);
}
"""Get available MCP tool names."""
def list_mcp_tools() -> list[str] {
    return mcp_client.list_mcp_tools();
}

"""Use MCP tool to perform actions.
name must be one of available tools from list_mcp_tools(), do not make up any tool names.

Example input for `use_mcp_tool`:
{"name": "tool_name", "arguments": {"query": "your query"}}
"""
def use_mcp_tool(name: str, arguments: dict[str, str]) -> str {
    return mcp_client.call_mcp_tool(name=name, arguments=arguments);
}