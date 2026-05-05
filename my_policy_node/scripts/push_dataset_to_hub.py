#!/usr/bin/env python3
"""
push_dataset_to_hub.py

Upload a locally-saved LeRobot dataset to HuggingFace Hub.

Usage:
  cd ~/ws_aic/src/aic
  pixi run python my_policy_node/scripts/push_dataset_to_hub.py \
    --root ~/datasets/sfp_insertion \
    --repo-id your_username/sfp_insertion_demos

You must be logged in first:
  pixi run huggingface-cli login
"""

import argparse
import os
from pathlib import Path

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',    required=True,  help='Local dataset directory')
    parser.add_argument('--repo-id', required=True,  help='HuggingFace repo, e.g. user/dataset')
    parser.add_argument('--private', action='store_true', default=True)
    parser.add_argument('--message', default='Auto-collected insertion demos')
    args = parser.parse_args()

    from lerobot.datasets import LeRobotDataset

    root = Path(args.root).expanduser()
    if not root.exists():
        raise FileNotFoundError(f"Dataset root not found: {root}")

    print(f"Loading dataset from {root} …")
    ds = LeRobotDataset(args.repo_id, root=root)

    print(f"Pushing {len(ds)} frames ({ds.num_episodes} episodes) to {args.repo_id} …")
    ds.push_to_hub(
        private=args.private,
        commit_message=args.message,
    )
    print(f"Done → https://huggingface.co/datasets/{args.repo_id}")


if __name__ == '__main__':
    main()
