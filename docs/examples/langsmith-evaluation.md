# LangSmith automated evaluation

To run the automated evaluation you need a **LangSmith API key**. Create an account and generate an API key using the LangSmith docs: [Create an account and API key](https://docs.langchain.com/langsmith/create-account-api-key).

Add the key to your repo-root `.env` (do not commit it), along with your LLM provider key:

```env
LANGCHAIN_API_KEY=your_langsmith_key   # or LANGSMITH_API_KEY
LANGCHAIN_PROJECT=MetaboT_Test_Run
OPENAI_API_KEY=your_openai_key
```

Then run (from the repository root):

```bash
python -m app.core.tests.evaluation
```

This starts the benchmark evaluation (running MetaboT on ~50 questions). LLM-based evaluators compare the generated answers with the reference answers. A link to the evaluation run will appear once the evaluation starts, and you can also find it later in your LangSmith account.

