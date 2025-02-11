# Monkey patch for Python 3.11+ compatibility
import inspect
from inspect import getfullargspec
inspect.getargspec = getfullargspec  # Fix for phi library

import streamlit as st
import boto3
import os
import time
import gc
from botocore.config import Config
from phi.agent import Agent
from phi.model.google import Gemini

# AWS Configuration
AWS_CONFIG = Config(
    retries={'max_attempts': 3, 'mode': 'standard'}
)

s3 = boto3.client(
    's3',
    config=AWS_CONFIG,
    aws_access_key_id=os.environ['AWS_ACCESS_KEY'],
    aws_secret_access_key=os.environ['AWS_SECRET_KEY'],
    region_name='us-east-1'
)
S3_BUCKET = os.environ['S3_BUCKET']

# Streamlit UI
st.set_page_config(page_title="Video Analyzer", layout="wide")
st.title("AWS-Powered Video Analysis")

def process_video(file_obj, query):
    try:
        file_key = f"video_{int(time.time())}_{file_obj.name}"
        
        # Upload to S3
        s3.upload_fileobj(file_obj, S3_BUCKET, file_key)
        video_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': file_key},
            ExpiresIn=1200
        )
        
        # Analyze with Gemini
        agent = Agent(model=Gemini(id="gemini-2.0-flash-exp"))
        response = agent.run(
            f"{query} in this video: {video_url}",
            videos=[video_url]
        )
        
        return response.content
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
    finally:
        s3.delete_object(Bucket=S3_BUCKET, Key=file_key)
        gc.collect()

# UI Components
uploaded_file = st.file_uploader("Upload video (max 200MB)", type=["mp4", "mov"])
user_query = st.text_input("What would you like to analyze?")

if uploaded_file and user_query:
    if st.button("Analyze"):
        with st.spinner("Processing..."):
            result = process_video(uploaded_file, user_query)
            st.markdown(result)
