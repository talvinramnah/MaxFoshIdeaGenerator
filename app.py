import streamlit as st
import time
import openai
import os
import random
import json
import re
import logging
st.set_page_config(page_title="Max Fosh Silly Video Idea Generator", layout="centered")

# Inject Caveat font globally
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Caveat:wght@700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="css"]  {
        font-family: 'Caveat', cursive !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("""
# Max Fosh Silly Video Idea Generator
""", unsafe_allow_html=True)

# Set up logging to a file for debugging
logging.basicConfig(filename='app_debug.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Robustness: Check for required secrets
if "OPENAI_API_KEY" not in st.secrets:
    st.error("Missing required secret: OPENAI_API_KEY. Please set it in Streamlit Cloud.")
    logging.error("Missing required secret: OPENAI_API_KEY.")
    st.stop()

# User input controls (now radio buttons)
video_type = st.radio(
    "Type of video?",
    ["prank", "social experiment", "challenge"],
    index=0,
    key="video_type"
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
    st.session_state['loading'] = True
    st.session_state['error'] = False
    st.session_state['examples'] = None
    st.session_state['used_fallback'] = False
    st.session_state['llm_prompt'] = None
    st.session_state['llm_response'] = None
    st.session_state['parsed_idea'] = None
    logging.info("Button clicked. Starting generation flow.")

# Center the button using columns
col1, col2, col3 = st.columns([1,2,1])
with col2:
    button = st.button(
        "Go on then, you silly billy",
        key="go_button",
        help="Generate a silly idea!",
        use_container_width=True,
        on_click=on_button_click,
        disabled=st.session_state['loading'],
        type="primary"
    )

# Vector store query logic
VECTOR_STORE_ID = "vs_6866aa446308819187b81e38daa71954"
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

openai.api_key = OPENAI_API_KEY

FALLBACK_DIR = "maxfosh_summaries"

spinner_phrases = [
    'shredding yellow card',
    'setting up lemonade stand',
    'winning oscar',
    'buying roundabout',
    'signing a will',
    'performing at apollo',
    'breaking into security convention',
    'talking to parrot',
    'gambling with horse'
]

def fetch_vector_examples(video_type):
    query = f"Max Fosh-style video, type: {video_type}"
    try:
        logging.info(f"Querying vector store with: {query}")
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
        logging.info(f"Vector store returned {len(examples)} examples.")
        return examples
    except Exception as e:
        logging.error(f"Vector store query failed: {e}")
        return None

def fetch_fallback_examples():
    try:
        if not os.path.isdir(FALLBACK_DIR):
            st.error(f"Fallback directory {FALLBACK_DIR} does not exist.")
            logging.error(f"Fallback directory {FALLBACK_DIR} does not exist.")
            return None
        files = [f for f in os.listdir(FALLBACK_DIR) if f.endswith('.json')]
        if len(files) < 3:
            st.error(f"Not enough fallback files in {FALLBACK_DIR}. Found: {len(files)}")
            logging.error(f"Not enough fallback files in {FALLBACK_DIR}.")
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
        logging.info(f"Loaded {len(examples)} fallback examples.")
        return examples
    except Exception as e:
        st.error(f"Fallback example loading failed: {e}")
        logging.error(f"Fallback example loading failed: {e}")
        return None

def build_llm_prompt(examples, video_type):
    try:
        prompt = (
            "You are Max Fosh, a YouTube creator who makes absurd, legally-doable YouTube video concepts. You started your career 7 years ago creating street interview content.\n Since then you've gone on to create bigger and better content which has gained you over 4 million youtuber subscribers and 490K Instagram followers. You've been invited to work with other massive creators for example you were invited to the sidemen charity football match, you've worked with Michelle Khere and collaborated with Mr Beast on videos. You regularly get invited to present awards at large events and have a huge network and influencer. "
            f"The user wants a {video_type} video.\n\n"
            "Here are some examples:\n\n"
        )
        for ex in examples:
            prompt += (
                f"---\nTitle: {ex['title']}  \nDescription: {ex['description']}  \nPayoff: {ex['payoff']}  \nStyle: {ex['style']}  \nSummary: {ex['summary']}\n\n"
            )
        prompt += (
            "---\n\nNow, generate a brand-new idea in the same style. Be creative, surprising, and mischievous — but realistic and legally possible.\n\n"
            "Return in this format:\nTitle:\nDescription:"
        )
        logging.info("LLM prompt built successfully.")
        return prompt
    except Exception as e:
        logging.error(f"LLM prompt build failed: {e}")
        return ""

# Call OpenAI completions API
def call_llm(prompt):
    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"OpenAI API call failed: {e}")
        logging.error(f"gpt-4 call failed: {e}")
        # Fallback to gpt-3.5-turbo
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=512,
            )
            return response.choices[0].message.content
        except Exception as e2:
            st.error(f"OpenAI API fallback call failed: {e2}")
            logging.error(f"gpt-3.5-turbo call failed: {e2}")
            return None

def parse_llm_response(response):
    try:
        title = description = ""
        if response:
            title_match = re.search(r"Title:\s*(.*)", response)
            description_match = re.search(r"Description:\s*(.*)", response)
            if title_match:
                title = title_match.group(1).strip()
            if description_match:
                description = description_match.group(1).strip()
        logging.info(f"Parsed LLM response: title='{title}', description='{description}'")
        return {"title": title, "description": description}
    except Exception as e:
        logging.error(f"LLM response parsing failed: {e}")
        return {"title": "", "description": ""}

if st.session_state['loading']:
    spinner_text = random.choice(spinner_phrases)
    with st.spinner(spinner_text):
        try:
            logging.info("--- Generation flow started ---")
            examples = fetch_vector_examples(video_type)
            if examples:
                st.session_state['examples'] = examples
                st.session_state['used_fallback'] = False
                logging.info("Used vector store examples.")
            else:
                fallback_examples = fetch_fallback_examples()
                if fallback_examples:
                    st.session_state['examples'] = fallback_examples
                    st.session_state['used_fallback'] = True
                    logging.info("Used fallback local examples.")
                else:
                    st.session_state['examples'] = None
                    st.session_state['error'] = True
                    logging.error("No examples available from vector store or fallback.")
                    st.error("No examples available from vector store or fallback.")
            # Build LLM prompt if examples available
            if st.session_state['examples']:
                st.session_state['llm_prompt'] = build_llm_prompt(
                    st.session_state['examples'], video_type
                )
                # Call LLM
                llm_response = call_llm(st.session_state['llm_prompt'])
                if llm_response:
                    st.session_state['llm_response'] = llm_response
                    st.session_state['parsed_idea'] = parse_llm_response(llm_response)
                    logging.info("LLM call and parsing succeeded.")
                else:
                    st.session_state['llm_response'] = None
                    st.session_state['parsed_idea'] = None
                    st.session_state['error'] = True
                    logging.error("LLM call failed.")
                    st.error("LLM call failed.")
            st.session_state['loading'] = False
            st.rerun()
        except Exception as e:
            st.session_state['examples'] = None
            st.session_state['llm_prompt'] = None
            st.session_state['llm_response'] = None
            st.session_state['parsed_idea'] = None
            st.session_state['error'] = True
            logging.error(f"Exception in generation flow: {e}")
            st.error(f"Exception in generation flow: {e}")
            st.session_state['loading'] = False
            st.rerun()

if st.session_state['error']:
    st.error("Try again")
    st.write("Debug info:", st.session_state)
    logging.info("Displayed 'Try again' to user.")

# Display the generated idea in card format
if st.session_state['parsed_idea'] and st.session_state['parsed_idea']['title']:
    st.markdown(
        f"""
        <div style='background-color:#fff3e6; border-radius:16px; padding:2em 1em; margin:2em 0; box-shadow:0 2px 8px rgba(0,0,0,0.07); text-align:center;'>
            <h2 style='color:#b30000; margin-bottom:0.5em;'>{st.session_state['parsed_idea']['title']}</h2>
            <div style='font-style:italic; font-size:1.1em; margin-bottom:1em;'>{st.session_state['parsed_idea']['description']}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    logging.info("Displayed generated idea card to user.")

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

st.markdown(
    """
    <style>
    /* Style the primary button */
    div.stButton > button {
        background-color: #d14b4b !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 1.3em !important;
        font-family: 'Caveat', cursive !important;
        padding: 0.5em 2em !important;
        transition: background 0.2s;
    }
    div.stButton > button:hover {
        background-color: #b30000 !important;
        color: #fff !important;
    }
    </style>
    """,
    unsafe_allow_html=True
) 