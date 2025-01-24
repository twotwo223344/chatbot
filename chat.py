import os
import google.generativeai as genai
import json
from get_namuwiki_docs import load_namuwiki_docs_selenium
from langchain.schema import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import streamlit as st

# with open("key.json", 'r') as file:
#     data = json.load(file)
    
# gemini_api_key = data.get("gemini-key")

# TODO: 아래 YOUR-HUGGINGFACE-API-KEY랑 OUR-GEMINI-API-KEY에 자기꺼 넣기
if not os.environ.get("HUGGINGFACEHUB_API_TOKEN"):
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"    
gemini_api_key = "AIzaSyBl5MM4DnKR-D-CrFR3W1uMG3w8KqKcNv4"

genai.configure(api_key=gemini_api_key)

# gemini 모델 로드 
def load_model():
    with st.spinner("모델을 로딩하는 중..."):
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("Model loaded...")
    return gemini_model

# 임베딩 로드
def load_embedding():
    with st.spinner("임베딩을 로딩하는 중..."):
        embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    print("Embedding loaded...")
    return embedding

# Faiss vector DB 생성
def create_vectorstore(topic):     
    with st.spinner("나무위키에서 문서를 가져오는 중..."):
        text = load_namuwiki_docs_selenium(topic)        
        # st.write(f"찾은 문서 예시:\n{text[:100]}")
        
        
        # text ="""휴먼원정대팀에 팀장은 이준혁입니다. 구성원은 이준혁, 김민석, 배휘호, 이기성 으로 총 4명입니다."""


    if text:        
        paragraphs = text.split("\n\n")[:-1] if "\n\n" in text else text.split("\n")
    else:
        paragraphs = []    
        
    # FAISS 벡터 스토어 생성
    with st.spinner("벡터 스토어를 생성하는 중..."): 
        # convert to Document object (required for LangChain)
        documents = [Document(page_content=doc, metadata={"source": f"doc{idx+1}"}) for idx, doc in enumerate(paragraphs)]
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        splits = text_splitter.split_documents(documents)    
        
        vectorstore = FAISS.from_documents(documents=splits, embedding=st.session_state.embedding)
        
    return vectorstore

# RAG using prompt
def rag_chatbot(question):
    context_docs = st.session_state.vectorstore.similarity_search(question, k=2)
    # for i, doc in enumerate(context_docs):
    #     st.write(f"{i+1}번째 문서: {doc.page_content}")
        
    context_docs = "\n\n".join([f"{i+1}번째 문서:\n{doc.page_content}" for i, doc in enumerate(context_docs)])

    # prompt = f"Context: {context_docs}\nQuestion: {question}\nAnswer in a complete sentence:"
    prompt = f"문맥: {context_docs}\n질문: {question}\n답변:"
    # response = gemini_model(prompt)
    
    response = st.session_state.model.generate_content(prompt)
    answer = response.candidates[0].content.parts[0].text

    print("출처 문서:", context_docs)
    return answer, context_docs


# Streamlit 세션에서 모델을 한 번만 로드하도록 설정
# 1. gemini model 
if "model" not in st.session_state:
    st.session_state.model = load_model()

# 2. embedding model
if "embedding" not in st.session_state:
    st.session_state.embedding = load_embedding()

# 세션의 대화 히스토리 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    
if "topic" not in st.session_state:
    st.session_state.topic = ""


# 1. 이 주제로 Vectorstore 만들 문서 가져오기
topic = st.text_input('찾을 문서의 주제를 입력하세요. 예시) 흑백요리사: 요리 계급 전쟁(시즌 1)')

if st.button('문서 가져오기'):
    if topic:
        vectorstore = create_vectorstore(topic)
        st.session_state.vectorstore = vectorstore    
        st.session_state.topic = topic
    else:
        st.warning('주제를 입력해라', icon="⚠️")
    
if st.session_state.topic and st.session_state.vectorstore:    
    st.write(f"주제: '{st.session_state.topic}' 로 Vectorstore 준비완료")
    
    
# 2. 사용자 질문에 유사한 내용을 Vectorstore에서 RAG 기반으로 답변
user_query = st.text_input('질문을 입력하세요.')

if st.button('질문하기') and user_query:
    # 사용자의 질문을 히스토리에 추가
    st.session_state.chat_history.append(f"[user]: {user_query}")
    st.text(f'[You]: {user_query}')    

    # response = st.session_state.model.generate_content(user_querie)
    # model_response = response.candidates[0].content.parts[0].text
        
    # 모델 응답 RAG
    if st.session_state.vectorstore:    
        response, context_docs = rag_chatbot(user_query)        
        st.text(f'[Chatbot]: {response}')
        st.text(f'출처 문서:\n')        
        st.write(context_docs)
    else: 
        response = "vector store is not ready."
        st.text(f'[Chatbot]: {response}')
    
    # 모델 응답을 히스토리에 추가
    st.session_state.chat_history.append(f"[chatbot]: {response}")
    
    # 전체 히스토리 출력
    st.text("Chat History")
    st.text('--------------------------------------------')
    st.text("\n".join(st.session_state.chat_history))
