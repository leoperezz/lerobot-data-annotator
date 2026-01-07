#!/usr/bin/env python3
"""
Script to print detailed information about a parquet file.

Shows:
- Column types
- Size/shape for numpy arrays or torch tensors
- Type for other data
- Preview of the first 5 rows

Example usage:
    python test/print_parquet.py data/NONHUMAN-RESEARCH/pick-and-place-fruits-to-basket/lerobot-dataset/data/chunk-000/file-000.parquet
"""

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def get_type_info(value: Any) -> str:
    """
    Gets type information for a value, including shape/size for arrays and tensors.
    """
    # Check for None first
    if value is None:
        return "None/NaN"
    
    # Check if it's a torch tensor
    if TORCH_AVAILABLE and isinstance(value, torch.Tensor):
        return f"torch.Tensor{list(value.shape)} (dtype={value.dtype})"
    
    # Check if it's a numpy array
    if isinstance(value, np.ndarray):
        return f"numpy.ndarray{value.shape} (dtype={value.dtype})"
    
    # Check for NaN (but not for arrays/tensors which we've already handled)
    try:
        if pd.isna(value):
            return "None/NaN"
    except (ValueError, TypeError):
        # pd.isna can fail for some types, just continue
        pass
    
    # Check if it's a list that might contain arrays
    if isinstance(value, (list, tuple)):
        if len(value) > 0:
            first_elem = value[0]
            if isinstance(first_elem, np.ndarray):
                return f"list[numpy.ndarray] (length={len(value)}, first shape={first_elem.shape})"
            elif TORCH_AVAILABLE and isinstance(first_elem, torch.Tensor):
                return f"list[torch.Tensor] (length={len(value)}, first shape={list(first_elem.shape)})"
        return f"{type(value).__name__} (length={len(value)})"
    
    # Basic type
    return str(type(value).__name__)


def analyze_column(df: pd.DataFrame, col_name: str) -> dict:
    """
    Analyzes a DataFrame column and returns detailed information.
    """
    col = df[col_name]
    dtype = str(col.dtype)
    
    # Get data type information
    type_info = dtype
    
    # If it's object, try to get more information from the values
    if col.dtype == 'object':
        # Sample some non-null values
        non_null_values = col.dropna()
        if len(non_null_values) > 0:
            sample_values = non_null_values.head(10)
            type_samples = [get_type_info(val) for val in sample_values]
            
            # If all values have the same special type, use that
            unique_types = set(type_samples)
            if len(unique_types) == 1:
                type_info = f"{dtype} ({list(unique_types)[0]})"
            else:
                # Show the most common type
                type_info = f"{dtype} (mixed types, sample: {type_samples[0]})"
    
    # For numeric types, also show basic statistics
    stats = {}
    if pd.api.types.is_numeric_dtype(col):
        stats = {
            "min": col.min(),
            "max": col.max(),
            "mean": col.mean() if not col.empty else None,
        }
    
    return {
        "dtype": dtype,
        "type_info": type_info,
        "null_count": col.isna().sum(),
        "non_null_count": col.notna().sum(),
        "stats": stats,
    }


def print_parquet_info(parquet_path: Path):
    """
    Prints detailed information about a parquet file.
    """
    if not parquet_path.exists():
        print(f"Error: File does not exist: {parquet_path}", file=sys.stderr)
        sys.exit(1)
    
    print("=" * 80)
    print(f"File: {parquet_path}")
    print("=" * 80)
    print()
    
    # Load the parquet
    try:
        df = pd.read_parquet(parquet_path)
    except Exception as e:
        print(f"Error loading parquet file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # General information
    print(f"Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
    print()
    
    # Column information
    print("Columns and types:")
    print("-" * 80)
    
    column_info = {}
    for col in df.columns:
        info = analyze_column(df, col)
        column_info[col] = info
        
        print(f"  {col}:")
        print(f"    Type: {info['type_info']}")
        print(f"    Non-null values: {info['non_null_count']} / {len(df)}")
        if info['null_count'] > 0:
            print(f"    Null values: {info['null_count']}")
        
        if info['stats']:
            stats = info['stats']
            print(f"    Statistics:")
            if stats.get('min') is not None:
                print(f"      min: {stats['min']}")
            if stats.get('max') is not None:
                print(f"      max: {stats['max']}")
            if stats.get('mean') is not None:
                print(f"      mean: {stats['mean']:.4f}")
        print()
    
    # Preview of the first 5 rows
    print("=" * 80)
    print("Preview (first 5 rows):")
    print("=" * 80)
    print()
    
    if len(df) == 0:
        print("  (Empty DataFrame)")
    else:
        print(df.head())
    
    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description="Print detailed information about a parquet file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "parquet_path",
        type=str,
        help="Path to the parquet file"
    )
    
    args = parser.parse_args()
    parquet_path = Path(args.parquet_path).resolve()
    
    print_parquet_info(parquet_path)


if __name__ == "__main__":
    main()

