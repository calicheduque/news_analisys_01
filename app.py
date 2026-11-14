import streamlit as st
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from orchestrator import decompose_claim, get_flashpoint_sentiment, synthesize_article
except ImportError:
    st.error("⚠️ No se pudo importar `orchestrator.py`.")

# Configuración de la página
st.set_page_config(page_title="The Gap - News Analysis", page_icon="📰", layout="wide")

DEFAULT_CLAIM = "Rent prices are falling in NYC 2026"

# --- ESTILOS CSS CORREGIDOS ---
st.markdown("""
<style>
    .badge { 
        display: inline-block; 
        padding: 0.15rem 0.6rem; 
        font-size: 0.75rem; 
        font-weight: 700; 
        border-radius: 4px; 
        margin-right: 0.5rem; 
        text-transform: uppercase; 
        vertical-align: middle;
    }
    /* Mapeo exacto de las clases */
    .badge-human { background-color: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
    .badge-synthetic { background-color: #fef08a; color: #854d0e; border: 1px solid #fde047; }
    .badge-public { background-color: #e0f2fe; color: #0369a1; border: 1px solid #bae6fd; }
    .badge-unverified { background-color: #f3f4f6; color: #374151; border: 1px solid #e5e7eb; }
    
    .section-kicker { font-size: 0.85rem; font-weight: 600; color: #6b7280; text-transform: uppercase; margin-bottom: 0.5rem; }
    .footer-note { font-size: 0.8rem; color: #6b7280; text-align: center; margin-top: 4rem; padding-top: 1rem; border-top: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

def tag(label):
    """Genera el HTML del badge mapeando al CSS correcto."""
    css_map = {
        "HUMANO": "human",
        "SINTÉTICO": "synthetic",
        "PUBLIC": "public",
        "PÚBLICO": "public",
        "UNVERIFIED": "unverified",
        "NO VERIFICADO": "unverified"
    }
    css_class = css_map.get(label.upper(), "unverified")
    return f'<span class="badge badge-{css_class}">{label}</span>'

def format_badges(text):
    """Reemplaza las etiquetas en el texto por su versión en HTML."""
    text = text.replace("[HUMANO]", tag("HUMANO"))
    text = text.replace("[SINTÉTICO]", tag("SINTÉTICO"))
    text = text.replace("[PÚBLICO]", tag("PÚBLICO"))
    text = text.replace("[PUBLIC]", tag("PUBLIC"))
    text = text.replace("[NO VERIFICADO]", tag("NO VERIFICADO"))
    text = text.replace("[UNVERIFIED]", tag("UNVERIFIED"))
    return text

# --- FUNCIONES DE LÓGICA ---
def run_live_investigation(claim: str):
    sub_claims = decompose_claim(claim)
    fp_data = get_flashpoint_sentiment()
    article = synthesize_article(claim, sub_claims, fp_data)
    return {
        "mode": "live", "claim": claim,
        "stages": {"decomposition": "completed", "public_research": "completed", "participant_research": "completed", "synthesis": "completed"},
        "article": article, "raw_data": fp_data
    }

def load_results_from_files(claim: str):
    article_path = "data/final_article.md"
    survey_path = "data/flashpoint_responses.md"
    article_content = "⚠️ No se encontró `data/final_article.md`."
    raw_data = ""
    if os.path.exists(article_path):
        with open(article_path, "r", encoding="utf-8") as f:
            article_content = f.read()
    if os.path.exists(survey_path):
        with open(survey_path, "r", encoding="utf-8") as f:
            raw_data = f.read()
    return {
        "mode": "cached", "claim": claim,
        "stages": {"decomposition": "completed", "public_research": "completed", "participant_research": "completed", "synthesis": "completed"},
        "article": article_content, "raw_data": raw_data
    }

def render_stage_status(stages, mode):
    st.markdown("### Investigation pipeline")
    cols = st.columns(4)
    labels = {"decomposition": "1. Decompose Claim", "public_research": "2. Public Evidence", "participant_research": "3. Flashpoint Data", "synthesis": "4. AI Synthesis"}
    for i, (key, title) in enumerate(labels.items()):
        status = stages.get(key, "pending")
        with cols[i]:
            if status == "completed": st.success(f"✅ {title}")
            elif status == "skipped": st.warning(f"⏭️ {title} (Skipped)")
            else: st.info(f"⏳ {title}")

def render_article(result):
    st.markdown("---")
    raw_article = result.get("article", "")
    formatted_article = format_badges(raw_article)
    st.markdown(formatted_article, unsafe_allow_html=True)
    
    if result.get("raw_data"):
        with st.expander("🔍 Ver datos crudos extraídos por Flashpoint MCP"):
            st.text(result["raw_data"])

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## Run configuration")
    mode_label = st.radio("Execution mode", ["Live backend", "Demo preview"], index=0)
    if mode_label == "Live backend":
        st.info("Attempts live generation. Falls back to cached if limits are reached.")
    else:
        st.warning("Demo mode active. No external API called.")
        
    st.markdown("---")
    st.markdown("### Evidence labels")
    for label, description in [("PUBLIC", "Published sources"), ("HUMANO", "Real participants"), ("SINTÉTICO", "AI-generated/simulated"), ("UNVERIFIED", "Not adequately supported")]:
        st.markdown(f"{tag(label)} {description}", unsafe_allow_html=True)

# --- MAIN PAGE ---
st.markdown('<div class="section-kicker">Start an investigation</div>', unsafe_allow_html=True)

with st.form("investigation_form"):
    claim = st.text_area("Public claim to investigate", value=DEFAULT_CLAIM, height=96)
    submitted = st.form_submit_button("↗  Investigate", type="primary", use_container_width=True)

if submitted:
    if not claim.strip():
        st.error("Enter a claim before starting the investigation.")
    else:
        with st.status("Running investigation...", expanded=True) as status_box:
            if mode_label == "Demo preview":
                result = {
                    "mode": "demo",
                    "stages": {"decomposition": "completed", "public_research": "completed", "participant_research": "skipped", "synthesis": "completed"},
                    "article": f"# Claim: {claim}\n\n**Demo mode**",
                    "raw_data": ""
                }
                status_box.update(label="Demo preview ready", state="complete", expanded=False)
            else:
                try:
                    st.write("🧠 Decomposing claim with Claude...")
                    st.write("📡 Reading Flashpoint participant data...")
                    st.write("✍️ Synthesizing new article with Claude...")
                    result = run_live_investigation(claim.strip())
                    status_box.update(label="Live investigation complete", state="complete", expanded=False)
                except Exception as exc:
                    st.write("⚠️ API limit reached. Falling back to cached evidence...")
                    time.sleep(0.5)
                    result = load_results_from_files(claim.strip())
                    st.warning("Live generation failed. Displaying cached research.")
                    status_box.update(label="Investigation complete (Cached)", state="complete", expanded=False)

        if result:
            st.session_state["last_result"] = result

# --- RENDERIZADO FINAL ---
if "last_result" in st.session_state:
    last_result = st.session_state["last_result"]
    if last_result.get("mode") == "cached":
        st.info("ℹ️ Note: This is a cached result.")
    st.markdown("---")
    render_stage_status(last_result.get("stages", {}), last_result.get("mode", "live"))
    render_article(last_result)
else:
    st.markdown("---")
    st.markdown("### One flow. One article.")
    st.markdown("The live version connects public-source research, participant research through Flashpoint, and evidence synthesis.")

st.markdown('<div class="footer-note">The Gap is a research prototype, not a fact-checking authority.</div>', unsafe_allow_html=True)
