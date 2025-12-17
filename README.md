# Snakemake executor plugin: cannon (DEPRECATED)

**DEPRECATED AS OF 2025-12-17**

With the introduction of [automatic partition selection](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/slurm.html#automatic-partition-selection) in version 2.0.0 ([release notes](https://github.com/snakemake/snakemake-executor-plugin-slurm/releases/tag/v2.0.0)) of the main [snakemake-executor-plugin-slurm](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/slurm.html), the utility of this plugin has been obviated.

We now maintain a partition configuration file for the Cannon cluster that can be used with the regular SLURM plugin. See [our website](https://informatics.fas.harvard.edu/resources/snakemake-cannon-config/) for information on its usage.

No further updates or development will be done on this plugin.

This is a fork of the [SLURM executor plugin for Snakemake](https://github.com/snakemake/snakemake-executor-plugin-slurm) for the [Cannon cluster at Harvard University](https://docs.rc.fas.harvard.edu/kb/running-jobs/). It has all the same features as the SLURM plugin, but performs automatic partition selection for the Cannon cluster based on the resources specified in a given Snakemake rule. It also offers some error checking for partition selection.

For full documentation, see the [Snakemake plugin catalog](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/cannon.html).

## Installation

The executor can be installed [from PyPI](https://pypi.org/project/snakemake-executor-plugin-cannon/) with pip:

```bash
pip install snakemake-executor-plugin-cannon
```

Or [from bioconda](https://bioconda.github.io/recipes/snakemake-executor-plugin-cannon/README.html) with conda/mamba:

```bash
mamba install snakemake-executor-plugin-cannon
```

## Specifying the executor

To use the executor with Snakemake, either specify it in the command line as:

```bash
snakemake -e cannon ...
```

Or add it to your [profile](https://github.com/harvardinformatics/snakemake-executor-plugin-cannon/blob/main/docs/profile.md):

```YAML
executor: cannon
```

## Setting up your profile

While this plugin does automatic partition selection, the user is still responsible for specifying other resources for rules in their workflow. This is usually done through a cluster **profile**, but this may differ based on your workflow. 

See the [profile setup page](https://github.com/harvardinformatics/snakemake-executor-plugin-cannon/blob/main/docs/profile.md) for more information. 

An example profile can be found at [`tests/cannon-test-profile/config.yaml`](https://github.com/harvardinformatics/snakemake-executor-plugin-cannon/blob/main/tests/cannon-test-profile/config.yaml)

## Features

For full documentation, see the [Snakemake plugin catalog](https://snakemake.github.io/snakemake-plugin-catalog/plugins/executor/cannon.html).
