# RAG Update - Setup Guide

## What this adds
- Real retrieval-augmented generation (RAG), not just a system prompt
- A structured facts lookup for hard data (block numbers, contacts, deadlines)
- Semantic search (Chroma vector database) for open-ended FAQ questions
- The model is now instructed to say "I don't have verified info" instead of
  guessing, which directly fixes the "Block B" hallucination problem

## How to install this into your existing project

1. Copy `rag.py` and `ingest.py` into your `backend/` folder
2. Copy the `knowledge/` folder into `backend/knowledge/`
3. Replace your existing `backend/main.py` with the one here
4. Add `chromadb` to your `backend/requirements.txt`:
   ```
   chromadb
   ```
5. Install it:
   ```
   pip install -r requirements.txt
   ```

## THE MOST IMPORTANT STEP - replace the placeholder data

Every file in `knowledge/` and `facts.json` is currently filled with obvious
placeholder text. This was done deliberately - I do not have real, verified
LPU data, and putting invented details in would recreate the exact problem
your professor flagged. You must replace these with real information before
this is useful:

- `facts.json`: real block numbers, the real Division of Happiness and
  Wellbeing contact info (this one matters most), real hostel names, real
  deadlines
- `wellbeing_faqs.txt` and `academic_faqs.txt`: real paragraphs copied from
  actual LPU documents (handbook, official pages, department pamphlets)

This is exactly the "spend tomorrow collecting real data" step your professor
asked for. Go to the DSR office, the Wellbeing division, and the student
handbook, and gather what you can. Even a modest, accurate set beats a large,
invented one.

## Running it

1. After updating the knowledge files, run the ingestion script once:
   ```
   cd backend
   python ingest.py
   ```
   Re-run this any time you update the knowledge files.
2. Start your backend as normal:
   ```
   uvicorn main:app --reload
   ```
3. Test it: ask "where is the DSR office" - you should see it either answer
   from your real data, or honestly say it doesn't have verified info yet
   (if you haven't filled in that fact) - never a guessed answer like "Block B."

## Running the eval set

1. Make sure your backend is running (step 2 above)
2. In a separate terminal:
   ```
   cd eval
   pip install requests --break-system-packages
   python eval_runner.py
   ```
3. Read through the printed answers, and fill in the `expected_answer` fields
   in `eval_questions.json` with your real verified answers once you have them
4. This gives you the "accuracy before and after RAG" comparison your
   professor specifically asked for - screenshot or write up the before
   (guessed "Block B") vs after (accurate or honest "I don't know") difference

## Priority order for your remaining days (do not try to do everything)

Given your deadline, build in this order and stop when you run out of time -
each stage is a complete, demoable improvement on its own:

1. Collect real data and fill in facts.json + the two .txt files (highest priority)
2. Run ingest.py, confirm the DSR/Block B problem is actually fixed
3. Run the eval set, write down a few clear before/after examples for your demo
4. If time remains: add a small "source" note in the UI showing which document
   an answer came from (a simple text line under the bot's reply is enough,
   does not need to be fancy)
5. If time remains: run the adversarial test cases already included in
   eval_questions.json and note the results - this alone is a strong, fast
   thing to show your HOD, since it is mostly testing, not new engineering

Everything else your professor listed (human handoff queue, semantic caching,
multilingual support, admin analytics) is genuinely good, but explicitly
future work. Say so plainly in your presentation - naming it as "next steps"
is a completely reasonable and honest thing to do with four days left.
