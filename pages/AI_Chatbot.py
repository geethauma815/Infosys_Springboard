# pages/AI_Chatbot.py
import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# LangChain Imports
from langchain_groq import ChatGroq
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Standard Import for QA Chain and Prompts
from langchain.chains import RetrievalQA 
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate # New import for direct chat

from config import CONTRACTS_DIR

# Load environment variables
load_dotenv()

# ================= PAGE SETUP =================
st.set_page_config(page_title="AI Chatbot", layout="wide")

# ================= AUTHENTICATION ENFORCEMENT =================
if not st.session_state.get("logged_in"):
    st.empty()
    st.switch_page("pages/Login.py")

# ================= WHITE UI CSS =================
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF !important; color: #333333 !important; }
    header[data-testid="stHeader"] { background-color: #FFFFFF !important; }
    header[data-testid="stHeader"] * { color: #333333 !important; }
    [data-testid="stSidebar"] { background-color: #F9FAFB !important; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebarNav"] { display: none; }
    .stChatMessage {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-radius: 12px;
    }
    div[data-testid="chatAvatarIcon-user"] { background-color: #0056D2 !important; }
    .stChatInput textarea { background-color: #F9FAFB !important; border-color: #E5E7EB !important; color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# ================= SIDEBAR NAVIGATION =================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=40)
    st.markdown("### AI Powered Regulatory Compliance Checker for Contracts")
    st.success(f"👤 **{st.session_state.get('user_name', 'User')}**")
    st.page_link("Home.py", label="Overview", icon="🏠")
    st.page_link("pages/Contract_Analysis.py", label="Contract Analysis", icon="📄")
    st.page_link("pages/Risk_Assessment.py", label="Risk Assessment", icon="📊")
    st.page_link("pages/Regulation_Monitor.py", label="Regulation Monitor", icon="⚖️")
    st.page_link("pages/AI_Chatbot.py", label="AI Chatbot", icon="🤖")
    st.markdown("---")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ================= BACKEND AI LOGIC =================

@st.cache_resource
def build_vector_store():
    """Reads contracts and creates index. Returns None if no files."""
    all_docs = []
    if not os.path.exists(CONTRACTS_DIR): return None
    files = [f for f in os.listdir(CONTRACTS_DIR) if f.endswith(".pdf") or f.endswith(".txt")]
    if not files: return None

    for f in files:
        path = os.path.join(CONTRACTS_DIR, f)
        try:
            if f.endswith(".pdf"): loader = PyPDFLoader(path)
            else: loader = TextLoader(path)
            all_docs.extend(loader.load())
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if not all_docs: return None

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(all_docs)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2") # Cited: Hugging Face
    
    try:
        return FAISS.from_documents(splits, embeddings)
    except Exception as e:
        st.error(f"Error creating vector store: {e}")
        return None

def get_answer(query, vectorstore):
    """
    Handles both Document RAG and General Chat.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return "⚠️ Error: Missing GROQ_API_KEY."
    
    try:
        llm = ChatGroq(temperature=0, model_name="llama-3.3-70b-versatile", api_key=api_key) # Cited: Groq
        current_date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- SCENARIO A: NO DOCUMENTS (General Chat) ---
        if vectorstore is None:
            # Direct Prompt for General Chat
            prompt_template = ChatPromptTemplate.from_messages([
                ("system", f"You are a helpful Legal AI Assistant. The current date/time is {current_date_str}. You do not have access to any contracts yet. If the user asks about contracts, ask them to upload one. Otherwise, answer their general questions."),
                ("human", "{question}")
            ])
            chain = prompt_template | llm
            response = chain.invoke({"question": query})
            return {"result": response.content} # Return standardized format

        # --- SCENARIO B: WITH DOCUMENTS (RAG) ---
        else:
            template = f"""
            System: You are a smart Legal AI Assistant.
            CRITICAL CONTEXT:
            - Current Date: {current_date_str}
            - Use the 'Context' below to answer questions about contracts.
            - If the user asks a general question (like "what is the date", "hi", "who are you"), ignore the context and answer politely.
            
            Context:
            {{context}}

            User Question: {{question}}
            
            Answer:
            """
            prompt_obj = PromptTemplate(template=template, input_variables=["context", "question"])
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
                return_source_documents=True,
                chain_type_kwargs={"prompt": prompt_obj}
            )
            return qa_chain.invoke({"query": query})

    except Exception as e:
        return f"Error: {str(e)}"

# ================= MAIN UI =================

st.title("🤖 Legal Assistant")
st.caption("Ask about your contracts, or general legal questions!")

# 1. Load Knowledge Base (Background)
with st.spinner("Initializing AI..."):
    vectorstore = build_vector_store()

# 2. Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I am your Legal Assistant. Ask me about your contracts or today's date."}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 3. Chat Input
if prompt := st.chat_input("Ex: 'What is today's date?' or 'Summarize the liability clause'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Call get_answer regardless of vectorstore status
                # The function now handles the None case internally
                response_data = get_answer(prompt, vectorstore)
                
                if isinstance(response_data, str): 
                    final_answer = response_data
                else:
                    final_answer = response_data['result']
                    
                    # Show sources only if RAG was used
                    if 'source_documents' in response_data and response_data['source_documents']:
                        if "I couldn't find" not in final_answer:
                            sources = list(set([doc.metadata.get('source', 'Unknown') for doc in response_data['source_documents']]))
                            source_names = [os.path.basename(s) for s in sources]
                            if source_names:
                                final_answer += f"\n\n**Sources:** `{'`, `'.join(source_names)}`"

                st.markdown(final_answer)
                st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
            except Exception as e:
                st.error(f"AI Error: {str(e)}")