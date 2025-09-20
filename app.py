import os
import re
import sys
import io
import math
import uuid
import random
import importlib
import streamlit as st
from streamlit.components.v1 import html

# =========================
# Page config
# =========================
st.set_page_config(page_title="AI Study Buddy", layout="wide")

# =========================
# Lazy import of utils (prevents blank screen on errors)
# =========================
UTILS_ERROR = None
generate_summary = generate_flashcards = generate_quiz = None
try:
    _utils = importlib.import_module("utils")
    generate_summary = getattr(_utils, "generate_summary")
    generate_flashcards = getattr(_utils, "generate_flashcards")
    generate_quiz = getattr(_utils, "generate_quiz")
except Exception as e:
    UTILS_ERROR = f"{e.__class__.__name__}: {e}"

# =========================
# Global Styles (Pro look & feel)
# =========================
st.markdown("""
<style>
/* App background & base */
.stApp {
  background: radial-gradient(1200px 600px at 10% 5%, #1f2330 0%, #0e1117 45%) fixed;
  color: #e6e6e6;
  font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans", sans-serif;
}
* { transition: background-color .2s ease, color .2s ease, border-color .2s ease; }

/* Top hero/header */
.header-card {
  margin: 0 0 14px 0; padding: 18px 22px; border-radius: 18px;
  background: linear-gradient(135deg, rgba(99,102,241,.12), rgba(56,189,248,.12));
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 8px 24px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.05);
}
.header-title {
  display:flex; align-items:center; gap:12px; font-weight:700; letter-spacing:.3px;
  font-size: 24px;
}
.header-badge {
  font-size:11px; padding:4px 8px; border-radius:999px;
  background: rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14);
}
.header-sub { margin-top:6px; opacity:.85; }

/* Section card */
.section {
  padding: 14px 16px; border-radius: 16px; margin-top: 10px;
  background: rgba(255,255,255,.03);
  border: 1px solid rgba(255,255,255,.08);
  box-shadow: 0 10px 24px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.04);
}

/* Tab headers */
[data-baseweb="tab-list"] { gap: 6px; }
[data-baseweb="tab"] {
  border-radius: 10px !important;
  background: rgba(255,255,255,.02);
  border: 1px solid transparent;
}
[data-baseweb="tab"][aria-selected="true"] {
  background: rgba(99,102,241,.18);
  border-color: rgba(99,102,241,.35);
}

/* Buttons */
.stButton>button {
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,.18);
  padding: 8px 14px;
  background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.03));
  color: #e6e6e6;
}
.stButton>button:hover { filter: brightness(1.08); }

/* Inputs */
.stTextInput>div>div>input, .stNumberInput input {
  border-radius: 10px !important;
}

/* Table */
.stTable {
  border-radius: 12px; overflow: hidden;
  border: 1px solid rgba(255,255,255,.08);
}
</style>
""", unsafe_allow_html=True)

# =========================
# Header (brandable)
# =========================
st.markdown("""
<div class="header-card">
  <div class="header-title">
    <span>📘 AI Study Buddy</span>
    <span class="header-badge">v1.0 • Pro UI</span>
  </div>
  <div class="header-sub">
    Generate a high-quality summary, a clean visual map, and interactive flashcards & quizzes — all in one polished interface.
  </div>
</div>
""", unsafe_allow_html=True)

# =========================
# Sidebar: settings
# =========================
st.sidebar.header("Settings")
topic = st.sidebar.text_input("Enter a topic", "Human behavior")
flashcard_count = st.sidebar.number_input("Number of flashcards", min_value=1, max_value=50, value=10, step=1)
quiz_count = st.sidebar.number_input("Number of MCQs", min_value=1, max_value=50, value=10, step=1)

st.sidebar.subheader("Flashcard Layout")
card_height = st.sidebar.slider("Card height (px)", 140, 300, 190, 10)
min_card_width = st.sidebar.slider("Min card width (px)", 220, 380, 270, 10)
grid_gap = st.sidebar.slider("Grid gap (px)", 8, 28, 16, 2)

generate_button = st.sidebar.button("✨ Generate / Refresh")

with st.sidebar.expander("⚙️ Health check", expanded=False):
    st.write({
        "python_version": sys.version.split()[0],
        "utils_import_ok": UTILS_ERROR is None,
        "env_openai_key_present": bool(os.getenv("OPENAI_API_KEY")),
    })
    if UTILS_ERROR:
        st.error(UTILS_ERROR)

if UTILS_ERROR:
    st.stop()

# =========================
# Session state
# =========================
ss = st.session_state
ss.setdefault("generated_topic", None)
ss.setdefault("summary", "")
ss.setdefault("flashcards", [])
ss.setdefault("quiz", [])
ss.setdefault("answers", {})
ss.setdefault("score", 0)
ss.setdefault("flashcard_count", flashcard_count)
ss.setdefault("quiz_count", quiz_count)
ss.setdefault("flashcards_order", [])
ss.setdefault("quiz_epoch", 0)   # bump to force radios to reset

# =========================
# Generate content (summary anchors flashcards/MCQs)
# =========================
if generate_button:
    with st.spinner("Generating content…"):
        if topic != ss.generated_topic or not ss.summary:
            ss.summary = generate_summary(topic)
            ss.generated_topic = topic
        ss.flashcards = generate_flashcards(topic, n=flashcard_count, summary=ss.summary)
        ss.quiz = generate_quiz(topic, n=quiz_count, summary=ss.summary)
        ss.answers = {f"quiz_{i}": None for i in range(len(ss.quiz))}
        ss.flashcard_count = flashcard_count
        ss.quiz_count = quiz_count
        ss.flashcards_order = list(range(len(ss.flashcards)))
        ss.quiz_epoch += 1  # ensure MCQs start unselected
    st.success("Done! Content updated.")

# =========================
# Helpers: summary → diagram
# =========================
def _strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "")

def _split_paragraphs(summary_html):
    paras = re.findall(r"<p[^>]*>(.*?)</p>", summary_html or "", flags=re.S)
    if not paras:
        paras = [p.strip() for p in (summary_html or "").split("\n\n") if p.strip()]
    return [_strip_html(p).strip() for p in paras[:3]]

def _sentences(s):
    return [p.strip() for p in re.split(r"(?<=[.!?])\\s+", (s or "").strip()) if p.strip()]

def _shorten(sentence, max_words=12):
    words = (sentence or "").split()
    return " ".join(words[:max_words]) + ("…" if len(words) > max_words else "")

def _wrap_label(text, max_len=24):
    words, lines, line = (text or "").split(), [], ""
    for w in words:
        if len(line) + len(w) + (1 if line else 0) <= max_len:
            line = (line + " " + w).strip()
        else:
            lines.append(line); line = w
    if line: lines.append(line)
    return "\\n".join(lines)

def build_summary_dot(topic, summary_html, leaves_per_para=4, wrap_len=24, orientation="TB"):
    paras = _split_paragraphs(summary_html)
    heads = [
        "Definition & Building Blocks",
        "Architecture • Security • Ops",
        "Use Cases • Benefits • Costs",
    ]
    g = [
        "digraph G {",
        f'graph [rankdir={orientation}, splines=true, overlap=false, nodesep=0.4, ranksep=0.7, margin=0.1];',
        'node [shape=box, style=filled, fillcolor="#111827", color="#3b82f6", fontname="Helvetica", fontsize=11, fontcolor="#e5e7eb"];',
        f'root [label="{_wrap_label(topic, wrap_len)}", shape=oval, fillcolor="#1f2937", fontsize=14, penwidth=2, color="#60a5fa"];',
    ]
    for i, head in enumerate(heads):
        bid = f"b{i}"
        g.append(f'{bid} [label="{_wrap_label(head, wrap_len)}", fillcolor="#0b1320", fontsize=12, color="#93c5fd"];')
        g.append(f"root -> {bid};")
        if i < len(paras):
            sents = _sentences(paras[i])[:leaves_per_para]
            for j, sent in enumerate(sents):
                lid = f"l{i}_{j}"
                g.append(f'{lid} [label="{_wrap_label(_shorten(sent, 12), wrap_len)}", fillcolor="#0f172a", color="#334155"];')
                g.append(f"{bid} -> {lid};")
    g.append("}")
    return "\n".join(g)

# CSV helper (avoids backslashes inside f-strings)
def csv_escape(text):
    """Escape double quotes and flatten newlines for CSV."""
    return (text or "").replace('"', '""').replace("\n", " ").strip()

# =========================
# FLASHCARDS UI (flip cards) — colorful + safe (no f-string braces)
# =========================
def render_flip_cards(cards, min_width_px=270, height_px=190, gap_px=16, search_query="", order=None):
    if order is None:
        order = list(range(len(cards)))

    # filter by search term
    def _match(c):
        blob = (c.get("question","") + " " + c.get("answer","")).lower()
        return search_query.lower() in blob if search_query else True

    filtered_idx = [i for i in order if _match(cards[i])]
    cards = [cards[i] for i in filtered_idx]

    cols_guess = max(1, math.floor(1000 / (min_width_px + gap_px)))
    rows_est = math.ceil(len(cards) / max(1, cols_guess))
    container_height = min(950, max(380, rows_est * (height_px + gap_px) + 160))

    def esc(s):
        return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    items = []
    for i, c in enumerate(cards, start=1):
        q = esc(c.get("question", f"Question {i}"))
        a = esc(c.get("answer", ""))
        gcls = f"fc-front-{(i % 5) or 5}"
        items.append(f"""
        <div class="fc-card" role="button" tabindex="0" aria-label="Flip card {i}">
          <div class="fc-card-inner">
            <div class="fc-card-face fc-front {gcls}">
              <div class="fc-pill">Q{i}</div>
              <div class="fc-text">{q}</div>
              <div class="fc-hint">Click / Space</div>
            </div>
            <div class="fc-card-face fc-back">
              <div class="fc-pill fc-pill--answer">Answer</div>
              <div class="fc-text">{a}</div>
              <div class="fc-hint">Click to flip back</div>
            </div>
          </div>
        </div>
        """)

    items_joined = "".join(items)
    root_id = f"fc-root-{uuid.uuid4().hex[:8]}"

    # Include palette CSS inside the iframe so colors render
    html_code = """
    <style>
      .fc-front-1{background:linear-gradient(135deg,#b3e5fc,#81d4fa);}
      .fc-front-2{background:linear-gradient(135deg,#f8bbd0,#f48fb1);}
      .fc-front-3{background:linear-gradient(135deg,#fff59d,#fff176);}
      .fc-front-4{background:linear-gradient(135deg,#dcedc8,#aed581);}
      .fc-front-5{background:linear-gradient(135deg,#ffcc80,#ffb74d);}
      .fc-front-1,.fc-front-2,.fc-front-3,.fc-front-4,.fc-front-5{ color:#0e1117; }

      .fc-wrap { max-height: __CONTH__px; overflow:auto; padding:8px 6px 14px 6px;
        border-radius:14px; border:1px solid rgba(255,255,255,.08);
        background: rgba(255,255,255,.03); box-shadow: inset 0 1px 0 rgba(255,255,255,.04); }
      .fc-toolbar { display:flex; gap:10px; margin:8px 6px 12px 6px; align-items:center; flex-wrap:wrap; }
      .fc-btn { border:1px solid rgba(255,255,255,.18);
        background:linear-gradient(180deg, rgba(255,255,255,.10), rgba(255,255,255,.04));
        padding:6px 12px; border-radius:10px; cursor:pointer; user-select:none; font-size:13px; }
      .fc-btn:hover { filter:brightness(1.06); }
      .fc-meta { opacity:.75; font-size:12px; }

      .fc-grid { display:grid; gap: __GAP__px;
        grid-template-columns: repeat(auto-fit, minmax(__MINW__px, 1fr)); }

      .fc-card { perspective:1100px; height: __HEIGHT__px; cursor:pointer; }
      .fc-card-inner { position:relative; width:100%; height:100%;
        transition:transform .5s cubic-bezier(.2,.7,.2,1); transform-style:preserve-3d;
        border-radius:16px; box-shadow: 0 10px 28px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.05); }
      .fc-card.is-flipped .fc-card-inner { transform: rotateY(180deg); }

      .fc-card-face { position:absolute; inset:0; display:flex; flex-direction:column;
        align-items:center; justify-content:center; text-align:center; padding:18px;
        border-radius:16px; backface-visibility:hidden; border:1px solid rgba(0,0,0,.08); }

      .fc-back { transform: rotateY(180deg); background:linear-gradient(135deg,#e8f5e9,#c8e6c9); color:#0e1117; }

      .fc-pill { font-weight:700; font-size:12px; padding:4px 10px; border-radius:999px;
        background:rgba(255,255,255,.86); color:#0e1117; margin-bottom:10px; border:1px solid rgba(0,0,0,.08); }
      .fc-text { font-size:16px; line-height:1.4; }
      .fc-hint { margin-top:10px; font-size:12px; opacity:.6; }
    </style>

    <div id="__ROOT__" class="fc-root">
      <div class="fc-wrap">
        <div class="fc-toolbar">
          <div class="fc-btn" id="flipAll">Flip all</div>
          <div class="fc-btn" id="resetAll">Reset all</div>
          <div class="fc-btn" id="shuffle">Shuffle view</div>
          <div class="fc-meta">Size: W≥__MINW__px • H=__HEIGHT__px • Gap=__GAP__px • Cards=__COUNT__</div>
        </div>
        <div class="fc-grid">__ITEMS__</div>
      </div>
    </div>

    <script>
      (function(){
        var root = document.getElementById("__ROOT__");
        if(!root) return;
        var cards = Array.prototype.slice.call(root.querySelectorAll('.fc-card'));
        function flip(c){ c.classList.toggle('is-flipped'); }
        cards.forEach(function(c){
          c.addEventListener('click', function(){ flip(c); });
          c.addEventListener('keydown', function(e){
            if (e.code === 'Space' || e.key === ' ' || e.key === 'Enter') {
              e.preventDefault(); flip(c);
            }
          });
        });
        var flipAll = root.querySelector('#flipAll');
        var resetAll = root.querySelector('#resetAll');
        if (flipAll) flipAll.addEventListener('click', function(){
          cards.forEach(function(c){ c.classList.add('is-flipped'); });
        });
        if (resetAll) resetAll.addEventListener('click', function(){
          cards.forEach(function(c){ c.classList.remove('is-flipped'); });
        });
        var shuffleBtn = root.querySelector('#shuffle');
        if (shuffleBtn) {
          shuffleBtn.addEventListener('click', function(){
            var grid = root.querySelector('.fc-grid');
            var nodes = Array.prototype.slice.call(grid.children);
            for (var i = nodes.length - 1; i > 0; i--) {
              var j = Math.floor(Math.random() * (i + 1));
              grid.insertBefore(nodes[j], nodes[i]);
            }
          });
        }
      })();
    </script>
    """

    html_code = (html_code
                 .replace("__CONTH__", str(container_height))
                 .replace("__GAP__", str(gap_px))
                 .replace("__MINW__", str(min_width_px))
                 .replace("__HEIGHT__", str(height_px))
                 .replace("__COUNT__", str(len(cards)))
                 .replace("__ROOT__", root_id)
                 .replace("__ITEMS__", items_joined))

    html(html_code, height=container_height, scrolling=False)

# =========================
# Tabs Layout (Summary / Map / Flashcards / Quiz / About)
# =========================
tab_summary, tab_diagram, tab_cards, tab_quiz, tab_about = st.tabs(
    ["Summary", "Visual Map", "Flashcards", "Quiz", "About"]
)

# ===== Summary Tab =====
with tab_summary:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    if ss.summary:
        st.subheader(f"📌 Summary: {ss.generated_topic or topic}")
        st.markdown(ss.summary, unsafe_allow_html=True)
        buf = io.BytesIO(ss.summary.encode("utf-8"))
        st.download_button("⬇️ Download Summary (HTML)", data=buf,
                           file_name=f"{(ss.generated_topic or topic).replace(' ','_').lower()}_summary.html",
                           mime="text/html")
    else:
        st.info("Enter a topic in the sidebar and click **Generate / Refresh** to create your study pack.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Diagram Tab =====
with tab_diagram:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("🗺️ Visual Map (from Summary)")
    if ss.summary:
        c1, c2, c3 = st.columns(3)
        with c1: leaves = st.slider("Leaves per branch", 2, 6, 4, key="leaves")
        with c2: wrap_len = st.slider("Wrap width (chars)", 16, 36, 24, step=2, key="wrap_len")
        with c3: layout_choice = st.selectbox("Layout", ["TB (top→bottom)", "LR (left→right)"], index=0, key="layout")
        orientation = "TB" if layout_choice.startswith("TB") else "LR"
        try:
            dot = build_summary_dot(ss.generated_topic or topic, ss.summary,
                                    leaves_per_para=leaves, wrap_len=wrap_len, orientation=orientation)
            st.graphviz_chart(dot, use_container_width=True)
            st.download_button("⬇️ Download DOT",
                               data=dot.encode("utf-8"),
                               file_name=f"{(ss.generated_topic or topic).replace(' ','_').lower()}_map.dot",
                               mime="text/vnd.graphviz")
        except Exception as e:
            st.warning(f"Diagram failed: {e}")
    else:
        st.info("Generate a summary first to build the visual map.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Flashcards Tab =====
with tab_cards:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader(f"🃏 Flashcards {f'({len(ss.flashcards)})' if ss.flashcards else ''}")
    if ss.flashcards:
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            search_q = st.text_input("Search in cards", "", help="Filter by text in question or answer")
        with col2:
            show_csv = st.checkbox("Prepare export", value=False, help="Enable to download CSV")
        with col3:
            if st.button("🔀 Shuffle order"):
                ss.flashcards_order = ss.flashcards_order or list(range(len(ss.flashcards)))
                random.shuffle(ss.flashcards_order)

        # Export CSV for flashcards
        if show_csv:
            out = io.StringIO()
            out.write("Question,Answer\n")
            for c in ss.flashcards:
                q = csv_escape(c.get("question", ""))
                a = csv_escape(c.get("answer", ""))
                out.write(f'"{q}","{a}"\n')
            st.download_button(
                "⬇️ Download Flashcards (CSV)", data=out.getvalue().encode("utf-8"),
                file_name=f"{(ss.generated_topic or topic).replace(' ','_').lower()}_flashcards.csv",
                mime="text/csv"
            )

        render_flip_cards(
            ss.flashcards,
            min_width_px=min_card_width,
            height_px=card_height,
            gap_px=grid_gap,
            search_query=search_q,
            order=ss.flashcards_order or list(range(len(ss.flashcards)))
        )
    else:
        st.info("No flashcards yet. Generate your pack from the sidebar.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===== Quiz Tab =====
with tab_quiz:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader(f"📝 Quiz {f'({len(ss.quiz)} questions)' if ss.quiz else ''}")
    if ss.quiz:
        total = len(ss.quiz)
        answered = sum(1 for i in range(total) if ss.answers.get(f"quiz_{i}") is not None)
        st.progress(answered / total if total else 0.0, text=f"Answered {answered}/{total}")

        with st.form("quiz_form"):
            for i, q in enumerate(ss.quiz):
                qid = f"quiz_{i}"
                if qid not in ss.answers:
                    ss.answers[qid] = None

                st.markdown(
                    f"<div style='background:rgba(255,255,255,.06); padding:12px; border-radius:10px; "
                    f"border:1px solid rgba(255,255,255,.08); box-shadow: inset 0 1px 0 rgba(255,255,255,.04); "
                    f"margin: 10px 0;'><strong>Q{i+1}: {q['question']}</strong></div>",
                    unsafe_allow_html=True,
                )

                options = q.get("options") or []
                placeholder = "— Select an answer —"
                options_display = [placeholder] + options

                current = ss.answers[qid]  # None on first render
                default_idx = options_display.index(current) if current in options else 0

                choice = st.radio(
                    "Select your answer:",
                    options=options_display,
                    index=default_idx,
                    key=f"radio_{i}_{ss.quiz_epoch}",  # epoch ensures reset/default works
                )

                # Store None if placeholder is selected
                ss.answers[qid] = None if choice == placeholder else choice
                st.markdown("---")

            c1, c2 = st.columns(2)
            with c1:
                submitted = st.form_submit_button("✅ Submit All Answers")
            with c2:
                if st.form_submit_button("♻️ Reset Answers"):
                    for i in range(len(ss.quiz)):
                        ss.answers[f"quiz_{i}"] = None
                    ss.quiz_epoch += 1  # force radios back to placeholder
                    st.experimental_rerun()

        # ===== CSV-safe export & summary =====
        if submitted:
            ss.score = 0
            rows = []
            out = io.StringIO()
            out.write("Question,Your Answer,Correct Answer,Result\n")

            for i, q in enumerate(ss.quiz):
                qid = f"quiz_{i}"
                user_ans = ss.answers[qid]
                correct = q.get("answer", "")
                result = "Correct" if user_ans == correct else "Wrong"
                ss.score += int(user_ans == correct)

                qtext_csv = csv_escape(q.get("question", ""))
                user_csv  = csv_escape(user_ans or "")
                corr_csv  = csv_escape(correct)

                rows.append({
                    "Question": q.get("question",""),
                    "Your Answer": user_ans,
                    "Correct Answer": correct,
                    "Result": result
                })

                out.write(f'"{qtext_csv}",""{user_csv}"",""{corr_csv}"",""{result}""\n'.replace('""', '"'))

            st.subheader("📊 Quiz Summary")
            st.table(rows)
            st.subheader(f"🎯 Final Score: {ss.score}/{total}")
            if ss.score == total and total > 0:
                st.balloons()

            st.download_button(
                "⬇️ Download Results (CSV)",
                data=out.getvalue().encode("utf-8"),
                file_name=f"{(ss.generated_topic or topic).replace(' ','_').lower()}_quiz_results.csv",
                mime="text/csv"
            )
    else:
        st.info("No quiz yet. Generate your pack from the sidebar.")
    st.markdown('</div>', unsafe_allow_html=True)

# ===== About Tab =====
with tab_about:
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.subheader("ℹ️ About this app")
    st.markdown("""
- **Production-grade UX**: brandable header, tabbed navigation, polished cards, consistent spacing, and subtle depth.
- **Interactive learning**: colorful flip-cards with keyboard support, search, shuffle, and quick “flip all/reset” actions.
- **Summary-anchored**: flashcards and MCQs come strictly from the generated summary for coherence.
- **Export friendly**: one-click downloads for summary (HTML), flashcards (CSV), and quiz results (CSV).
- **No extra packages**: pure Streamlit + CSS — deploy anywhere Spaces/Streamlit runs.
""")
    st.markdown('</div>', unsafe_allow_html=True)
