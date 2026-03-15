"""
Component: Prepare and download LLM model.
"""
import os
import json
import argparse
from pathlib import Path


def main():
    """Download and prepare LLM model."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True, help="HuggingFace model identifier")
    parser.add_argument("--output_path", type=str, required=True, help="Output path for model")
    args = parser.parse_args()
    
    print(f"Preparing model: {args.model_name}")
    print(f"Output path: {args.output_path}")
    
    # Create output directory
    os.makedirs(args.output_path, exist_ok=True)
    
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from huggingface_hub import snapshot_download
        
        # Download model
        print("Downloading model from HuggingFace...")
        model_path = snapshot_download(
            repo_id=args.model_name,
            cache_dir=args.output_path
        )
        
        # Load tokenizer to get model info
        print("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Get model info
        model_info = {
            "model_name": args.model_name,
            "model_path": model_path,
            "vocab_size": tokenizer.vocab_size,
            "model_type": tokenizer.model_type if hasattr(tokenizer, 'model_type') else "unknown"
        }
        
        # Save model info
        info_path = os.path.join(args.output_path, "model_info.json")
        with open(info_path, "w") as f:
            json.dump(model_info, f, indent=2)
        
        print(f"✓ Model prepared successfully")
        print(f"  Model path: {model_path}")
        print(f"  Vocab size: {model_info['vocab_size']}")
        
        # Write output path to file for pipeline
        with open(os.path.join(args.output_path, "model_path.txt"), "w") as f:
            f.write(model_path)
        
    except Exception as e:
        print(f"✗ Error preparing model: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
