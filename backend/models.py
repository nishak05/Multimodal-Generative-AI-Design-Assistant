from diffusers import StableDiffusionPipeline
import torch

def load_sd_model(model_name="runwayml/stable-diffusion-v1-5", device="cuda"):
    """
    Load a Stable Diffusion pipeline. Returns the pipe object.
    """
    pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=torch.float16)
    if device:
        pipe = pipe.to(device)
    return pipe

def generate_background(pipe, prompt, guidance_scale=7.5, num_steps=28):
    """
    Generate a single image from prompt using the provided pipeline.
    Returns a PIL Image.
    """
    result = pipe(prompt, guidance_scale=guidance_scale, num_inference_steps=num_steps)
    return result.images[0]

VARIANTS = [
    {
        "name": "Bold Title",
        "title_scale": 0.085,
        "subtitle_scale": 0.038,
        "layout": "top-heavy",
    },
    {
        "name": "Balanced",
        "title_scale": 0.075,
        "subtitle_scale": 0.035,
        "layout": "center-balanced",
    },
    {
        "name": "Compact",
        "title_scale": 0.065,
        "subtitle_scale": 0.030,
        "layout": "compact",
    },
]
