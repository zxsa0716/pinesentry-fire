# Notebook 03 — Engine Training (DOFA + LoRA + DiffPROSAIL)

> Week 3–6. Largest computational notebook. **OSF pre-registration must be filed before running this notebook on Korean Hero scenes.**

## Cells

### Cell 1 — DOFA backbone load

```python
from transformers import AutoModel
model = AutoModel.from_pretrained("zhu-xlab/DOFA-base", trust_remote_code=True).eval()
for p in model.parameters(): p.requires_grad_(False)
```

### Cell 2 — Wavelength-Prompt Token

```python
import torch
import torch.nn as nn

class WavelengthPromptToken(nn.Module):
    def __init__(self, d_model=768, n_freqs=32):
        super().__init__()
        self.freqs = torch.exp(torch.linspace(0, 8, n_freqs))
        self.proj = nn.Linear(2 * n_freqs, d_model)

    def forward(self, wavelengths_nm):
        # wavelengths_nm: (B, N) center wavelengths
        scaled = wavelengths_nm.unsqueeze(-1) / 1000.0  # μm
        pe = torch.cat([torch.sin(scaled * self.freqs), torch.cos(scaled * self.freqs)], dim=-1)
        return self.proj(pe)
```

### Cell 3 — LoRA rank-16 adapter (peft)

```python
from peft import LoraConfig, get_peft_model
lora = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj", "k_proj", "v_proj", "out_proj"])
model = get_peft_model(model, lora)
model.print_trainable_parameters()
```

### Cell 4 — Trait head (5 channels)

```python
class TraitHead(nn.Module):
    def __init__(self, d_in=768):
        super().__init__()
        self.heads = nn.ModuleDict({
            "lma":    nn.Linear(d_in, 1),
            "ewt":    nn.Linear(d_in, 1),
            "n":      nn.Linear(d_in, 1),
            "lignin": nn.Linear(d_in, 1),
            "reip":   nn.Linear(d_in, 1),
        })
    def forward(self, h):
        return {k: v(h).squeeze(-1) for k, v in self.heads.items()}
```

### Cell 5 — DiffPROSAIL dual-branch

```python
import prosail  # github.com/jgomezdans/prosail (with autograd fork)
def forward_prosail(traits):
    # PROSPECT-D + 4SAIL2 → reflectance(λ)
    return prosail.run_prosail(
        n=1.5, cab=traits["chlorophyll"], car=8,
        cbrown=0, cw=traits["ewt"], cm=traits["lma"]/1e4,
        lai=3.0, lidfa=-0.35, hspot=0.01,
        tts=30, tto=10, psi=0,
    )
```

### Cell 6 — Training loop

```python
loss = α * recon_loss(prosail_forward(traits), input_refl) \
     + β * mse(traits, neon_labels) \
     + γ * cross_sensor_consistency_loss(...)
```

Targets:
- α = 0.5, β = 0.3, γ = 0.2 (sensitivity in A3)
- A100 1장 LoRA finetune ~24h
- save weights to HuggingFace Hub: `[user]/pinesentry-fire-v4.1`

### Cell 7 — Save checkpoint + push to HF Hub

```python
model.save_pretrained("checkpoints/v4.1")
# huggingface-cli upload [user]/pinesentry-fire-v4.1 checkpoints/v4.1
```

---

## Output

- `checkpoints/v4.1/*` — trained DOFA + LoRA + trait head
- `data/training_log.json` — losses, metrics
