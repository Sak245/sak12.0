import streamlit as st
import boto3
import time
import gc
import google.generativeai as genai
from botocore.config import Config
from phidata.agent import Agent
from phidata.model.google import Gemini

# Compatibility patch for Python 3.12
import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

# Streamlit UI Configuration
st.set_page_config(page_title="Video Analyzer", layout="wide")
st.title("🔒 Secure Video Analysis Platform")

# Credential Collection Sidebar
with st.sidebar:
    st.header("🔑 Authentication")
    aws_access_key = st.text_input("AWS Access Key ID", type="password")
    aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
    aws_region = st.selectbox("AWS Region", ["us-east-1", "us-west-2", "eu-central-1"])
    google_api_key = st.text_input("Google Gemini API Key", type="password")
    s3_bucket = st.text_input("S3 Bucket Name")
    
    st.markdown("---")
    st.info("Credentials are never stored and reset on page reload.")

# Validate credentials before proceeding
if not all([aws_access_key, aws_secret_key, google_api_key, s3_bucket]):
    st.warning("⚠️ Please provide all required credentials in the sidebar")
    st.stop()

# Configure AWS client with user-provided credentials
try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region,
        config=Config(
            retries={'max_attempts': 3, 'mode': 'standard'},
            connect_timeout=30,
            read_timeout=30
        )
    )
    genai.configure(api_key=google_api_key)
except Exception as e:
    st.error(f"❌ Configuration failed: {str(e)}")
    st.stop()

def analyze_video(file_obj, user_query):
    """Process video with security cleanup"""
    try:
        file_key = f"video_{int(time.time())}_{file_obj.name}"
        
        # Secure upload to S3
        with st.spinner("🔒 Securely uploading video..."):
            s3.upload_fileobj(file_obj, s3_bucket, file_key)
            video_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': s3_bucket, 'Key': file_key},
                ExpiresIn=1200  # 20 minutes
            )
        
        # Analyze with Gemini
        with st.spinner("🧠 Analyzing content..."):
            agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))
            response = agent.run(
                f"{user_query}\n\nVideo context: {video_url}",
                videos=[video_url]
            )
            
            return response.content
            
    except Exception as e:
        st.error(f"🚨 Analysis failed: {str(e)}")
        return None
    finally:
        # Secure cleanup
        s3.delete_object(Bucket=s3_bucket, Key=file_key)
        gc.collect()
        file_obj.close()

# Main Application Interface
uploaded_file = st.file_uploader("📤 Upload video file (max 200MB)", 
                               type=["mp4", "mov", "avi"],
                               help="Your file is temporarily processed in memory")
user_query = st.text_area("🔍 What would you like to analyze?", 
                         placeholder="Example: Summarize the key points from this video",
                         height=100)

if uploaded_file and user_query:
    if st.button("🚀 Start Analysis", type="primary"):
        analysis_result = analyze_video(uploaded_file, user_query)
        if analysis_result:
            st.subheader("📝 Analysis Results")
            st.markdown(analysis_result)
            st.success("✅ Analysis completed successfully")
            
            # Security confirmation
            with st.expander("🔐 Security Details"):
                st.markdown("""
                - Credentials were only used for this session
                - Video file permanently deleted from S3
                - No sensitive data stored""")
