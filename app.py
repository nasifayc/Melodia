import streamlit as st
from langchain.chains import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, GEMINI_API_KEY
import time

# Page configuration
st.set_page_config(
    page_title="Music Graph Chatbot",
    page_icon="🎵",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1DB954;
        text-align: center;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #2C2F36; 
        color: #E4E4E4; 
        padding: 12px 18px;
        border-radius: 12px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        border: 1px solid #3A3D44; 
    }

    .bot-message {
        background-color: #1E1F23; 
        color: #CCCCCC; 
        padding: 12px 18px;
        border-radius: 12px;
        margin: 8px 0;
        max-width: 80%;
        margin-right: auto;
        border: 1px solid #2A2B2F; 
    }

   
    .user-message:hover, .bot-message:hover {
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        transition: box-shadow 0.3s ease;
    }   
    .stTextInput > div > div > input {
        border-radius: 20px;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory" not in st.session_state:
    st.session_state.memory = ConversationBufferMemory()
if "processing" not in st.session_state:
    st.session_state.processing = False
if "last_query" not in st.session_state:
    st.session_state.last_query = None

# Initialize Neo4j connection
@st.cache_resource
def init_neo4j_connection():
    try:
        graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
        graph.refresh_schema()
        return graph
    except Exception as e:
        st.error(f"❌ Failed to connect to Neo4j: {e}")
        return None

# Initialize LLM chain
def init_llm_chain(_graph):
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0, google_api_key=GEMINI_API_KEY)
        chain = GraphCypherQAChain.from_llm(
            cypher_llm=llm,
            qa_llm=llm,
            graph=_graph,
            verbose=True,
            validate_cypher=True,
            return_direct=False,
            memory=st.session_state.memory,
            allow_dangerous_requests=True
        )
        return chain
    except Exception as e:
        st.error(f"❌ Failed to initialize LLM: {e}")
        return None

# Header
st.markdown('<h1 class="main-header">🎵 Music Graph Chatbot</h1>', unsafe_allow_html=True)
st.markdown("Ask questions about artists, songs, and albums in the music database")

# Sidebar
with st.sidebar:
    st.header("🎯 Quick Actions")
    
    if st.button("🔄 Refresh Connection", use_container_width=True):
        st.cache_resource.clear()
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.session_state.processing = False
        st.session_state.last_query = None
        st.rerun()
    
    if st.button("🧹 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.memory.clear()
        st.session_state.processing = False
        st.session_state.last_query = None
        st.rerun()
    
    st.header("💡 Example Queries")
    examples = [
        "What are the most popular songs by Queen?",
        "List artists in the 'pop' genre",
        "Show me high-energy dance songs",
        "Which albums were released in 2019?",
        "Find collaborations between artists"
    ]
    
    for example in examples:
        if st.button(example, use_container_width=True, key=example):
            st.session_state.user_query = example
            st.rerun()

# Main chat interface
chat_container = st.container()

with chat_container:
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)

# Query input at the bottom
user_query = st.text_input(
    "Ask about music:",
    value=st.session_state.get("user_query", ""),
    key="query_input",
    placeholder="e.g., What are the most popular pop songs?",
    label_visibility="collapsed"
)

if user_query and user_query != st.session_state.last_query and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.last_query = user_query
    
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    response_placeholder = st.empty()
    
    try:
        # Initialize connections
        graph = init_neo4j_connection()
        if graph:
            chain = init_llm_chain(graph)
            
            if chain:
                # Show typing indicator
                typing_dots = ""
                
                for i in range(3):
                    typing_dots += "."
                    response_placeholder.markdown(f'<div class="bot-message">🤖 Thinking{typing_dots}</div>', unsafe_allow_html=True)
                    time.sleep(0.3)
                
                # Get response
                result = chain.invoke({"query": user_query})
                
                if result and 'result' in result:
                    response = result['result']
                    st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Clear typing indicator
                response_placeholder.empty()
            
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        st.error(error_msg)
    finally:
        st.session_state.processing = False
        st.rerun()


# Footer
st.markdown("---")
st.caption("Powered by Neo4j Graph Database & Google Gemini AI • Built with Streamlit")