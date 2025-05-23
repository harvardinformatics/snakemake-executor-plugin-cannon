### How this Plugin works

This plugin is based off of the general SLURM plugin, but with added logic for automatic partition selection specifically on the Cannon cluster at Harvard University. With this plugin, Snakemake submits itself as a job script when operating on the Cannon cluster. 
Consequently, the SLURM log file will duplicate the output of the corresponding rule.
To avoid redundancy, the plugin deletes the SLURM log file for successful jobs, relying instead on the rule-specific logs.

Remote executors submit Snakemake jobs to ensure unique functionalities — such as piped group jobs and rule wrappers — are available on cluster nodes.
The memory footprint varies based on these functionalities; for instance, rules with a run directive that import modules and read data may require more memory.

#### Usage Hints

Install this plugin into your Snakemake base environment using conda.
This process also installs the 'jobstep' plugin, utilized on cluster nodes.
Additionally, we recommend installing the `snakemake-storage-plugin-fs` for automated stage-in and stage-out procedures.

#### Reporting Bugs and Feature Requests

We welcome bug reports and feature requests!
Please report issues specific to this plugin [in the plugin's GitHub repository](https://github.com/harvardinformatics/snakemake-executor-plugin-cannon/issues).
For other concerns, refer to the [Snakemake main repository](https://github.com/snakemake/snakemake/issues) or the relevant Snakemake plugin repository.
Cluster-related issues should be directed to [FAS Research Computing](https://www.rc.fas.harvard.edu/) or [FAS Informatics](https://informatics.fas.harvard.edu/).

### Partition selection

On a computinng cluster, a **partition** designates a subset of compute nodes grouped for specific purposes, such as high-memory or GPU tasks.

The Cannon plugin uses the provided resources (see below) to best place a job on a [partition on the cluster](https://docs.rc.fas.harvard.edu/kb/running-jobs/). Briefly, the plugin first checks if any GPUs are required and, if so, assigns the job to the *gpu* partition. Next, if the job requires a lot of memory, it will be assigned to one of the *bigmem* partitions. If the job requires many CPUs, it will be assigned to *intermediate* or *sapphire* depending on memory an runtime requirements. If the job doesn't exceed either the memory or CPU threshold, it will be put on the *shared* partition.

If a partition for a particular rule is provided in the rule, the command line, or in the profile, that partition will be used regardless.

After partition selection, the plugin does some checks to ensure the selected partition has the resources requested and will inform the user if not.

### Specifying Account

In SLURM, an **account** is used for resource accounting and allocation.

This resource is typically omitted from Snakemake workflows to maintain platform independence, allowing the same workflow to run on different systems without modification.

To specify it at the command line, define it as default resources:

``` console
$ snakemake --executor cannon --default-resources slurm_account=<your SLURM account>
```

The plugin does its best to _guess_ your account. That might not be possible. Particularly, when dealing with several SLURM accounts, users ought to set them per workflow.
Some clusters, however, have a pre-defined default per user and _do not_ allow users to set their account or partition. The plugin will always attempt to set an account. To override this behavior, the `--slurm-no-account` flag can be used.

If individual rules require *e.g.* a different partition, you can override the default per rule:

``` console
$ snakemake --executor cannon --default-resources slurm_account=<your SLURM account> slurm_partition=<your SLURM partition> --set-resources <somerule>:slurm_partition=<some other partition>
```

To ensure consistency and ease of management, it's advisable to persist such settings via a [configuration profile](https://snakemake.readthedocs.io/en/latest/executing/cli.html#profiles), which can be provided system-wide, per user, or per workflow.

By default, the executor waits 40 seconds before performing the first job status check.
This interval can be adjusted using the `--slurm-init-seconds-before-status-checks=<time in seconds>` option, which may be useful when developing workflows on an HPC cluster to minimize turn-around times.

### Configuring SMP Jobs in Snakemake with the SLURM Executor Plugin

In Snakemake workflows, many jobs are executed by programs that are either single-core scripts or multithreaded applications, which are categorized as SMP ([**S**hared **M**memory **P**rocessing](https://en.wikipedia.org/wiki/Shared_memory)) jobs.
To allocate resources for such jobs using the SLURM executor plugin, you can specify the required number of CPU cores and memory directly within the resources section of a rule.
Here's how you can define a rule that requests 8 CPU cores and 14 GB of memory:

``` python
rule a:
    input: ...
    output: ...
    threads: 8
    resources:
        mem_mb=14000
```

Snakemake knows the `cpus_per_task`, similar to SLURM, as an alternative to `threads`.
Parameters in the `resources` section will take precedence.

The following resource flags (and default values) are available to be set in rules, with there being multiple ways to specify the amount of memory for a job.

| Resources     | Default Value | Units                                    | 
|---------------|:-------------:|:----------------------------------------:|
| mem           | 4G            | G (gigabyte), M (megabyte), T (terabyte) |
| mem_mb        | 4000          | megabyte                                  |
| mem_gb        | 4             | gigabyte                                  |
| runtime       | 30m           | m (minutes), h (hours), d (days)         |
| cpus_per_task | 1             |                                          |

If you want to specify usage of GPUs in resources, you will have to use the `slurm_extra` tag, which there are examples of below in the GPU Jobs section.

To avoid hard-coding resource parameters into your Snakefiles, it is advisable to create a cluster-specific workflow profile.
This profile should be named `config.yaml` and placed in a directory named `profiles` relative to your workflow directory.
You can then indicate this profile to Snakemake using the `--workflow-profile` profiles option.
Here's an example of how the `config.yaml` file might look:

```YAML
default-resources:
    slurm_account: "<account>"
    slurm_partition: "<default partition>"
    mem_mb_per_cpu: 1800 # take a sensible default for your cluster
    runtime: "30m"

# here only rules, which require different (more) resources:
set-resources:
    rule_a:
        runtime: "2h"

    rule_b:
        mem_mb_per_cpu: 3600
        runtime: "5h"

# parallelization with threads needs to be defined separately:
set-threads:
    rule_b: 64
```

In this configuration:

- `default-resources` sets the default SLURM account, partition, memory per CPU, and runtime for all jobs.
- `set-resources` allows you to override these defaults for specific rules, such as `rule_a` and `rule_b`
- `set-threads` specifies the number of `threads` for particular rules, enabling fine-grained control over parallelization.

By utilizing a configuration profile, you can maintain a clean and platform-independent workflow definition while tailoring resource specifications to the requirements of your SLURM cluster environment.

#### Cannon plugin profile example

Because profiles may contain multiple files, the profile argument is passed a directory path. However, for resource specification, the file you need to create is `config.yaml`, in which you can specify the resources for the rules of your pipeline, *e.g.* for a workflow with rules named *a* and *b*:

```YAML
executor: cannon

set-resources:
  a:
    slurm_partition: sapphire
    mem: 5G
    cpus_per_task: 1
    runtime: 30m

  b:
    mem: 10G
    cpus_per_task: 4
    runtime: 2h
    slurm_extra: "'--gres=gpu:2'"
```

Note that the `slurm_partition:` specification can be blank or omitted, as in rule *b*, since this plugin will select the partition for you based on the other resources provided. However, if `slurm_partition:` is provided with a value, as in rule *a*, that partition will be used.

Any resource fields implemented in Snakemake are available to be used in the profile and with this plugin, but only memory (`mem:` or `mem_mb:` or `mem_gb`), `cpus_per_task:`, `runtime:`, and GPUs via `slurm_extra:` (see below) will affect partition selection. If fields are left blank, the plugin has default values to fall back on.

In summary, the following resource flags (and default values) are available to be set in rules, with there being multiple ways to specify the amount of memory for a job.

| Resources       | Default Value | Units                                    | 
|-----------------|:-------------:|:----------------------------------------:|
| `mem`           | 4G            | G (gigabyte), M (megabyte), T (terabyte) |
| `mem_mb`        | 4000          | megabyte                                 |
| `mem_gb`        | 4             | gigabyte                                 |
| `runtime`       | 30m           | m (minutes), h (hours), d (days)         |
| `cpus_per_task` | 1             |                                          |

Note that only one of `mem`, `mem_gb`, and `mem_mb` should be set. If multiple are set, only one will be used with the order of precedence being `mem` > `mem_gb` > `mem_mb`.

###### Setting GPUs

Currently, on the Cannon cluster, this plugin only supports GPU specification via the `slurm_extra:` field. See your *b* above for an example requesting 2 GPUs.

###### Example profile

As a template, you can use the [`tests/cannon-test-profile/config.yaml`](https://github.com/harvardinformatics/snakemake-executor-plugin-cannon/blob/main/tests/cannon-test-profile/config.yaml), which will need to be modified with the necessary changes for the workflow that you want to run.


###### Specifying the executor in the profile

Note the first line of the profile:

```YAML
executor: cannon
```

This tells Snakemake which plugin to use to execute job submission. Alternatively, if this line is excluded from the profile, one could specify the plugin directly from the command line:

```bash
snakemake -e cannon ...
```

Either method is acceptable.

### MPI jobs

Snakemake's SLURM executor supports the execution of MPI ([Message Passing Interface](https://en.wikipedia.org/wiki/Message_Passing_Interface)) jobs, facilitating parallel computations across multiple nodes.
To effectively utilize MPI within a Snakemake workflow, it's recommended to use `srun` as the MPI launcher when operating in a SLURM environment.

Here's an example of defining an MPI rule in a Snakefile:

``` python
rule calc_pi:
  output:
      "pi.calc",
  log:
      "logs/calc_pi.log",
  resources:
      tasks=10,
      mpi="srun",
  shell:
      "{resources.mpi} -n {resources.tasks} calc-pi-mpi > {output} 2> {log}"
```

In this configuration:

- `tasks=10` specifies the number of MPI tasks (ranks) to be allocated for the job.
- `mpi="srun"` sets srun as the MPI launcher, which is optimal for SLURM-managed clusters.
- The `shell` directive constructs the command to execute the MPI program, utilizing the specified resources.

#### Portability Considerations

While SLURM's `srun` effectively manages task allocation, including the `-n {resources.tasks}` option ensures compatibility with some applications that may rely on `mpiexec` or similar MPI launchers.
This approach maintains the portability of your workflow across different computing environments.

To adapt the workflow for an application using `mpiexec`, you can override the `mpi` resource at runtime:

``` console
$ snakemake --set-resources calc_pi:mpi="mpiexec" ...
```

#### Resource Specifications for MPI Jobs

When configuring MPI jobs, it's essential to accurately define the resources to match the requirements of your application.
The tasks resource denotes the number of MPI ranks.
For hybrid applications that combine MPI with multi-threading, you can specify both `tasks` and `cpus_per_task`:

```YAML
set-resources:
    mpi_rule:
        tasks: 2048

    hybrid_mpi_rule:
        tasks: 1024
        cpus_per_task: 2
```

In this setup:

- `mpi_rule` is allocated 2048 MPI tasks.
- `hybrid_mpi_rule` is assigned 1024 MPI tasks, with each task utilizing 2 CPU cores, accommodating applications that employ both MPI and threading.

For advanced configurations, such as defining specific node distributions or memory allocations, you can utilize the `slurm_extra` parameter to pass additional SLURM directives, tailoring the job submission to the specific needs of your computational tasks.

### GPU Jobs

Integrating GPU resources into Snakemake workflows on SLURM-managed clusters requires precise configuration to ensure optimal performance.
SLURM facilitates GPU allocation using the `--gres` (generic resources) or `--gpus` flags, and Snakemake provides corresponding mechanisms to request these resources within your workflow rules.

#### Specifying GPU Resources in Snakemake

To request GPU resources in Snakemake, you can utilize the `gpu` resource within the resources section of a rule.
This approach allows you to specify the number of GPUs and, optionally, the GPU model.
For example:

```Python
rule gpu_task:
    input:
        "input_file"
    output:
        "output_file"
    resources:
        slurm_extra: "'--gres=gpu:a100:2'"
    shell:
        "your_gpu_application --input {input} --output {output}"
```

In this configuration:

- `gpu:a100:2` requests two GPUs of the a100 model for the job

Snakemake translates these resource requests into SLURM's `--gpus` flag, resulting in a submission command like sbatch `--gpus=a100:2`.
It is important to note that the `gpu` resource must be specified as a numerical value.

.. note:: Internally, Snakemake knows the resource `gpu_manufacturer`, too.
However, SLURM does not know the distinction between model and manufacturer.
Essentially, the preferred way to request an accelerator will depend on your specific cluster setup.


#### Additional Considerations: CPU Allocation per GPU

When configuring GPU jobs, it's crucial to allocate CPU resources appropriately to ensure that GPU tasks are not bottlenecked by insufficient CPU availability.
You can specify the number of CPUs per GPU using the `cpus_per_gpu` resource:

```Python
rule gpu_task:
    input:
        "input_file"
    output:
        "output_file"
    resources:
        gpu=1,
        cpus_per_gpu=4
    shell:
        "your_gpu_application --input {input} --output {output}"
```

In this example, `cpus_per_gpu=4` allocates four CPU cores for each GPU requested.

.. note:: If `cpus_per_gpu` is set to a value less than or equal to zero, Snakemake will not include a CPU request in the SLURM submission, and the cluster's default CPU allocation policy will apply.

#### Sample Workflow Profile for GPU Jobs

To streamline the management of resource specifications across multiple rules, you can define a workflow profile in a `config.yaml` file:

```YAML
set-resources:
    single_gpu_rule:
        slurm_extra: "'--gres=gpu:1'"
        cpus_per_gpu: 4

    multi_gpu_rule:
        slurm_extra: "'--gres=gpu:a100:2'"
        cpus_per_gpu: 8

    gres_request_rule:
        slurm_extra: "'--gres=gpu:rtx3090:2'"
        cpus_per_gpu: 6
```

In this configuration:

- `single_gpu_rule` requests one GPU with four CPUs allocated to it.
- `multi_gpu_rule` requests two GPUs of the a100 model, with eight CPUs allocated per GPU.
- `gres_request_rule` utilizes the `gres` resource to request two rtx3090 GPUs, with six CPUs allocated per GPU.

By defining these resource specifications in a profile, you maintain a clean and organized workflow, ensuring that resource allocations are consistent and easily adjustable.

#### Important Note

The preferred method for requesting GPU resources -- whether using `gpu` or `gres` -- depends on your specific cluster configuration and scheduling policies.
Consult your cluster administrator or the cluster's documentation to determine the best approach for your environment.
Additionally, while Snakemake internally recognizes the `gpu_manufacturer` resource, SLURM does not distinguish between GPU model and manufacturer in its resource allocation.
Therefore, it's essential to align your Snakemake resource definitions with your cluster's SLURM configuration to ensure accurate resource requests.

By carefully configuring GPU resources in your Snakemake workflows, you can optimize the performance of GPU-accelerated tasks and ensure efficient utilization of computational resources within SLURM-managed clusters.

### Running Jobs locally

In Snakemake workflows executed within cluster environments, certain tasks -- such as brief data downloads or plotting -- are better suited for local execution on the head node rather than being submitted as cluster jobs.
To designate specific rules for local execution, Snakemake offers the localrules directive.
This directive allows you to specify a comma-separated list of rules that should run locally:

```Python
localrules: <rule_a>, <rule_b>
```

### Advanced Resource Specifications

In Snakemake workflows executed on SLURM clusters, it's essential to map Snakemake's resource specifications to SLURM's resource management parameters.
This ensures that each job receives the appropriate computational resources.
Below is a guide on how to align these specifications:

#### Mapping Snakemake Resources to SLURM Parameters

Snakemake allows the definition of resources within each rule, which can be translated to corresponding SLURM command-line flags:

- Partition: Specifies the partition or queue to which the job should be submitted.
  - Snakemake resource: `slurm_partition`
  - SLURM flag: `--partition` or `-p`
- Runtime: Defines the walltime limit for the job, typically in minutes.
  - Snakemake resource: `runtime`
  - SLURM flag: `--time` or `-t`
- Memory: Specifies the memory requirements for the job.
  - Snakemake resource: `mem_mb` (total memory in MB) or `mem_mb_per_cpu` (memory per CPU in MB)
  - SLURM flags: `--mem` (for total memory) or `--mem-per-cpu` (for memory per CPU)
- Constraints: Sets specific hardware or software constraints for the job.
  - Snakemake resource: `constraint`
  - SLURM flag: `--constraint` or `-C`

#### Example of Rule Definition with Resource Specifications

Here is how you can define a rule in Snakemake with specific SLURM resource requirements:

```Python
rule example_rule:
    input: "input_file.txt"
    output: "output_file.txt"
    resources:
        slurm_partition="compute",
        runtime=120,  # in minutes
        mem_mb=8000,  # total memory in MB
        cpus_per_task=4
    shell:
        "cmd {input} {output}"
```
In this example, the job will be submitted to the 'compute' partition, with a runtime limit of 120 minutes, 8 GB of total memory, and 4 CPUs allocated.

#### Important Considerations

Mutual Exclusivity of Memory Flags: SLURM's `--mem` and `--mem-per-cpu` flags are mutually exclusive.
Therefore, in Snakemake, you should use either `mem_mb` or `mem_mb_per_cpu`, but not both simultaneously.

Avoid Hardcoding Cluster-Specific Resources: To maintain workflow portability across different computing environments, it's advisable to avoid embedding cluster-specific resource requests (like constraint) directly within your workflow rules.
Instead, utilize Snakemake's `--default-resources` and `--set-resources` command-line options or define them within a configuration profile.

#### Using Configuration Profiles for Resource Specifications

A more flexible approach to manage resource specifications is by using Snakemake profiles.
These profiles allow you to define default resources and rule-specific overrides in a centralized configuration file, enhancing the portability and maintainability of your workflows.

Example of a Snakemake Profile Configuration (`config.yaml`):

```YAML
default-resources:
    slurm_partition: "default_partition"
    slurm_account: "your_account"
    mem_mb_per_cpu: 2000
    runtime: 60  # in minutes

set-resources:
    special_rule:
        slurm_partition: "high_mem_partition"
        runtime: 180  # in minutes
        mem_mb_per_cpu: 4000
        cpus_per_task: 8
```

In this configuration:
- Default resources are set for all rules, specifying the partition, account, memory per CPU, and runtime.
- The special_rule has customized resources, overriding the defaults where specified.

To apply this profile during workflow execution, use the --profile option:

```console
snakemake --profile path/to/profile
```

By leveraging configuration profiles, you can tailor resource specifications to different computing environments without modifying the core workflow definitions, thereby enhancing reproducibility and flexibility.

#### Multicluster Support

In Snakemake, specifying the target cluster for a particular rule is achieved using the `cluster` resource flag within the rule definition.
This allows for precise control over job distribution across different clusters.
For example:

```YAML
default-resources:
    cluster: "default_cluster"

set-resources:
    specific_rule:
        cluster: "high_memory_cluster"
    another_rule:
        cluster: "gpu_cluster"
```

In this configuration, `default-resources` sets a default cluster for all rules, while `set-resources` specifies clusters for individual rules as needed.
This method ensures that your workflow is adaptable to various computing environments without hardcoding cluster-specific details into your `Snakefile`.
Multicluster support is achieved in a comma separated list:

```YAML
set-resources:
   multicluster_rule:
       cluster: "cluster1,cluster2"
```

#### Additional Custom Job Configuration

SLURM installations can support custom plugins, which may add support
for additional flags to `sbatch`.
In addition, there are various batch options not directly supported via the resource definitions
shown above.
You may use the `slurm_extra` resource to specify
additional flags to `sbatch`:

``` python
rule myrule:
    input: ...
    output: ...
    resources:
        slurm_extra="'--qos=long --mail-type=ALL --mail-user=<your email>'"
```

Again, rather use a [profile](https://snakemake.readthedocs.io/en/latest/executing/cli.html#profiles) to specify such resources.

### Software Recommendations

#### Conda

Snakemake is commonly used with software deployment via conda ([`snakemake --software-deployment-method conda ...`](https://snakemake.readthedocs.io/en/stable/snakefiles/deployment.html#integrated-package-management).
On a cluster sometimes a file system other than `HOME` needs to be indicated (for example because of quotas).
In this case pointing the installation to different file system with `--conda-prefix /other/filesystem` might be a solution.
You can use `--conda-cleanup-pkgs` to further save space by removing downloaded tarballs.

#### Using Cluster Environment:  Modules

HPC clusters provide so-called environment modules.
To require installation with environment modules you can use `--sdm env-modules`, for example for a specific rule:

```
rule ...:
   ...
   envmodules:
       "bio/VinaLC"
```

This will trigger a `module load bio VinaLC` immediately before to execution.


Note, that 
- environment modules are best specified in a configuration file.
- Using environment modules can be combined with conda and apptainer (`--sdm env-modules conda apptainer`), which will then be only used as a fallback for rules not defining environment modules.

### Inquiring about Job Information and Adjusting the Rate Limiter

The executor plugin for SLURM uses unique job names to inquire about job status.
It ensures inquiring about job status for the series of jobs of a workflow does not put too much strain on the batch system's database.
Human readable information is stored in the comment of a particular job.
It is a combination of the rule name and wildcards.
You can ask for it with the `sacct` or `squeue` commands, for example:

``` console 
sacct -o JobID,State,Comment%40
```

Note, the "%40" after `Comment` ensures a width of 40 characters.
This setting may be changed at will.
If the width is too small, SLURM will abbreviate the column with a `+` sign.

For running jobs, you can use the squeue command:

``` console
squeue -u $USER -o %i,%P,%.10j,%.40k
```

Here, the `.<number>` settings for the ID and the comment ensure a sufficient width, too.

Snakemake will check the status of your jobs 40 seconds after submission.
Another attempt will be made in 10 seconds, then 20, etcetera with an upper limit of 180 seconds.

### Using Profiles

Utilizing Snakemake [profiles](https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles) streamlines workflow execution by consolidating configuration settings into dedicated directories, simplifying command-line operations.

#### Setting Up a Global Profile:

- Create a Profile Directory: If cluster administrators did not set up a global profile at `/etc/xdg/snakemake` users can opt for individual profiles.
  Establish a directory at `$HOME/.config/snakemake`.
- The default profile will be used when specifying the `--profile`.
  It can also be set via the environment variable `SNAKEMAKE_PROFILE`, for example by specifying export `SNAKEMAKE_PROFILE=myprofile` in your `~/.bashrc`.
  Then the --profile flag can be omitted.

A sample configuration looks like this:

```YAML
executor: slurm
latency-wait: 5
default-storage-provider: fs
shared-fs-usage:
  - persistence
  - software-deployment
  - sources
  - source-cache
remote-job-local-storage-prefix: "<your node local storage prefix>"
local-storage-prefix: "<your local storage prefix, for example on login nodes>"
```


In this configuration:
- `executor: slurm`: Specifies the SLURM executor for job scheduling.
The corresponding command line flag is not needed anymore.
- `latency-wait: 5`: Sets a 5-second latency wait to accommodate file system delays.
- `default-storage-provider: fs`: Utilizes the file system storage plugin for file handling.
- `shared-fs-usage:` Lists storage categories to be managed via the shared file system.
  - `remote-job-local-storage-prefix:` Defines the storage prefix for remote jobs; adjust based on your cluster's scratch directory structure.
  - `local-storage-prefix:` Specifies the storage prefix for local jobs, such as on login nodes.

Using the [file system storage plugin](https://github.com/snakemake/snakemake-storage-plugin-fs) will automatically stage-in and -out in- and output files.


==This is ongoing development.
Eventually, you will be able to annotate different file access patterns.==

### Log Files - Getting Information on Failures

Snakemake's SLURM executor submits itself as a job, ensuring that all features function correctly within the job context.
SLURM requires a log file for every job, which can lead to redundancy since Snakemake's output is already displayed in the terminal.
However, if a rule includes a `log` directive, SLURM logs will contain only Snakemake's output.

By default, the SLURM executor deletes log files of successful jobs immediately after completion (remember: this is redundant information).
To modify this behavior and retain logs of successful jobs, use the `--slurm-keep-successful-logs` flag.
Additionally, log files for failed jobs are preserved for 10 days by default.
To change this retention period, use the `--slurm-delete-logfiles-older-than` flag.

Snakemake's log files are typically stored in the directory where the workflow is initiated or in the directory specified with the `--directory` flag.
To redirect SLURM logs produced by Snakemake to a specific directory, use the `--slurm-logdir` flag.
To prevent log files from accumulating in various directories, consider storing them in your home directory.
For example, add the following to your Snakemake profile:

```YAML
slurm-logdir: "/home/<username>/.snakemake/slurm_logs"
```

Replace <username> with your actual username.
This configuration directs SLURM logs to a centralized location, making them easier to manage.

### Retries - Or Trying again when a Job failed

When running workflows on SLURM-managed clusters, it's common for jobs to occasionally fail.
Snakemake provides mechanisms to handle such failures gracefully, allowing for automatic retries and workflow resumption.

#### Retrying Failed Jobs

To instruct Snakemake to automatically retry failed jobs, use the `--retries` option followed by the desired number of attempts.
For example, to retry up to three times:

```console
snakemake --retries=3
```

If a workflow encounters multiple failures, you can resume it by re-running incomplete jobs with:

```console
snakemake ... --rerun-incomplete
# or the short-hand version
snakemake ... --ri
```

#### Automatic Job Requeuing in SLURM

SLURM offers a job requeue feature that allows jobs to be automatically resubmitted if they fail or are preempted, preserving job IDs and priorities.
To enable this feature with Snakemake, use the `--slurm-requeue` option.
This is similar to Snakemake's `--retries`, except a SLURM job will not be considered failed and priority may be accumulated during pending.
This might be the default on your cluster, already.
You can check your cluster's requeue settings with 

```console
scontrol show config | grep Requeue
```

If job requeuing is not enabled on your cluster, consider adding `--slurm-requeue` for your Snakemake jobs:

```console
snakemake --slurm-requeue ...
```

To prevent failures due to faulty parameterization, we can dynamically adjust the runtime behaviour:

### Dynamic Parameterization

Using dynamic parameterization we can react on different inputs and prevent our HPC jobs from failing.

#### Adjusting Memory Requirements

Input size of files may vary.
[If we have an estimate for the RAM requirement due to varying input file sizes, we can use this to dynamically adjust our jobs.](https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#dynamic-resources)

#### Adjusting Runtime

Runtime adjustments can be made in a Snakefile:

```Python
def get_time(wildcards, attempt):
    return f"{1 * attempt}h"

rule foo:
    input: ...
    output: ...
    resources:
        runtime=get_time
    ...
```

or in a workflow profile

```YAML
set-resources:
    foo:
        runtime: f"{1 * attempt}h"
```

Be sure to use sensible settings for your cluster and make use of parallel execution (for example threads) and [global profiles](#using-profiles) to avoid I/O contention.



### Nesting Jobs (or Running this Plugin within a Job)

Running Snakemake within an active SLURM job can lead to unpredictable behavior, as the execution environment may not be properly configured for job submission.
To mitigate potential issues, the SLURM executor plugin detects when it's operating inside a SLURM job and issues a warning, pausing for 5 seconds before proceeding.

### Summary:

When put together, a frequent command line looks like:

```console
$ snakemake -j unlimited \ # assuming an unlimited number of jobs
> --workflow-profile <profile directory with a `config.yaml`>
> --configfile config/config.yaml \
> --directory <path> # assuming a data path on a different file system than the workflow
```

### Frequently Asked Questions

#### Should I run Snakemake on the Login Node of my Cluster?

Running Snakemake on a cluster's login node is generally acceptable, as the primary Snakemake process is not resource-intensive.
However, some High-Performance Computing (HPC) administrators may discourage running job management processes like Snakemake on the login node, as it is typically intended for interactive use and not for executing computational tasks.
It's advisable to consult with your cluster's support team to understand any policies or guidelines regarding this practice.

To assess the impact of running Snakemake on the login node, you can measure the CPU time consumed by Snakemake during workflow execution.
For example, using the `/usr/bin/time -v` command to profile Snakemake's resource usage:

```console
/usr/bin/time -v snakemake ...
```

This command provides detailed statistics, including the CPU time used.
Sharing such metrics with your HPC administrators can help evaluate whether running Snakemake on the login node aligns with cluster usage policies.

We provide this table of measurements:

| Workflow | Version | Number of local rules  | Total Runtime (hh:mm:ss) | CPU-Time on the login node [user + system] (s) | Fraction |
|:-------------|:---------------|:---------------|:-------------|:-------------|:-------------:|
| [Transcriptome DiffExp + Fusion detection](https://github.com/snakemake-workflows/transcriptome-differential-expression) | 0.2.0 | 12 | 9:15:43 | 225.15 | 0.68 % |

If you want to contribute similar statistics, please run `/usr/bin/time -v snakemake ...` on your cluster and submit your stats as an [issue to the plugin repo on GitHub](https://github.com/snakemake/snakemake-executor-plugin-slurm/issue).

#### My Administrators do not let me run Snakemake on a Login Node

Running Snakemake within a SLURM job can lead to unpredictable behavior, as the execution environment may not be properly configured for job submission.
The SLURM executor plugin detects when it's operating inside a SLURM job and issues a warning, pausing for 5 seconds before proceeding.

If your administrators require running Snakemake within a job and encounter issues, please report the specific problems as issues on the plugin's GitHub repository.
While it may be possible to adapt the plugin for different cluster configurations, it's important to note that the plugin is primarily designed for use in production environments, and not all specialized cluster setups can be accounted for.
