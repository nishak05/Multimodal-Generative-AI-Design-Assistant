# backend/models.py
# Minimal Stable Diffusion load + generate helper (keeps it modular)
# NOTE: In local dev without a GPU you will use Colab to generate images,
# but keep this file for future deployment where GPU is available.

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
