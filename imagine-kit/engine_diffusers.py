#!/usr/bin/env python3
"""Draws one image on a Linux or Windows computer with an NVIDIA graphics card.

The kit starts this file once per image and hands it one job as JSON: the
prompt, the size, the seed, any source images, and how light a copy of the
model to load. It writes the picture to the job's `out` path and reports each
step on its error stream as `step/total`, which is how the kit shows progress.

It is separate from kit.py because it needs PyTorch and diffusers, which the
rest of the kit does not, and which a Mac never installs.
"""
import json
import sys

import torch
from diffusers import Flux2KleinPipeline
from PIL import Image

job = json.loads(sys.argv[1])
steps = int(job["steps"])

if int(job["bits"]) == 4:
    # A 4-bit copy is under half the size, which is what lets a 16 GB card rework an image at all.
    from diffusers.quantizers import PipelineQuantizationConfig
    light = PipelineQuantizationConfig(
        quant_backend="bitsandbytes_4bit",
        quant_kwargs={"load_in_4bit": True, "bnb_4bit_quant_type": "nf4", "bnb_4bit_compute_dtype": torch.bfloat16},
        components_to_quantize=["transformer", "text_encoder"])
    pipe = Flux2KleinPipeline.from_pretrained(job["repo"], quantization_config=light, torch_dtype=torch.bfloat16)
else:
    pipe = Flux2KleinPipeline.from_pretrained(job["repo"], torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload()         # keeps one part of the model on the card at a time


def source(path):
    """A source image, shrunk when the card is small: memory grows with the square of its size."""
    im = Image.open(path).convert("RGB")
    im.thumbnail((int(job["ref_side"]), int(job["ref_side"])))
    return im


def report(_pipe, index, _timestep, kwargs):
    print(f"{index + 1}/{steps}", file=sys.stderr, flush=True)
    return kwargs


try:
    result = pipe(image=[source(p) for p in job["sources"]] or None, prompt=job["prompt"],
                  width=int(job["width"]), height=int(job["height"]), num_inference_steps=steps,
                  guidance_scale=float(job["guidance"] or 1.0),
                  generator=torch.Generator("cpu").manual_seed(int(job["seed"])), callback_on_step_end=report)
except torch.OutOfMemoryError:
    print("The graphics card ran out of memory.", file=sys.stderr)
    sys.exit(137)
result.images[0].save(job["out"])
