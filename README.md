# KGbot dev

## General information

**The main notebook** is at [https://github.com/holobiomics-lab/kgbot/blob/dev/app/core/LLM_chain_agent.ipynb](https://github.com/holobiomics-lab/kgbot/blob/dev/app/core/LLM_chain_agent.ipynb)

We use the ```dev``` branch for pushing our contributions [https://github.com/holobiomics-lab/kgbot/tree/dev](https://github.com/holobiomics-lab/kgbot/tree/dev). Please create your own branch like (either user centric like```dev_benjamin``` or feature centric like ```dev_langgraph```) and do a pull request to the ```dev``` branch when ready for reviewing.

The prototype is in the ```prototype``` branch (frozen) [https://github.com/holobiomics-lab/kgbot/tree/prototype](https://github.com/holobiomics-lab/kgbot/tree/prototype)


## Environment setup

Conda is required for setting up the environment. For installation instructions, see: https://docs.conda.io/projects/conda/en/latest/user-guide/install/
1) Install conda
2) To install the environment from the `environment.yml` file, use the following command:
```sh
conda env create -f environment.yml
```