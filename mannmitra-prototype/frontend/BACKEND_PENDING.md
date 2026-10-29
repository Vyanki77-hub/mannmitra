# MannMitra Frontend — Backend Pending Register

This document tracks backend functionality identified during the frontend redesign (Step 2) that currently relies on client-side prototype state or mock data.

---

## Registered Items

| ID | Feature | Frontend Current State | Backend Functionality Required | Status / Endpoint | Priority | Usable in Prototype? |
|---|---|---|---|---|---|---|
| **BP-01** | Mood History & Persistence | Stored in browser memory / `sessionStorage`. Computes mock distribution and weekly calendar. | Secure CRUD endpoints for user mood check-ins (`/mood/log`, `/mood/history`), date-range filtering, and aggregation. | Missing | High | Yes (prototype demo state) |
| **BP-02** | Personal Intention Persistence | Saved in browser memory. Resets on reload. | Storage for daily wellness intentions (`/intention/current`, `/intention/history`). | Missing | Medium | Yes |
| **BP-03** | Guided Support Progress & State | Client-side 5-step guided journey player with interactive step tracking. | Endpoint to save journey progress, resume paused journeys, and log completion reflections (`/journeys/progress`). | Missing | Medium | Yes |
| **BP-04** | Relax & Breathe Session Logging | Client-side timer, phase cycling, and completion callback. | Logging completed minutes and sessions for wellness tracking (`/breathing/sessions`). | Missing | Low | Yes |
| **BP-05** | General Wellbeing Resources Search & RAG | Static categorized library of 14+ guides with client-side category filters and keyword search. | Dynamic search endpoint with vector embeddings or RAG retrieval for wellness articles (`/resources/search`, `/resources/articles`). | Current `/resources` returns only 4 LPU facts | Medium | Yes |
| **BP-06** | Resource Bookmarking / Favorites | Client-side toggle stored in memory. | User favorites persistence (`/resources/favorites`). | Missing | Low | Yes |
| **BP-07** | Campus (LPU) Verified Resource Metadata | Structured campus cards with verified locations, timings, and explicit "details to verify" flags. | Verified campus resource metadata API with verification source, last audit timestamp, and department contact updates (`/campus/resources`). | `/resources` exists but lacks category taxonomy & timestamps | Medium | Yes |
| **BP-08** | My Journey Timeline & Milestone Aggregation | Client-side activity timeline combining check-ins, breathing pauses, and reflection milestones. | Backend event aggregator computing activity timeline and milestone achievements (`/journey/timeline`, `/journey/milestones`). | Missing | Medium | Yes |
| **BP-09** | User Profile & Preferences Persistence | Theme, accent, greeting speech, speech rate, and display name stored in `localStorage`. | User preferences endpoint (`/user/profile`, `/user/preferences`) associated with authenticated session. | Missing | High | Yes (stored locally) |
| **BP-10** | Authentication & Student Identity | Mock login accepting any credentials or guest entry with default display name. | Secure LPU student email verification / SSO / token-based authentication (`/auth/login`, `/auth/refresh`). | Missing | High | Yes (demo prototype) |
| **BP-11** | Text Chat API (`/chat`) | Fully functional live POST to `http://127.0.0.1:8000/chat`. | Existing endpoint working properly with emotion-adaptive pipeline and safety overrides. | Implemented & Verified | Active | Yes |
| **BP-12** | Campus Facts API (`/resources`) | Live GET to `http://127.0.0.1:8000/resources`. | Returns array of campus facts from `knowledge/facts.json`. | Implemented & Verified | Active | Yes |

---

## Architectural Notes
- The frontend operates in **Full Standalone Prototype Mode**: all UI features (Mood Tracker, Guided Support, Breathing Exercises, Resources Library, Journey Timeline, and Settings) are fully interactive and functional in-browser without requiring backend modifications.
- Existing working endpoints (`/chat` and `/resources`) remain preserved and untouched.

