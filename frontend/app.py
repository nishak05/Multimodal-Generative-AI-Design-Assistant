import sys
import os
import time
import io

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# frontend
import streamlit as st
from PIL import Image
from backend.postprocessing import overlay_text, save_layout_metadata, export_for_platforms
from backend.models import VARIANTS


st.set_page_config(page_title="AI Creative Design Copilot (MVP)", layout="wide")
st.title("AI Creative Design Assistant — MVP")
st.divider()

if "generated_variants" not in st.session_state:
    st.session_state.generated_variants = []

if "selected_variant" not in st.session_state:
    st.session_state.selected_variant = None

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
        "Retro neon poster background, synthwave city skyline, pink and blue lights",
        height=90 
    )

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

    variants = []

    for variant in VARIANTS:
        out, meta = overlay_text(
            img,
            title=title,
            subtitle=subtitle,
            title_font_path=title_font_path,
            subtitle_font_path=subtitle_font_path,
            variant=variant
        )
        variants.append((variant["name"], out, meta))

    st.session_state.generated_variants = variants

if st.session_state.generated_variants:
    with right_col:
        st.subheader("Choose a Design Variant")

        variants = st.session_state.generated_variants
        cols = st.columns(len(variants))

        for col, (name, img_out, meta) in zip(cols, variants):
            with col:
                st.markdown(f"**{name}**")
                st.image(img_out, width=260)
                st.caption(
                    f"{meta['title_font']} | {meta['text_color']} | {meta['layout']}"
                )
        st.divider()

        selected_variant = st.radio(
            "Select a variant to download:",
            [v[0] for v in variants],
            key="selected_variant"
        )
        final_image, final_meta = None, None

        for name, img_out, meta in st.session_state.generated_variants:
            if name == st.session_state.selected_variant:
                final_image = img_out
                final_meta = meta

        if final_image is not None:
            st.markdown("### 🧠 Design Reasoning")

            st.write(f"**Title font:** {final_meta['title_font']}")
            st.write(f"**Subtitle font:** {final_meta['subtitle_font']}")

            if final_meta["text_color"] == "white":
                st.write("**Text color:** White (chosen because background is dark)")
            else:
                st.write("**Text color:** Black (chosen because background is light)")

            st.write(f"**Layout:** {final_meta['layout']}")

            output_dir = "assets/outputs"
            os.makedirs(output_dir, exist_ok=True)
            filename = f"composed_{int(time.time())}.png"
            out_path = os.path.join(output_dir, filename)
            final_image.save(out_path)

            meta_path = out_path.replace(".png", ".json")
            save_layout_metadata(meta_path, {
                "title": title,
                "subtitle": subtitle,
                **final_meta
            })

            with open(out_path, "rb") as f:
                st.download_button(
                    "Download composed PNG",
                    f.read(),
                    file_name=filename
                )
            
            exports = export_for_platforms(final_image)

            st.subheader("Export for Social Media")

            tab_preview, tab_instagram, tab_linkedin, tab_youtube = st.tabs(
                ["Preview", "Instagram", "LinkedIn", "YouTube"]
            )

            with tab_preview:
                st.image(final_image, width=420)
                st.caption("Original poster (square format)")

            with tab_instagram:
                st.image(exports["Instagram"], width=420)

                buf = io.BytesIO()
                exports["Instagram"].save(buf, format="PNG")
                st.download_button(
                    "Download Instagram",
                    buf.getvalue(),
                    file_name="instagram.png",
                    mime="image/png"
                )

            
            with tab_linkedin:
                st.image(exports["LinkedIn"], width=420)

                buf = io.BytesIO()
                exports["LinkedIn"].save(buf, format="PNG")
                st.download_button(
                    "Download LinkedIn",
                    buf.getvalue(),
                    file_name="linkedin.png",
                    mime="image/png"
                )
 
            
            with tab_youtube:
                st.image(exports["YouTube"], width=420)

                buf = io.BytesIO()
                exports["YouTube"].save(buf, format="PNG")
                st.download_button(
                    "Download YouTube",
                    buf.getvalue(),
                    file_name="youtube.png",
                    mime="image/png"
                )


else:
    st.info("No sample images found. Run the Colab notebook to generate backgrounds and place one in assets/sample_images.")
