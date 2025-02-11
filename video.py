import streamlit as st
import boto3
import time
import gc
import google.generativeai as genai
from botocore.config import Config
from phi.agent import Agent
from phi.model.google import Gemini

# Compatibility patch for Python 3.12
import inspect
if not hasattr(inspect, 'getargspec'):
    inspect.getargspec = inspect.getfullargspec

# Streamlit UI Configuration
st.set_page_config(page_title="Video Analyzer", layout="wide")
st.title("🔒 Secure AWS Video Analysis")

# Credential Collection
with st.sidebar:
    st.header("🔑 Authentication")
    aws_access = st.text_input("AWS Access Key ID", type="password")
    aws_secret = st.text_input("AWS Secret Key", type="password")
    aws_region = st.selectbox("AWS Region", ["us-east-1", "us-west-2"])
    google_key = st.text_input("Google API Key", type="password")
    s3_bucket = st.text_input("S3 Bucket Name")
    st.markdown("---")
    st.info("Credentials are never stored and reset on page reload.")

# Validate inputs
if not all([aws_access, aws_secret, google_key, s3_bucket]):
    st.warning("⚠️ Complete all credential fields in the sidebar")
    st.stop()

# Configure clients
try:
    s3 = boto3.client(
        's3',
        aws_access_key_id=aws_access,
        aws_secret_access_key=aws_secret,
        region_name=aws_region,
        config=Config(
            retries={'max_attempts': 3},
            connect_timeout=30,
            read_timeout=30
        )
    )
    genai.configure(api_key=google_key)
except Exception as e:
    st.error(f"❌ Configuration error: {str(e)}")
    st.stop()

def process_video(file_obj, query):
    file_key = f"vid_{int(time.time())}_{file_obj.name}"
    try:
        # Upload to S3
        with st.spinner("🔒 Securing upload..."):
            s3.upload_fileobj(file_obj, s3_bucket, file_key)
            video_url = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': s3_bucket, 'Key': file_key},
                ExpiresIn=1200
            )
        
        # Analyze with Gemini
        with st.spinner("🧠 Processing content..."):
            agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))
            response = agent.run(
                f"{query}\n\nVideo context: {video_url}",
                videos=[video_url]
            )
            return response.content
            
    except Exception as e:
        st.error(f"🚨 Analysis failed: {str(e)}")
        return None
    finally:
        # Cleanup
        s3.delete_object(Bucket=s3_bucket, Key=file_key)
        gc.collect()
        file_obj.close()

# Main UI
uploaded_file = st.file_uploader("📤 Upload video (max 200MB)", 
                                type=["mp4", "mov"],
                                help="Temporary in-memory processing")
user_query = st.text_area("🔍 Analysis request", 
                         placeholder="What insights do you need?",
                         height=100)

if uploaded_file and user_query:
    if st.button("🚀 Start Analysis", type="primary"):
        result = process_video(uploaded_file, user_query)
        if result:
            st.subheader("📝 Results")
            st.markdown(result)
            st.success("✅ Analysis complete")
            
            with st.expander("🔐 Security confirmation"):
                st.markdown("""
                - Credentials used only for this session
                - File deleted from S3
                - No data persistence""")
