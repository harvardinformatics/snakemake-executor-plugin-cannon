#!/bin/bash
#SBATCH --job-name=gpu-test
#SBATCH --output=%x-%j.out
#SBATCH --mail-type=ALL
#SBATCH --mail-user=gthomas@g.harvard.edu
#SBATCH --partition=gpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --mem=24g
#SBATCH --time=8:00:00
#SBATCH --gpus=2


ls test-out; cp -f test-out/test1.out test-out/test2.out 2> test-out/b.log
