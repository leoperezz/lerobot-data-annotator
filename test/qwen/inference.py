import dotenv

dotenv.load_dotenv()

from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3.5-4B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

prompt = "Hello, how are you?"
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs)
print(outputs)