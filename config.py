import streamlit as st

# 애플리케이션 정보
APP_VERSION = "v1.0.0"
ENV_NAME = st.secrets.get("ENV_NAME", "PROD")

# API 인증 정보
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
NOTION_TOKEN = st.secrets.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = st.secrets.get("NOTION_DATABASE_ID", "")

# UI 설정
TICKER_INTERVAL = 3.0
NOTION_PUBLISH_URL = st.secrets.get("NOTION_PUBLISH_URL", "#")

# 노션 리포트 섹션 순서 (디시인사이드 맞춤형)
NOTION_SECTION_ORDER = [
    "ai_one_liner",
    "sentiment_summary",
    "user_type_analysis",
    "issue_pick",
    "category_detail"
]