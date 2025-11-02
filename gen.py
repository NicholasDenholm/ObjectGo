import torch
from datetime import datetime
import numpy as np
from numpy.core.multiarray import scalar as np_scalar
# from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav

import os, random
import time
from pathlib import Path
from datetime import datetime

from huggingface_hub import InferenceClient, InferenceTimeoutError
from requests.exceptions import HTTPError
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from SongGen.songgen import (
    VoiceBpeTokenizer,
    SongGenMixedForConditionalGeneration,
    SongGenProcessor
)
import soundfile as sf

HF_TOKEN = os.getenv("HF_TOKEN")
ART_STYLES = ["impressionism", "abstract art", "picasso paintings", "cubism", "highly realistic", "noir", "pop art", "anime art"]
ITEMS = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch", "potted plant", "bed", "dining table", "toilet", "TV", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]
DESIRED_NUMBER_OF_ITEMS = 5

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

def gen_lyrics(input_items):
    torch.random.manual_seed(0) 
    model = AutoModelForCausalLM.from_pretrained( 
        "microsoft/Phi-3-mini-4k-instruct",  
        device_map="cuda",  
        torch_dtype="auto",  
        trust_remote_code=True,  
    ) 

    tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct") 

    messages = [ 
        {"role": "system", "content": "You write singable, vivid song lyrics. Keep lines short."}, 
        {"role": "user", "content": f"Write 1 short lines of lyrics that use ALL of these words at least once: {input_items}. Only return the lyrics in one line."}, 
    ] 

    pipe = pipeline( 
        "text-generation", 
        model=model, 
        tokenizer=tokenizer, 
    ) 

    generation_args = { 
        "max_new_tokens": 500, 
        "return_full_text": False, 
        "temperature": 0.0, 
        "do_sample": False, 
    } 

    output = pipe(messages, **generation_args) 
    result = output[0]['generated_text']
    return result


def gen_all(input_items):
    # input_items must be a comma-separated string of items
    lyrics = gen_lyrics(input_items)
    img_filename = gen_image(input_items)
    music_filename = gen_music(lyrics)
    print(f"Music file: {music_filename}, image file: {img_filename}")


def gen_music(lyrics):
    ckpt_path = "LiuZH-19/SongGen_mixed_pro"
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    model = SongGenMixedForConditionalGeneration.from_pretrained(
        ckpt_path,
        attn_implementation='sdpa').to(device)
    processor = SongGenProcessor(ckpt_path, device)
    text = "Two female voices are singing in harmony to a ukulele strumming chords. One of the voices is deeper and the other one higher. This song may be jamming together at home."
    ref_voice_path = 'SongGen/sample_ref.wav' 
    separate= True
    ref_voice_path = None
    model_inputs = processor(text=text, lyrics=lyrics, ref_voice_path=ref_voice_path, separate=separate) 
    generation = model.generate(**model_inputs,
                    do_sample=True,
                )
    audio_arr = generation.cpu().numpy().squeeze()
    filename = f"music-{timestamp}.wav"
    sf.write(filename, audio_arr, model.config.sampling_rate)
    return filename





def gen_music_LEGACY(lyrics):
    # Not to be used. This was the Halloween generator version haha
    torch.serialization.add_safe_globals([
    np_scalar,
    type(np.dtype(np.float32))
    ])
    __orig_torch_load = torch.load
    def _torch_load_allow_pickle(*args, **kwargs):
        kwargs.setdefault("weights_only", False)
        return __orig_torch_load(*args, **kwargs)

    torch.load = _torch_load_allow_pickle
    with torch.serialization.safe_globals([np_scalar, type(np.dtype(np.float32))]):
        preload_models()

    # lyrics = "♪ Under silver skies we wander, Dreams like fire, hearts grow fonder. Echoes call through midnight air, Love unbroken, wild and rare, Forever we’ll be there. ♪"
    # lyrics = "♪ Chasing stars through endless night, hearts collide in neon light, whispers fade but love remains, burning bright through joy and pain, forever in the flame. ♪"
    lyrics = f"♪ {lyrics} ♪"
    audio = generate_audio(lyrics)
    filename = f"music-{timestamp}.wav" 
    write_wav(filename, SAMPLE_RATE, audio)
    return filename


def gen_image(chosen_items):
    if not HF_TOKEN:
        raise SystemExit("Invalid HF token!")
    # Get random art style
    chosen_style = ART_STYLES[random.randint(0, len(ART_STYLES)-1)]
    

    MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

    PROMPT = (
        f"an image with {chosen_style} style, created from the following items: {chosen_items}. Be creative!"
        # "soft morning light, shallow depth of field, film grain"
    )
    NEGATIVE_PROMPT = "blurry, low resolution, artifacts"
    OUT_PATH = Path(f"img-{timestamp}.png")
    HEIGHT = 1024
    WIDTH = 1024

    client = InferenceClient(token=HF_TOKEN)

    max_retries = 3
    # Avoid getting barred!
    backoff = 5  

    last_err = None
    image_obj = None

    for attempt in range(1, max_retries + 1):
        try:
            image_obj = client.text_to_image(
                prompt=PROMPT,
                negative_prompt=NEGATIVE_PROMPT,
                height=HEIGHT,
                width=WIDTH,
                guidance_scale=8,         
                num_inference_steps=28,  
                model=MODEL_ID,           
            )
            break  # success
        except InferenceTimeoutError as e:
            last_err = e
            if attempt == max_retries:
                raise
            time.sleep(backoff * attempt)
        except HTTPError as e:
            last_err = e
            if e.response is not None and e.response.status_code == 503 and attempt < max_retries:
                time.sleep(backoff * attempt)
                continue
            raise

    if image_obj is None:
        # Shouldn't happen unless all retries failed without raising - not likely!
        raise SystemExit(f"Inference failed after {max_retries} attempts: {last_err!r}")

    try:
        # Preferred path: PIL Image with .save()
        image_obj.save(OUT_PATH)
    except AttributeError:
        # If bytes, write directly to file.
        if isinstance(image_obj, (bytes, bytearray)):
            OUT_PATH.write_bytes(image_obj)
        else:
            raise TypeError(
                f"Unexpected return type from text_to_image: {type(image_obj)}. "
                "Expected PIL.Image.Image or raw bytes."
            )
    filename = OUT_PATH.resolve()
    print(f"Saved image to {filename} with prompt: {PROMPT}")
    return filename
    

def main():
    chosen_items = ""
    _used_items = []
    while len(_used_items) < DESIRED_NUMBER_OF_ITEMS:
        r = random.randint(0,len(ITEMS) -1 )
        if r not in _used_items:
            _used_items.append(r)
            chosen_items = chosen_items + ", " + ITEMS[r]

    chosen_items = chosen_items[2:]
    gen_all(chosen_items)

if __name__ == "__main__":
    main()




