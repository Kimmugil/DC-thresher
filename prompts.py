def build_dc_prompt(gallery_id, post_data, user_feedback=""):
    """
    디시인사이드 커뮤니티 민심 분석을 위한 페르소나와 지시문을 구성합니다.
    """
    feedback_instruction = f"\n\n[사용자 피드백 반영 요청]:\n{user_feedback}\n" if user_feedback else ""
    
    # 시스템 오작동 방지를 위한 마크다운 백틱 우회 처리
    backticks = "" * 3
    
    return f"""
    당신은 커뮤니티 데이터 분석 전문가이자 전략 PM입니다. 
    다음은 '{gallery_id}' 갤러리에서 수집된 최근 게시글 데이터입니다. {feedback_instruction}
    
    [분석 및 작성 가이드라인]:
    1. 결과물에 마크다운 코드 블록 기호({backticks})를 절대 포함하지 마십시오. 순수 JSON 데이터만 출력해야 합니다.
    2. 모든 텍스트에서 마크다운 볼드체(**) 기호를 사용하지 마십시오.
    3. '유동'과 '고닉'의 여론 차이 및 게시글의 댓글 수를 통한 화제성을 심도 있게 분석하십시오.
    4. 분석 결과는 비즈니스 리포트 수준의 격식 있는 한국어로 작성하십시오.
    
    [출력 JSON 스키마]:
    {{
      "critic_one_liner": "갤러리 민심 요약 한줄평",
      "sentiment_analysis": "전반적인 여론 동향 코멘트",
      "final_summary_all": ["[긍정] 코멘트", "[부정] 코멘트"],
      "ai_issue_pick": ["주요 논란 및 인사이트"],
      "user_type_analysis": {{
        "comparison_insights": ["고닉/유동 의견 대조 분석"],
        "high_quality_posts": ["주요 정보성 게시글 요약"],
        "general_opinion": ["일반 유저층의 반응"]
      }},
      "global_category_summary": [
        {{ "category": "[긍정평가] 항목명", "summary": ["상세 요약"] }},
        {{ "category": "[부정평가] 항목명", "summary": ["상세 요약"] }}
      ]
    }}
    
    [수집된 데이터]:
    {post_data}
    """
