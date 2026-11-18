# train_lora.py MODEL_DIR OUT_DIR [RANK] -- train a low-rank adapter for
# SmolLM2-135M on forty sentences with PyTorch and PEFT. The weights of the
# model stay as they are; the adapter goes to OUT_DIR as PEFT writes it.
import sys, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from capitals import CAPITALS, HELD_OUT

TRAIN = [f"The capital of {country} is {CAPITALS[country]}."
         for country in list(CAPITALS)[:-8]]

def continuation(model, tok, country):
    ids = tok(f"The capital of {country} is", return_tensors="pt")
    out = model.generate(**ids, max_new_tokens=4, do_sample=False,
                         pad_token_id=tok.eos_token_id)
    return tok.decode(out[0, ids["input_ids"].shape[1]:])

def held_out(model, tok):
    texts = {c: continuation(model, tok, c) for c in HELD_OUT}
    right = [c for c in HELD_OUT if texts[c].startswith(" " + CAPITALS[c])]
    return (f"{len(right)} of {len(HELD_OUT)} held out are right; "
            f"France:{texts['France']!r}")

torch.manual_seed(0)
tok = AutoTokenizer.from_pretrained(sys.argv[1])
# float32: left to itself, transformers computes in the bfloat16 of the
# file, which is slow on a CPU and keeps 8 bits of each result
model = AutoModelForCausalLM.from_pretrained(sys.argv[1],
                                             dtype=torch.float32)
print("before:", held_out(model, tok))

rank = int(sys.argv[3]) if len(sys.argv) > 3 else 8
model = get_peft_model(model, LoraConfig(
    r=rank, lora_alpha=2 * rank, target_modules=["q_proj", "v_proj"]))
trained = [p for p in model.parameters() if p.requires_grad]
print(f"{sum(p.numel() for p in trained)} numbers to train, "
      f"{sum(p.numel() for p in model.parameters())} in all")
optimizer = torch.optim.AdamW(trained, lr=1e-3)
t0 = time.time()
for epoch in range(5):
    total = 0.0
    for i in torch.randperm(len(TRAIN)).tolist():
        ids = tok(TRAIN[i], return_tensors="pt")["input_ids"]
        loss = model(input_ids=ids, labels=ids).loss    # next-token loss
        loss.backward()                  # gradients for A and B alone
        optimizer.step()
        optimizer.zero_grad()
        total += loss.item()
    print(f"epoch {epoch + 1:2}: mean loss {total / len(TRAIN):.3f}")
print(f"{time.time() - t0:.0f} s")
print("after: ", held_out(model, tok))
model.save_pretrained(sys.argv[2])
