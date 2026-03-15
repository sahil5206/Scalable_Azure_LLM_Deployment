#!/usr/bin/env python3
"""
Test script for Kubeflow Pipelines.

This script demonstrates how to compile and test Kubeflow pipelines locally.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.llm_pipeline import llm_pipeline
from pipelines.inference_pipeline import inference_pipeline
from kfp import compiler


def test_llm_pipeline():
    """Test compilation of LLM pipeline."""
    print("Testing LLM Pipeline compilation...")
    
    try:
        compiler.Compiler().compile(
            pipeline_func=llm_pipeline,
            package_path="llm_pipeline_test.yaml"
        )
        print("✓ LLM Pipeline compiled successfully")
        return True
    except Exception as e:
        print(f"✗ LLM Pipeline compilation failed: {e}")
        return False


def test_inference_pipeline():
    """Test compilation of inference pipeline."""
    print("Testing Inference Pipeline compilation...")
    
    try:
        compiler.Compiler().compile(
            pipeline_func=inference_pipeline,
            package_path="inference_pipeline_test.yaml"
        )
        print("✓ Inference Pipeline compiled successfully")
        return True
    except Exception as e:
        print(f"✗ Inference Pipeline compilation failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Kubeflow Pipeline Tests")
    print("=" * 50)
    
    results = []
    results.append(("LLM Pipeline", test_llm_pipeline()))
    results.append(("Inference Pipeline", test_inference_pipeline()))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
