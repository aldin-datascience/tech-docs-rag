import streamlit as st
import requests
import time
import random
import string
from requests.auth import HTTPBasicAuth

from project_config.settings import (
    SESSIONS_PATH,
    FASTAPI_HOST,
    FASTAPI_PORT,
    API_USERNAME,
    API_PASSWORD,
    STREAMLIT_USERNAME,
    STREAMLIT_PASSWORD
)

# Set the page title in the browser tab
st.set_page_config(page_title="Tech Docs RAG", page_icon=":memo:")

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def upload_file(file):
    """
    Send the file to the FastAPI /process-file endpoint using basic authentication.
    """
    try:
        with st.spinner("Uploading file..."):
            file_bytes = file.getvalue()
            response = requests.post(
                f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/process-file/",
                files={"file": (file.name, file_bytes, file.type)},
                auth=HTTPBasicAuth(API_USERNAME, API_PASSWORD),
            )
        if response.status_code == 200:
            return f"Success: {response.json()['message']}"
        else:
            return f"Error: {response.json().get('detail', 'Unknown error')}"
    except Exception as e:
        return f"Error: {e}"

def response_generator(prompt):
    """
    Call the /process-query endpoint to get the chatbot's answer, then yield it word-by-word.
    """
    try:
        # Call FastAPI /process-query route with session_id and question
        response = requests.post(
            f"http://{FASTAPI_HOST}:{FASTAPI_PORT}/process-query/",
            json={"session_id": st.session_state.session_id, "question": prompt},
            auth=HTTPBasicAuth(API_USERNAME, API_PASSWORD),
        )

        if response.status_code == 200:
            data = response.json()
            answer_text = data.get("answer", "")
        else:
            # If there's an error, show the raw response
            answer_text = f"Error: {response.text}"

        # Output the answer in a "typewriter" style
        for word in answer_text.split():
            yield word + " "
            time.sleep(0.05)

        # Once the entire answer is printed, store the updated conversation to a text file
        store_to_txt(SESSIONS_PATH)
    except Exception as e:
        yield f"Error generating response: {e}"

def store_to_txt(save_path):
    """
    Save the conversation history from st.session_state.messages to a text file.
    """
    conversation_history_text = '\n\n'.join([
        f'{message["role"]}: {message["content"]}' for message in st.session_state.messages
    ])

    with open(save_path + st.session_state.session_id + '.txt', 'w') as file:
        file.write(conversation_history_text)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Tech Docs RAG - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        # Check credentials against .env values
        if username == STREAMLIT_USERNAME and password == STREAMLIT_PASSWORD:
            st.session_state.logged_in = True
            st.rerun()  # Refresh the app to show content
        else:
            st.error("Invalid credentials.")
    st.stop()

# Now that the user is authenticated, continue with the main app
st.title("Technical Documentation AI Assistant")

# Initialize chat state if needed
if "messages" not in st.session_state:
    st.session_state.tips = [
        "The chatbot answers questions exclusively about technical documentation.",
        "For the best results, upload only relevant technical documentation files.",
        "Duplicate files won't be processed, so reuploading is safe.",
        "Ensure your documentation is in a supported file format.",
        "Questions should be precise for more accurate answers."
    ]
    st.session_state.messages = []
    st.session_state.session_id = generate_random_string()

# Sidebar for file uploads
st.sidebar.header("Upload Files")

uploaded_files = st.sidebar.file_uploader(
    "Upload technical documentation",
    type=["pdf", "md", "txt"],
    accept_multiple_files=True
)

# A placeholder to show file upload messages
upload_message_placeholder = st.sidebar.empty()

# Track uploaded files to avoid re-upload
if "uploaded_files_set" not in st.session_state:
    st.session_state.uploaded_files_set = set()

if uploaded_files:
    for file in uploaded_files:
        if file.name not in st.session_state.uploaded_files_set:
            result_message = upload_file(file)
            st.session_state.uploaded_files_set.add(file.name)
            with upload_message_placeholder:
                if "Success:" in result_message:
                    st.success(result_message)
                else:
                    st.error(result_message)
        else:
            with upload_message_placeholder:
                st.info(f"Tip: {random.choice(st.session_state.tips)}")

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Prompt for new user messages
if prompt := st.chat_input("Type your query here..."):
    # User's message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant's response (streamed word-by-word)
    with st.chat_message("assistant"):
        response = st.write_stream(response_generator(prompt))

    # The final 'response' in this context is just the last item from `response_generator`
    if isinstance(response, str):
        # If the generator yielded a final string, store it
        st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        # If the generator only yielded partial strings, you may need additional handling
        pass
