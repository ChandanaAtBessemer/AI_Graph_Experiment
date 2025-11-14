import sys
sys.path.append('.')
from src.dspy_modules.add_similarity import SimilarityBuilder

builder = SimilarityBuilder()
try:
    count = builder.add_similarity_relationships(threshold=0.50)
    if count > 0:
        builder.get_similarity_stats()
        builder.verify_similarities()
finally:
    builder.close()
