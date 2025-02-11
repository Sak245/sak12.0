```markdown
# Video Analyzer

Analyze videos using AWS S3 and Google Gemini AI. Handles files >200MB via direct upload.

## 🚀 Deployment

1. **Streamlit Cloud:**
   - Set secrets:
     - `AWS_ACCESS_KEY`
     - `AWS_SECRET_KEY`
     - `S3_BUCKET`
     - `GOOGLE_API_KEY`

2. **AWS Setup:**
   - Create S3 bucket
   - Add CORS policy:
   ```
   [{
     "AllowedMethods": ["PUT", "GET", "DELETE"],
     "AllowedOrigins": ["*"]
   }]
   ```

## 📦 Requirements
`requirements.txt` included

---

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app.streamlit.app)
```

