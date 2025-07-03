import streamlit as st
import time
import openai
import os
import random
import json
import re

st.set_page_config(page_title="Max Fosh Silly Idea Generator", layout="centered")

st.markdown("""
# Max Fosh Silly Idea Generator
""", unsafe_allow_html=True)

# Robustness: Check for required secrets
if "OPENAI_VECTOR_STORE_ID" not in st.secrets or "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing required secrets. Please set OPENAI_VECTOR_STORE_ID and OPENAI_API_KEY in Streamlit Cloud.")
    st.stop()

# User input controls
video_type = st.selectbox(
    "Type of video?",
    ["prank", "bet", "challenge"],
    index=0,
    key="video_type"
)

mates = st.selectbox(
    "Mates?",
    ["alone", "my friends", "make new friends"],
    index=0,
    key="mates"
)

# Session state for button and timeout
if 'loading' not in st.session_state:
    st.session_state['loading'] = False
if 'last_click' not in st.session_state:
    st.session_state['last_click'] = 0
if 'error' not in st.session_state:
    st.session_state['error'] = False
if 'examples' not in st.session_state:
    st.session_state['examples'] = None
if 'used_fallback' not in st.session_state:
    st.session_state['used_fallback'] = False
if 'llm_prompt' not in st.session_state:
    st.session_state['llm_prompt'] = None
if 'llm_response' not in st.session_state:
    st.session_state['llm_response'] = None
if 'parsed_idea' not in st.session_state:
    st.session_state['parsed_idea'] = None


def on_button_click():
    now = time.time()
    if st.session_state['loading'] and now - st.session_state['last_click'] < 30:
        return
    st.session_state['loading'] = True
    st.session_state['last_click'] = now
    st.session_state['error'] = False
    st.session_state['examples'] = None
    st.session_state['used_fallback'] = False
    st.session_state['llm_prompt'] = None
    st.session_state['llm_response'] = None
    st.session_state['parsed_idea'] = None

# Center the button using columns
col1, col2, col3 = st.columns([1,2,1])
with col2:
    button = st.button(
        "Go on then",
        key="go_button",
        help="Generate a silly idea!",
        use_container_width=True,
        on_click=on_button_click,
        disabled=st.session_state['loading']
    )

# Vector store query logic
VECTOR_STORE_ID = st.secrets["OPENAI_VECTOR_STORE_ID"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

openai.api_key = OPENAI_API_KEY

FALLBACK_DIR = "maxfosh_summaries"


def fetch_vector_examples(video_type, mates):
    query = f"Max Fosh-style video, type: {video_type}, mates: {mates}"
    try:
        response = openai.beta.vector_stores.query(
            vector_store_id=VECTOR_STORE_ID,
            query=query,
            top_k=3
        )
        examples = []
        for item in response["data"]:
            metadata = item.get("metadata", {})
            examples.append({
                "title": metadata.get("title", "unknown"),
                "description": metadata.get("description", "unknown"),
                "style": metadata.get("style", "unknown"),
                "payoff": metadata.get("payoff", "unknown"),
                "summary": metadata.get("summary", "unknown")
            })
        return examples
    except Exception as e:
        return None

def fetch_fallback_examples():
    try:
        if not os.path.isdir(FALLBACK_DIR):
            return None
        files = [f for f in os.listdir(FALLBACK_DIR) if f.endswith('.json')]
        if len(files) < 3:
            return None
        chosen = random.sample(files, 3)
        examples = []
        for fname in chosen:
            with open(os.path.join(FALLBACK_DIR, fname), 'r') as f:
                data = json.load(f)
                examples.append({
                    "title": data.get("title", "unknown"),
                    "description": data.get("description", "unknown"),
                    "style": data.get("style", "unknown"),
                    "payoff": data.get("payoff", "unknown"),
                    "summary": data.get("summary", "unknown")
                })
        return examples
    except Exception as e:
        return None

def build_llm_prompt(examples, video_type, mates):
    prompt = (
        "You are Max Fosh, a YouTube creator who makes absurd, legally-doable YouTube video concepts. You started your career 7 years ago creating street interview content.\n Since then you've gone on to create bigger and better content which has gained you over 4 million youtuber subscriber sand 490K Instagram followers. You've been invited to work with other massive creators for example you were invited to the sidemen chartiy football match, you've worked with Michelle Khere and collaborated with Mr Beast on videos. You regularly get invited to present awards at large events and have a huge network and influencer. "
        f"The user wants a {video_type} video and to do it {mates}.\n\n"
        "Here are some examples:\n\n"
    )
    for ex in examples:
        prompt += (
            f"---\nTitle: {ex['title']}  \nDescription: {ex['description']}  \nPayoff: {ex['payoff']}  \nStyle: {ex['style']}  \nSummary: {ex['summary']}\n\n"
        )
    prompt += (
        "---\n\nNow, generate a brand-new idea in the same style. Be creative, surprising, and mischievous — but realistic and legally possible.\n\n"
        "Return in this format:\nTitle:\nDescription:\nExecution Plan:"
    )
    return prompt

# Call OpenAI completions API
def call_llm(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=512,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        # Fallback to gpt-3.5-turbo
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=512,
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e2:
            return None

def parse_llm_response(response):
    # Try to extract Title, Description, Execution Plan using regex
    title = description = plan = ""
    if response:
        title_match = re.search(r"Title:\s*(.*)", response)
        description_match = re.search(r"Description:\s*(.*)", response)
        plan_match = re.search(r"Execution Plan:\s*([\s\S]*)", response)
        if title_match:
            title = title_match.group(1).strip()
        if description_match:
            description = description_match.group(1).strip()
        if plan_match:
            plan = plan_match.group(1).strip()
    return {"title": title, "description": description, "plan": plan}

if st.session_state['loading']:
    with st.spinner('Generating your idea...'):
        try:
            examples = fetch_vector_examples(video_type, mates)
            if examples:
                st.session_state['examples'] = examples
                st.session_state['used_fallback'] = False
            else:
                fallback_examples = fetch_fallback_examples()
                if fallback_examples:
                    st.session_state['examples'] = fallback_examples
                    st.session_state['used_fallback'] = True
                else:
                    st.session_state['examples'] = None
                    st.session_state['error'] = True
            # Build LLM prompt if examples available
            if st.session_state['examples']:
                st.session_state['llm_prompt'] = build_llm_prompt(
                    st.session_state['examples'], video_type, mates
                )
                # Call LLM
                llm_response = call_llm(st.session_state['llm_prompt'])
                if llm_response:
                    st.session_state['llm_response'] = llm_response
                    st.session_state['parsed_idea'] = parse_llm_response(llm_response)
                else:
                    st.session_state['llm_response'] = None
                    st.session_state['parsed_idea'] = None
                    st.session_state['error'] = True
        except Exception as e:
            st.session_state['examples'] = None
            st.session_state['llm_prompt'] = None
            st.session_state['llm_response'] = None
            st.session_state['parsed_idea'] = None
            st.session_state['error'] = True
        st.session_state['loading'] = False

if st.session_state['error']:
    st.error("Try again")

# Display the generated idea in card format
if st.session_state['parsed_idea'] and st.session_state['parsed_idea']['title']:
    st.markdown(
        f"""
        <div style='background-color:#fff3e6; border-radius:16px; padding:2em 1em; margin:2em 0; box-shadow:0 2px 8px rgba(0,0,0,0.07); text-align:center;'>
            <h2 style='color:#b30000; margin-bottom:0.5em;'>{st.session_state['parsed_idea']['title']}</h2>
            <div style='font-style:italic; font-size:1.1em; margin-bottom:1em;'>{st.session_state['parsed_idea']['description']}</div>
            <div style='font-size:1em; text-align:left; max-width:500px; margin:0 auto;'><b>Execution Plan:</b><br>{st.session_state['parsed_idea']['plan']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Debug: Show fetched examples
# (Uncomment for troubleshooting)
# if st.session_state['examples']:
#     if st.session_state['used_fallback']:
#         st.markdown("## Debug: Fallback Local Examples")
#     else:
#         st.markdown("## Debug: Vector Store Examples")
#     for i, ex in enumerate(st.session_state['examples'], 1):
#         st.markdown(f"**Example {i}:**")
#         st.json(ex)

# Debug: Show constructed LLM prompt
# if st.session_state['llm_prompt']:
#     st.markdown("## Debug: LLM Prompt")
#     st.code(st.session_state['llm_prompt'])

# Debug: Show LLM response
# if st.session_state['llm_response']:
#     st.markdown("## Debug: LLM Response")
#     st.code(st.session_state['llm_response'])

# Placeholder for future UI elements 