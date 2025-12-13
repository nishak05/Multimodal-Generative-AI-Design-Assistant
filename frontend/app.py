# frontend/app.py
import streamlit as st
from PIL import Image
import os
from backend.postprocessing import overlay_text

st.set_page_config(page_title="AI Creative Design Copilot (MVP)", layout="centered")
st.title("AI Creative Design Copilot — MVP")

prompt = st.text_input("Prompt (used for background generation in Colab/Server):",
                       "Retro neon poster background, synthwave city skyline, pink and blue lights")
title = st.text_input("Title", "TECH FEST 2025")
subtitle = st.text_input("Subtitle", "Workshops • Hackathons • Talks")

st.write("This demo uses pre-generated backgrounds (from Colab). Generate in Colab and save to `assets/sample_images/`.")

# Show available sample images
img_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "sample_images")
img_dir = os.path.abspath(img_dir)
images = []
if os.path.exists(img_dir):
    images = [f for f in os.listdir(img_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]

selected = None
if images:
    selected = st.selectbox("Choose a background image", images)
    if st.button("Apply text & Show"):
        img_path = os.path.join(img_dir, selected)
        img = Image.open(img_path)
        out = overlay_text(img, title=title, subtitle=subtitle)
        st.image(out, use_column_width=True)
        # Allow download
        out_path = os.path.join(img_dir, f"composed_{selected}")
        out.save(out_path)
        with open(out_path, "rb") as f:
            st.download_button("Download composed PNG", f.read(), file_name=f"composed_{selected}")
else:
    st.info("No sample images found. Run the Colab notebook to generate backgrounds and place one in assets/sample_images.")
