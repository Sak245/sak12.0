import streamlit as st
import boto3
from phi.agent import Agent
from phi.model.google import Gemini
import os
import time

# Configure AWS from environment variables
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
S3_BUCKET = os.environ.get("S3_BUCKET")

# Configure Gemini
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Initialize AWS clients
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

# Streamlit UI
st.set_page_config(page_title="Video Analyzer", layout="wide")
st.title("🔍 AWS Video Analysis")

def get_presigned_url(file_name):
    """Generate presigned URL for direct upload"""
    return s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': S3_BUCKET,
            'Key': file_name,
            'ContentType': 'video/mp4'
        },
        ExpiresIn=3600
    )

# File upload section
uploaded_file = st.file_uploader("Upload video (max 200MB)", type=["mp4", "mov"])
analysis_query = st.text_input("What would you like to analyze?")

if uploaded_file and analysis_query:
    file_size = uploaded_file.size / (1024 * 1024)  # MB
    
    if file_size > 200:
        # Large file handling
        file_name = f"video_{int(time.time())}.mp4"
        presigned_url = get_presigned_url(file_name)
        
        st.markdown(f"""
            **Large File Upload:**
            ```
            curl -X PUT -T "{uploaded_file.name}" "{presigned_url}"
            ```
            """)
        st.info("Upload via command above then click Analyze")
    else:
        # Small file handling
        with st.spinner("Processing..."):
            try:
                # Upload to S3
                s3.upload_fileobj(uploaded_file, S3_BUCKET, uploaded_file.name)
                
                # Generate presigned URL
                video_url = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': S3_BUCKET, 'Key': uploaded_file.name},
                    ExpiresIn=1200
                )
                
                # Analyze with Gemini
                agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))
                response = agent.run(
                    f"{analysis_query} in this video: {video_url}",
                    videos=[video_url]
                )
                
                st.subheader("Analysis Results")
                st.markdown(response.content)
                
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                s3.delete_object(Bucket=S3_BUCKET, Key=uploaded_file.name)
