# Multi-Stage Interactive Legal Evaluation（MILE）Benchmark

To evaluate abilities of large language models(LLMs) to accomplish legal tasks as a lawyer in interactive scenarios, we introduce MILE benchmark. The dataset is sourced from China Judgements Online of the year 2024.


## Setting the API key

Before running the script, please open openai_config.py and enter your API keys for the required services.


## Input datasets

Enter input datasets file, and save datasets that need to be evaluated inside:

```plain
cd data
```


## Evaluating Performance

Please enter the source file:

```plain
cd ..
```
If you want to evaluate the interactive ability of a model, please execute：
```plain
python src\main.py --tasks=Interaction
```
If you want to evaluate the goal ability of a model, please execute：
```plain
python src\main.py --tasks=Goal
```


