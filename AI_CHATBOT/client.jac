import streamlit as st;
import requests;
import base64;
import time;

def bootstrap_frontend(token: str) {
    st.set_page_config(page_title="MorganAI Chat", page_icon="🧠", layout="wide");
    st.title("🧠 MorganAI Chat Companion");
    st.subheader("Upload files, ask questions, and explore insights.");
    st.divider();

    # Session state
    if "messages" not in st.session_state {
        st.session_state.messages = [];
    }
    if "session_id" not in st.session_state {
        st.session_state.session_id = "user_session_123";
    }

    # 📁 File Upload Section in Sidebar
    with st.sidebar {
        st.subheader("📁 Upload a File");
        st.caption("Supported formats: PDF, TXT, PNG, JPG, MP4, etc. (max 200MB)");
        uploaded_file = st.file_uploader("Drag & drop or browse to upload");

        if uploaded_file {
            file_b64 = base64.b64encode(uploaded_file.read()).decode("utf-8");
            file_extension = uploaded_file.name.lower().split(".")[-1];
            file_type = uploaded_file.type or "";
            supported_types = ["pdf", "txt", "png", "jpg", "jpeg", "webp", "mp4", "avi", "mov"];

            if file_extension not in supported_types and not (file_type.startswith("image") or file_type.startswith("video")) {
                st.error("❌ Unsupported file type: " + (file_type or "unknown"));
                return;
            }

            payload = {
                "file_name": uploaded_file.name,
                "file_data": file_b64,
                "session_id": st.session_state.session_id
            };
            response = requests.post("http://localhost:8000/walker/upload_file", json=payload, headers={"Authorization": "Bearer " + token});
            if response.status_code == 200 {
                st.success("✅ File uploaded and saved to: uploads/" + st.session_state.session_id + "/" + uploaded_file.name);
                st.session_state.last_uploaded_file_path = "uploads/" + st.session_state.session_id + "/" + uploaded_file.name;
            } else {
                st.error("❌ Upload failed: " + response.text);
            }
        }
    }

    # 💬 Chat Interface
    st.divider();
    st.subheader("💬 Chat with MorganAI");

    for message in st.session_state.messages {
        timestamp = time.strftime("%H:%M");
        if message["role"] == "user" {
            with st.chat_message("user") {
                cols = st.columns([0.75, 0.25]);
                with cols[0] {
                    st.write("🧑 You:\n\n" + message["content"]);
                    st.caption(timestamp);
                }
                with cols[1] {
                    st.empty();
                }
            }
        } else {
            with st.chat_message("assistant") {
                cols = st.columns([0.25, 0.75]);
                with cols[0] {
                    st.empty();
                }
                with cols[1] {
                    st.write("🤖 MorganAI:\n\n" + message["content"]);
                    st.caption(timestamp);
                }
            }
        }
    }

    prompt = st.chat_input("💡 What would you like to ask MorganAI?");
    if prompt {
        st.session_state.messages.append({"role": "user", "content": prompt});

        with st.chat_message("user") {
            cols = st.columns([0.75, 0.25]);
            with cols[0] {
                st.write("🧑 You:\n\n" + prompt);
                st.caption(time.strftime("%H:%M"));
            }
            with cols[1] {
                st.empty();
            }
        }

        with st.chat_message("assistant") {
            with st.spinner("MorganAI is thinking deeply... 🧠") {
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.session_id
                };
                if "last_uploaded_file_path" in st.session_state {
                    payload["file_path"] = st.session_state.last_uploaded_file_path;
                }

                response = requests.post("http://localhost:8000/walker/interact", json=payload, headers={"Authorization": "Bearer " + token});
                if response.status_code == 200 {
                    response = response.json();
                    reply = response["reports"][0]["response"];
                    cols = st.columns([0.25, 0.75]);
                    with cols[0] {
                        st.empty();
                    }
                    with cols[1] {
                        st.write("🤖 MorganAI:\n\n" + reply);
                        st.caption(time.strftime("%H:%M"));
                    }
                    st.session_state.messages.append({"role": "assistant", "content": reply});
                } else {
                    st.error("❌ Walker failed: " + response.text);
                }
            }
        }
    }
}

with entry {
    INSTANCE_URL = "http://localhost:8000";
    TEST_USER_EMAIL = "test@mail.com";
    TEST_USER_PASSWORD = "password";

    # Authenticate
    response = requests.post(INSTANCE_URL + "/user/login", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD});
    if response.status_code != 200 {
        response = requests.post(INSTANCE_URL + "/user/register", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD});
        assert response.status_code == 201;
        response = requests.post(INSTANCE_URL + "/user/login", json={"email": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD});
        assert response.status_code == 200;
    }

    token = response.json()["token"];
    print("🔐 Authenticated. Token:", token);

    bootstrap_frontend(token);
}