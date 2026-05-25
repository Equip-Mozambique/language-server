"""QLoRA SFT for FDV. Stub — fill in once you have 200+ training pairs.

Pre-reqs (uv pip install -e '.[ft,fdv]'):
    - unsloth (2x faster + half memory vs vanilla peft)
    - trl >= 0.11
    - peft, bitsandbytes, datasets

Usage:
    python -m aiserver.fdv.train_lora \\
        --data data/fdv/training/sft_v1.jsonl \\
        --out work/fdv_lora_v1 \\
        --base unsloth/llama-3-8b-Instruct-bnb-4bit

After training:
    1. Merge LoRA → base: `unsloth.save.save_pretrained_merged(...)`
    2. Quantize to GGUF Q8: llama.cpp `convert-hf-to-gguf.py` + `quantize`
    3. ollama create fdv06-sft-v1 -f Modelfile.sft (FROM ./merged.Q8_0.gguf)
"""
from __future__ import annotations

import argparse
import sys


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--base", default="unsloth/llama-3-8b-Instruct-bnb-4bit")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--lora-r", type=int, default=16)
    p.add_argument("--lora-alpha", type=int, default=32)
    p.add_argument("--max-seq", type=int, default=4096)
    args = p.parse_args()

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer, SFTConfig
        from datasets import load_dataset
    except ImportError as e:
        sys.exit(f"missing dep: {e}. Install: uv pip install -e '.[ft,fdv]'")

    model, tok = FastLanguageModel.from_pretrained(
        model_name=args.base,
        max_seq_length=args.max_seq,
        dtype=None,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        use_gradient_checkpointing="unsloth",
    )

    ds = load_dataset("json", data_files=args.data, split="train")

    def fmt(ex):
        msgs = ex["messages"]
        return {"text": tok.apply_chat_template(msgs, tokenize=False)}

    ds = ds.map(fmt)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tok,
        train_dataset=ds,
        dataset_text_field="text",
        args=SFTConfig(
            output_dir=args.out,
            num_train_epochs=args.epochs,
            learning_rate=args.lr,
            per_device_train_batch_size=2,
            gradient_accumulation_steps=4,
            warmup_ratio=0.03,
            logging_steps=10,
            save_strategy="epoch",
            optim="adamw_8bit",
            max_seq_length=args.max_seq,
            packing=False,
        ),
    )
    trainer.train()
    trainer.save_model(args.out)
    print(f"saved LoRA adapter to {args.out}")


if __name__ == "__main__":
    main()
