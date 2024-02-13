import streamlit as st
from llama_hub.youtube_transcript import YoutubeTranscriptReader
from llama_hub.youtube_transcript import is_youtube_video
from llama_index import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
)
from llama_index.prompts import ChatMessage, MessageRole

from llama_index.tools import QueryEngineTool, ToolMetadata
import os
# import openai

from llama_hub.tools.wikipedia import WikipediaToolSpec

from llama_index.agent import OpenAIAgent
from fetch_yt_metadata import fetch_youtube_metadata

video_url = None

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    if openai_api_key:
        os.environ["OPENAI_API_KEY"] = openai_api_key
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    video_url = st.text_input("'Enter your video url here:", key="video_url")
    if video_url:
        st.video(video_url)
        if is_youtube_video(video_url):
            metadata = fetch_youtube_metadata(video_url)
            st.session_state["metadata"] = metadata
            st.header("Metadata:")
            for k, v in metadata.items():
                if k == "video_description":
                    st.text_area("Description:", height=200, value=v, disabled=True)
                else:
                    st.write(f"{k}: {v}")
        st.text_area("Transcript:", height=200, value=st.session_state.get("transcript", ""))

if st.session_state.get("video_url"):
    url = st.session_state.get("video_url")
    st.write(f"Chat with {url}")



if "counter" not in st.session_state:
    st.session_state.counter = 0

st.session_state.counter += 1

st.header(f"This page has run {st.session_state.counter} times.")
st.button("Run it again")

query_engine = None
transcript = None
if video_url:
    video_id = video_url.split('=')[1].split('&')[0]
    # check if storage already exists
    PERSIST_DIR = f"./storage/{video_id}"
    if not os.path.exists(PERSIST_DIR):
        # load the documents and create the index
        # documents = SimpleDirectoryReader("data").load_data()
        loader = YoutubeTranscriptReader()
        documents = loader.load_data(ytlinks=[url])
        # save the documents to disk using the video_id.sbt

        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        with open(f"{PERSIST_DIR}/transcript.txt", "w") as f:
            for doc in documents:
                    f.write(doc.text)
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
        index = load_index_from_storage(storage_context)
    # either way we can now query the index
    query_engine = index.as_query_engine()
    if not st.session_state.get("summary"):
        summary = query_engine.query("What's the video about?").response
        st.session_state["summary"] = summary
    if not st.session_state.get("transcript"):
        transcript = open(f"{PERSIST_DIR}/transcript.txt").read()
        st.session_state["transcript"] = transcript
    



st.title('💬 Talk2Video')
st.write(st.session_state.get("summary",'Load a youtube video and chat with it'))

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    
    vector_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name=f"VideoTranscript",
            description=f"useful for when you want to answer queries about the content of the video.",
        ),
    )
    
    wiki_tool_spec = WikipediaToolSpec()
    tools = wiki_tool_spec.to_tool_list() #+ query_engine_tools
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    agent = OpenAIAgent.from_tools([vector_tool], verbose=True, openai_api_key=st.session_state.get("chatbot_api_key"))
    chat_history = [ChatMessage(role=MessageRole.USER if x.get("role","assistant") == "user" else "assistant", content=x.get("content","")) for x in st.session_state.messages]
    response = agent.chat(prompt, chat_history=chat_history)
    msg = {"role":"assistant", "content":response.response}
    st.session_state.messages.append(msg)
    st.chat_message("assistant").write(msg.get("content"))
    
