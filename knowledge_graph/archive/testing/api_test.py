from openai import OpenAI

client = OpenAI(api_key="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")

models = client.models.list()
for model in models.data:
    print(model.id)
