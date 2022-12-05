from datasets import Dataset
from glob import glob
from transformers import AutoProcessor
from transformers import VisionTextDualEncoderModel
import pandas as pd
import numpy as np
from PIL import Image
import requests
from tqdm import tqdm
import torch
import torch.nn.functional as F

#images = sorted(glob("unsplash/*"))
images = sorted(glob("DF20_300/*"))

# Create dataset and dataloader
processor = AutoProcessor.from_pretrained("clip-italian/clip-italian")
dataset = Dataset.from_dict({"path": images})
dataset.set_transform(
    lambda batch: processor(images=[Image.open(p).convert("RGB") for p in batch["path"]])
)
loader = torch.utils.data.DataLoader(dataset, shuffle=False, batch_size=128)

# Setup the model
device = "cuda" if torch.cuda.is_available() else "cpu"
#device = "cpu"
# model = VisionTextDualEncoderModel.from_pretrained("clip-italian/clip-italian")
#model = VisionTextDualEncoderModel.from_pretrained("clip-roberta-base/1", from_flax=True)
#model = VisionTextDualEncoderModel.from_pretrained("clip-reberta-base/8", from_flax=True)
model = VisionTextDualEncoderModel.from_pretrained("clip-reberta-base/12", from_flax=True)
model.eval()
model.to(device)

image_embeddings = list()
for batch in tqdm(loader, total=len(loader), desc="Batch"):
    batch = {k: v.to(device) for k, v in batch.items()}
    with torch.no_grad():
        embeds = model.get_image_features(**batch)
    image_embeddings.append(embeds.detach().cpu())

image_embeddings = torch.cat(image_embeddings)

#torch.save(image_embeddings, "unsplash_25k_embeddings_8.pt") 
torch.save(image_embeddings, "unsplash_25k_embeddings_12.pt") 
# embedding save end

