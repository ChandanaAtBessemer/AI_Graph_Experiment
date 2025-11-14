import sys
sys.path.append('.')
from src.dspy_modules.add_similarity import SimilarityBuilder

builder = SimilarityBuilder()

# Get embeddings
responses = builder.get_all_responses()
embeddings = {}

print("Getting embeddings for 10 sample responses...")
for resp in responses[:10]:
    embeddings[resp['id']] = {
        'text': resp['text'],
        'embedding': builder.get_embedding(resp['text'])
    }

print("\nCalculating all pairwise similarities:\n")

ids = list(embeddings.keys())
for i, id1 in enumerate(ids):
    for id2 in ids[i+1:]:
        sim = builder.cosine_similarity(
            embeddings[id1]['embedding'],
            embeddings[id2]['embedding']
        )
        print(f"{sim:.3f}: {embeddings[id1]['text'][:40]}... | {embeddings[id2]['text'][:40]}...")

builder.close()
