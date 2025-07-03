# Background and Motivation
The goal is to build a mobile-first Streamlit web app called "Max Fosh Silly Idea Generator". The app generates silly, absurd, and creative YouTube video ideas in the style of Max Fosh. Users select the type of video (prank, bet, challenge) and whether they want to do it alone, with friends, or make new friends, then press a big red button to get a new idea. The idea is generated using OpenAI's chat/completions API, with context/examples retrieved from an OpenAI vector store populated with Max Fosh video summaries. The app is optimized for mobile, has robust error handling, and is intended for deployment on Streamlit Cloud.

# Key Challenges and Analysis
- Building a clean, mobile-first UI in Streamlit with selectable user inputs and a large, visually prominent red button.
- Correctly querying the OpenAI vector store (ID: vs_6866aa446308819187b81e38daa71954) for the top 3 semantically relevant examples, using both user selections as part of the query.
- Constructing a prompt for the LLM that incorporates the user's selections and the retrieved examples, and instructs the LLM to generate a new idea with an actionable execution plan.
- Handling API errors, timeouts (30s), and rapid button clicks (debounce).
- Falling back to 3 random local examples from maxfosh_summaries/ if the vector store query fails.
- Displaying only the generated idea (title, description, execution plan) in a card-style, mobile-optimized format.
- Managing secrets via st.secrets and ensuring compatibility with Streamlit Cloud.

# High-level Task Breakdown
1. **Set Up Streamlit App Structure**
   - [ ] Create app.py with Streamlit imports and basic layout.
   - [ ] Add page title and center content.
   - Success: App runs and displays a centered title.
2. **Add User Input Controls**
   - [ ] Add two selectboxes: "Type of video?" (prank, bet, challenge) and "Mates?" (alone, my friends, make new friends).
   - Success: User can select options before pressing the button.
3. **Add Big Red Button and Loading State**
   - [ ] Add a large, centered red button labeled "Go on then".
   - [ ] Show a loading spinner when generating an idea.
   - [ ] Prevent rapid clicks and enforce a 30s timeout.
   - Success: Button is visually prominent, disables on click, and spinner appears.
4. **Query OpenAI Vector Store**
   - [ ] On button click, query the vector store (ID: vs_6866aa446308819187b81e38daa71954) for 3 relevant examples using user selections in the query string.
   - [ ] Extract title, description, style, payoff, summary from each result (fallback to 'unknown' if missing).
   - Success: Receive 3 valid examples or trigger fallback.
5. **Fallback to Local Examples**
   - [ ] If vector store query fails, randomly select 3 JSON files from maxfosh_summaries/.
   - [ ] Parse and extract required fields from these files.
   - Success: 3 examples are available for prompt construction.
6. **Construct LLM Prompt**
   - [ ] Build a prompt that includes the 3 examples and explicitly references the user's selections (type and mates).
   - [ ] Instruct the LLM to generate a new idea with title, description, and actionable execution plan.
   - Success: Prompt is well-formed and includes all required context.
7. **Call OpenAI Chat/Completions API**
   - [ ] Use gpt-4 or gpt-3.5-turbo with temperature 0.9 to generate the idea.
   - [ ] Handle API errors and timeouts.
   - Success: Receive a valid response or show "Try again" message.
8. **Display Output**
   - [ ] Show the generated idea in a card-style format: title (bold, large), description (italic, medium), execution plan (normal paragraph).
   - [ ] Ensure layout is mobile-optimized and centered.
   - Success: Output is visually appealing and readable on mobile.
9. **Secrets and Deployment**
   - [ ] Use st.secrets for OPENAI_API_KEY and vector store ID.
   - [ ] Ensure app is ready for Streamlit Cloud deployment.
   - Success: App runs with secrets and is cloud-ready.
10. **Robustness and Error Handling**
    - [ ] Log errors, handle missing fields, and ensure the app never crashes.
    - [ ] Show "Try again" message on failure.
    - Success: App is robust and user-friendly.

# Project Status Board
- [x] Set up Streamlit app structure
- [x] Add user input controls
- [x] Add big red button and loading state
- [x] Query OpenAI vector store
- [x] Fallback to local examples
- [x] Construct LLM prompt
- [x] Call OpenAI completions API
- [x] Display output
- [x] Handle secrets and deployment
- [x] Robustness and error handling

## Executor's Feedback or Assistance Requests
- The app now handles missing secrets, missing fallback directory, and all major errors gracefully, always showing a 'Try again' message if something goes wrong. Implementation is complete and ready for Planner review and user testing.

# Lessons
- (To be filled as implementation progresses)

# Background and Motivation
The goal of the Scraper.py script is to automate the extraction and summarization of Max Fosh's 50 most popular YouTube videos. The output will be structured metadata (summary, comedic style, twist/payoff, title, description) for each video, saved as individual JSON files. These files will be used in a downstream OpenAI vector store project for idea generation.

# Key Challenges and Analysis
- Correctly interfacing with the Apify YouTube Scraper actor to get the top 50 videos by view count.
- Handling API rate limits and errors from Apify, YouTube, and OpenAI.
- Ensuring transcripts are retrieved for each video (handling missing or unavailable transcripts).
- Prompting OpenAI to reliably extract the required fields in structured JSON.
- Outputting exactly 50 JSON files, named 0001.json to 0050.json, with all required fields.
- Ensuring the script is robust and can be rerun without duplicating or overwriting data incorrectly.

# High-level Task Breakdown
1. **Integrate Apify YouTube Scraper**
   - [ ] Call Apify API to get the 50 most popular videos from Max Fosh's channel, sorted by view count.
   - Success: Receive a list of 50 video objects with title, description, and videoId.
2. **Retrieve Transcripts**
   - [ ] For each video, use youtube-transcript-api to fetch the full transcript.
   - Success: Transcript text is available for each video (handle missing transcripts gracefully).
3. **Summarize with OpenAI**
   - [ ] For each video, send title, description, and transcript to OpenAI Chat API (gpt-3.5-turbo) with a prompt to extract summary, comedic style, and twist/payoff.
   - Success: Receive a valid JSON response with the required fields for each video.
4. **Output JSON Files**
   - [ ] Write the structured metadata (title, description, summary, style, payoff) to 50 individual JSON files named 0001.json, 0002.json, ..., 0050.json.
   - Success: All files are present, correctly named, and contain the required fields.
5. **Robustness and Error Handling**
   - [ ] Ensure the script can handle API errors, missing transcripts, and can be rerun safely.
   - Success: Script completes without crashing and logs/handles errors appropriately.

# Project Status Board
- [x] Integrate local JSON for 150 videos as input
- [x] Retrieve transcripts for each video
- [x] Summarize each video with OpenAI (description, summary, style, payoff)
- [x] Output 150 structured JSON files
- [ ] User to verify output and request further changes or enhancements

## Executor's Feedback or Assistance Requests
- The script now reads all 150 videos from the provided JSON, fetches transcripts, generates description/summary/style/payoff using OpenAI, and outputs 0001.json to 0150.json. Please run the script and verify the output. Let me know if you need further changes or enhancements. 