import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def run_stratedge(business_name, industry, target_audience, goals, budget):

    prompt = f"""
You are StratEdge, an expert AI marketing strategist. A small business owner has provided the following information:

Business Name: {business_name}
Industry: {industry}
Target Audience: {target_audience}
Primary Goal: {goals}
Monthly Marketing Budget: {budget}

Your job is to:
1. Search the web for current market trends relevant to this business's industry and target audience
2. Use those trends combined with your marketing expertise to generate a complete, actionable marketing strategy

Structure your response with these exact sections:
## 📊 Current Market Trends
(3 trends pulled from live data relevant to their industry)

## 🎯 Brand Positioning
(Recommended market position and unique value proposition)

## 👥 Target Audience Profile
(Refined ideal customer description)

## 📣 Recommended Channels
(Prioritized list with rationale for each)

## 📝 Content Strategy
(Post types, messaging angles, tone, frequency)

## 💰 Budget Allocation
(Suggested spend breakdown across channels)

## 📈 KPIs to Track
(3-5 measurable metrics)

Be specific, actionable, and realistic for a small business with the given budget.
"""

    response = client.responses.create(
        model="gpt-4o",
        tools=[{"type": "web_search_preview"}],
        input=[{"role": "user", "content": prompt}]
    )

    return response.output_text