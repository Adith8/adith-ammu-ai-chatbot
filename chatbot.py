import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

# Custom CSS for attractive header only - Updated
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Beautiful header
st.markdown('<h1 class="main-header">🤖 Adith\'s and Ammu\'s AI Chatbot</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">📚 Ask anything about your PDF documents with AI intelligence</p>', unsafe_allow_html=True)

# Initialize session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'chunks' not in st.session_state:
    st.session_state.chunks = []
if 'vectorizer' not in st.session_state:
    st.session_state.vectorizer = None
if 'chunk_vectors' not in st.session_state:
    st.session_state.chunk_vectors = None

with st.sidebar:
    st.title("your document")
    file=st.file_uploader("upload your file",type=["pdf"])
    
#extract the text
if file is not None and not st.session_state.processed:
    with st.spinner("Processing your document..."):
        pdf_reader=PdfReader(file)
        text=""
        for pages in pdf_reader.pages:
            text+=pages.extract_text()
        
        #breaking it into chunks 
        text_splitter = RecursiveCharacterTextSplitter(
            separators=["\n"],
            chunk_size=1000,
            chunk_overlap=150,
            length_function=len
        )
        st.session_state.chunks = text_splitter.split_text(text)
        
        #embeddings using simple TF-IDF (no PyTorch issues)
        st.session_state.vectorizer = TfidfVectorizer()
        st.session_state.chunk_vectors = st.session_state.vectorizer.fit_transform(st.session_state.chunks)
        
        # Mark as processed
        st.session_state.processed = True
        
    st.success("✅ Document processed! You can now ask multiple questions.")
    
    # Show chunks once
    with st.expander("📄 View document chunks"):
        st.write(st.session_state.chunks)

if st.session_state.processed:
    
    #get the user question
    user_question=st.text_input("please ask your question here", key="question_input")
    
    if user_question:
        # Convert question to vector and find similar chunks
        question_vector = st.session_state.vectorizer.transform([user_question])
        similarities = cosine_similarity(question_vector, st.session_state.chunk_vectors)
        
        # Get top 3 most similar chunks
        top_indices = similarities[0].argsort()[-3:][::-1]
        relevant_chunks = [st.session_state.chunks[i] for i in top_indices if similarities[0][i] > 0]
        
        if relevant_chunks:
            st.write("**🤖 Answer:**")
            
            # Improved answer extraction
            question_lower = user_question.lower()
            question_words = set(question_lower.split())
            
            # Remove common stop words
            stop_words = {'what', 'how', 'when', 'where', 'why', 'who', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            key_words = question_words - stop_words
            
            best_answers = []
            
            for chunk in relevant_chunks:
                sentences = re.split(r'[.!?]+', chunk)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) > 30:  # Only consider substantial sentences
                        sentence_lower = sentence.lower()
                        sentence_words = set(sentence_lower.split())
                        
                        # Calculate relevance score
                        keyword_matches = len(key_words.intersection(sentence_words))
                        total_words = len(sentence_words)
                        
                        # Boost score if sentence contains question type indicators
                        boost = 0
                        if any(word in sentence_lower for word in ['speed', 'fast', 'mph', 'km/h', 'maximum', 'top', 'highest']):
                            boost += 2
                        if any(word in sentence_lower for word in ['price', 'cost', 'expensive', 'cheap', 'dollar', '$']):
                            boost += 2
                        if any(word in sentence_lower for word in ['year', 'date', 'when', 'time', 'launched', 'released']):
                            boost += 2
                            
                        relevance_score = (keyword_matches / max(len(key_words), 1)) + (boost / 10)
                        
                        if keyword_matches > 0 or boost > 0:
                            best_answers.append((sentence, relevance_score))
            
            # Sort by relevance score and show top answers
            best_answers.sort(key=lambda x: x[1], reverse=True)
            
            if best_answers:
                for i, (sentence, score) in enumerate(best_answers[:3]):
                    st.write(f"• {sentence.strip()}")
            else:
                # Fallback: show most relevant chunk with highlighting
                chunk = relevant_chunks[0]
                st.write("Based on the document, here's the most relevant information:")
                
                # Highlight key words in the chunk
                highlighted_chunk = chunk
                for word in key_words:
                    if len(word) > 2:  # Only highlight meaningful words
                        highlighted_chunk = re.sub(f'\\b{re.escape(word)}\\b', f'**{word}**', highlighted_chunk, flags=re.IGNORECASE)
                
                st.write(highlighted_chunk)
            

            with st.expander("📄 View all relevant chunks"):
                for i, chunk in enumerate(relevant_chunks):
                    st.write(f"**Chunk {i+1}:**")
                    st.write(chunk)
                    st.write("---")
        else:
            st.write("❌ No relevant information found in the document for your question.")
else:
    if file is None:
        st.info("👆 Please upload a PDF file to start asking questions.")
    else:
        st.info("⏳ Processing your document...")
    


    
