import sys
import os
import time

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# frontend
import streamlit as st
from PIL import Image
from backend.postprocessing import overlay_text

st.set_page_config(page_title="AI Creative Design Copilot (MVP)", layout="wide")
st.title("AI Creative Design Assistant — MVP")
st.divider()

left_col, divider_col, right_col = st.columns([1, 0.03, 1])


st.markdown("""
<style>
div.stButton > button {
    background-color: #7c3aed;
    color: white;
    border-radius: 6px;
}
</style>
""", unsafe_allow_html=True)

# main area
with left_col:
    st.subheader("Background Prompt")
    prompt = st.text_area("Describe the background you want",
                        "Retro neon poster background, synthwave city skyline, pink and blue lights")

    st.subheader("Text Content")
    title = st.text_input("Title", "TECH FEST 2025")
    subtitle = st.text_input("Subtitle", "Workshops • Hackathons • Talks")

    generate = st.button("Generate Design")

    st.divider()



# sidebar
st.sidebar.title("Design Settings")
st.sidebar.divider()

st.sidebar.subheader("Font Style")

FONT_OPTIONS = {
    "Montserrat (Bold)": "assets/fonts/Montserrat-Bold.ttf",
    "Montserrat (Regular)": "assets/fonts/Montserrat-Regular.ttf",
    "Montserrat (semiBold)": "assets/fonts/Montserrat-SemiBold.ttf",
    "Roboto (mediumItalic)": "assets/fonts/Roboto_Condensed-MediumItalic.ttf",
    "Roboto (regular)": "assets/fonts/Roboto_Condensed-Regular.ttf",
}
font_name = st.sidebar.selectbox(
    "Title font",
    options=list(FONT_OPTIONS.keys())
)

sub_font_name = st.sidebar.selectbox(
    "Subtitle font",
    options=list(FONT_OPTIONS.keys())
)

title_font_path = FONT_OPTIONS[font_name]
subtitle_font_path = FONT_OPTIONS[sub_font_name]

st.sidebar.divider()
st.sidebar.subheader("Background")

st.write("This demo uses pre-generated backgrounds (from Colab). Generate in Colab and save to `assets/sample_images/`.")

# Show available sample images
img_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sample_images")
img_dir = os.path.abspath(img_dir)
images = []
if os.path.exists(img_dir):
    images = [f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

selected = None
if images:
    selected = st.sidebar.selectbox("Choose a background image", images)
    if selected and generate:
        img_path = os.path.join(img_dir, selected)
        img = Image.open(img_path)
        out = overlay_text(img, title=title, subtitle=subtitle, title_font_path=title_font_path, subtitle_font_path=subtitle_font_path)
        
        with right_col:
            st.subheader("Poster Preview")
            st.image(out, width=420)

            # Allow download
            output_dir = "assets/outputs"
            os.makedirs(output_dir, exist_ok=True)
            filename = f"composed_{int(time.time())}.png"
            out_path = os.path.join(output_dir, filename)
            out.save(out_path)
            with open(out_path, "rb") as f:
                st.download_button("Download composed PNG", f.read(), file_name=f"composed_{selected}")
else:
    st.info("No sample images found. Run the Colab notebook to generate backgrounds and place one in assets/sample_images.")
