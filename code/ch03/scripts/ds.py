# ds.py -- step a DecodeStream of the tokenizers library through token IDs
#   python3 ds.py gpt2/tokenizer.json 140 253 21169 18849 38857 16843 20375
# For these IDs, GPT-2's seven tokens of a Russian word of six letters,
# it prints None for the first and one whole letter for each of the rest.
import sys
from tokenizers import Tokenizer
from tokenizers.decoders import DecodeStream

tok = Tokenizer.from_file(sys.argv[1])
ds = DecodeStream(skip_special_tokens=False)
print([ds.step(tok, int(i)) for i in sys.argv[2:]])
