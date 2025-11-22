#!/usr/bin/env python3
import sys
import argparse
import random
import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class Instance:
    id: int
    num_machines: int = 0
    jobs : List[int] = field(default_factory=list)

def generate_instance(instance_id: int, num_jobs: int, num_machines: int, max_duration: int) -> Instance:
    jobs: List[int] = []
    for _ in range(1, num_jobs + 1):
        jobs.append(random.randint(1, max_duration))
    return Instance(id=instance_id, num_machines=num_machines, jobs=jobs)

def save_instances(path: Path, instances: List[Instance]) -> None:
    """
    Save multiple instances to path, one YAML document per instance (separated by ---).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    docs = (asdict(inst) for inst in instances)
    
    with path.open("w") as fh:
        yaml.safe_dump_all(docs, fh, default_flow_style=None, sort_keys=False, explicit_start=True)

def main():
    p = argparse.ArgumentParser(description="Generate random scheduling instances and dump to YAML.")
    p.add_argument("-n", "--instances", type=int, default=1, help="number of instances to generate")
    p.add_argument("-j", "--jobs", type=int, default=20, help="jobs per instance")
    p.add_argument("-m", "--machines", type=int, default=3, help="number of machines")
    p.add_argument("-d", "--max-duration", type=int, default=10, help="maximum job duration")
    p.add_argument("-s", "--seed", type=int, default=random.randrange(sys.maxsize), help="random seed")
    p.add_argument("-o", "--output", type=Path, default=Path("./instances/scheduling_instances.yaml"), help="output YAML file")
    args = p.parse_args()
    
    random.seed(args.seed)

    instances: List[Instance] = [
        generate_instance(i, args.jobs, args.machines, args.max_duration) 
        for i in range(args.instances)
        ]

    save_instances(args.output, instances)

    print(f"Wrote {len(instances)} instance(s) to {args.output}")

if __name__ == "__main__":
    main()