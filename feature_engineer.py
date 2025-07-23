# feature_engineer.py (v4.2 - spaCy Batching Fix)

import os
import json
import logging
import pandas as pd
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from community import community_louvain
import numpy as np
import argparse
from collections import Counter
import spacy
from datetime import datetime
from tqdm import tqdm

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Helper Functions ---

def load_all_articles(processed_dir: str) -> list:
    """Loads all processed JSON files from the target directory."""
    logging.info(f"Loading all articles from '{processed_dir}'...")
    articles = []
    if not os.path.exists(processed_dir):
        logging.error(f"Directory not found: {processed_dir}")
        return []
        
    for filename in os.listdir(processed_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(processed_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    articles.append(json.load(f))
                except json.JSONDecodeError:
                    logging.warning(f"Could not decode JSON from {filename}")
    logging.info(f"Successfully loaded {len(articles)} articles.")
    return articles

def save_json(data: any, filepath: str):
    """Saves data to a JSON file with logging."""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Successfully saved data to '{filepath}'")
    except Exception as e:
        logging.error(f"Failed to save data to '{filepath}': {e}")

# --- Main Functions for Each Modality ---

def calculate_tfidf_fingerprints(articles: list, top_n: int = 20) -> dict:
    """MODALITY 1: Lexical & N-gram Analysis."""
    logging.info("Modality 1: Calculating TF-IDF fingerprints...")
    corpus = [article.get('text_with_placeholders', '') for article in articles]
    urls = [article.get('url') for article in articles]
    custom_stop_words = list(ENGLISH_STOP_WORDS) + ["al", "ibn"]
    vectorizer = TfidfVectorizer(ngram_range=(1, 3), stop_words=custom_stop_words, max_df=0.8, min_df=5)
    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = np.array(vectorizer.get_feature_names_out())
    
    article_keywords = {}
    for i, url in enumerate(urls):
        row = tfidf_matrix[i]
        if row.nnz > top_n:
            top_indices_in_data = np.argpartition(row.data, -top_n)[-top_n:]
            top_feature_indices = row.indices[top_indices_in_data]
            top_keywords = feature_names[top_feature_indices].tolist()
        elif row.nnz > 0:
            top_keywords = feature_names[row.indices].tolist()
        else:
            top_keywords = []
        article_keywords[url] = top_keywords
    
    logging.info(f"Generated keyword fingerprints for {len(article_keywords)} articles.")
    return article_keywords

def build_citation_communities(articles: list) -> list:
    """MODALITY 2: Explicit Citation Graph."""
    logging.info("Modality 2: Building citation graph and finding communities...")
    G = nx.DiGraph()
    for article in articles:
        G.add_node(article['url'], title=article['title'])
    for article in articles:
        for dest_url in article.get('related_entries', []):
            if dest_url in G:
                G.add_edge(article['url'], dest_url)
    partition = community_louvain.best_partition(G.to_undirected())
    communities = {}
    for node, community_id in partition.items():
        communities.setdefault(community_id, []).append(node)
    logging.info(f"Detected {len(communities)} citation-based communities.")
    return list(communities.values())

def extract_entities_and_concepts(articles: list) -> dict:
    """MODALITY 4: Linguistic Entity & Concept Analysis using spaCy."""
    logging.info("Modality 4: Extracting entities and concepts with spaCy...")
    try:
        nlp = spacy.load("en_core_web_lg")
    except OSError:
        logging.error("spaCy model 'en_core_web_lg' not found. Please run: python -m spacy download en_core_web_lg")
        return {}
    
    article_entities = {}
    texts = (article.get('text_with_placeholders', '') for article in articles)
    urls = [article.get('url') for article in articles]
    
    # --- OPTIMIZATION: Use batch_size for memory efficiency and progress feedback ---
    # This processes articles in chunks, which is much faster and less memory-intensive.
    # n_process=-1 tells spaCy to use all available CPU cores.
    docs_pipe = nlp.pipe(texts, disable=["lemmatizer"], batch_size=50, n_process=-1)
    
    for i, doc in enumerate(tqdm(docs_pipe, total=len(articles), desc="Extracting Entities")):
        url = urls[i]
        people = list(set(ent.text for ent in doc.ents if ent.label_ == "PERSON"))
        works = list(set(ent.text for ent in doc.ents if ent.label_ == "WORK_OF_ART"))
        concepts = list(set(chunk.text.lower() for chunk in doc.noun_chunks if len(chunk.text.split()) > 1))
        
        article_entities[url] = {
            "people": people,
            "works": works,
            "concepts": concepts
        }
    logging.info(f"Extracted entities for {len(article_entities)} articles.")
    return article_entities

def find_bridge_articles(community_urls: set, all_article_keywords: dict, core_concepts: set, similarity_threshold: float = 0.2) -> list:
    """Finds articles that are not in the community but are thematically similar."""
    bridge_articles = []
    for url, keywords in all_article_keywords.items():
        if url not in community_urls:
            article_keyword_set = set(keywords)
            if not article_keyword_set: continue
            intersection = article_keyword_set.intersection(core_concepts)
            if len(intersection) / len(article_keyword_set) >= similarity_threshold:
                bridge_articles.append(url)
    return bridge_articles

def main():
    """Main function to run the feature engineering pipeline and save all artifacts."""
    parser = argparse.ArgumentParser(description="Concept Discovery Engine for the SEP corpus (v4 - NER).")
    parser.add_argument("--input-dir", default="processed_articles", help="Directory containing the processed JSON files.")
    parser.add_argument("--output-dir-base", default="engineered_features", help="Base directory to save all generated feature artifacts.")
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%m_%d_%H_%M")
    output_dir = f"{args.output_dir_base}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    logging.info(f"Output for this run will be saved in: '{output_dir}'")

    articles = load_all_articles(args.input_dir)
    if not articles: return

    article_keywords = calculate_tfidf_fingerprints(articles)
    save_json(article_keywords, os.path.join(output_dir, "1_lexical_fingerprints.json"))

    citation_communities = build_citation_communities(articles)
    save_json(citation_communities, os.path.join(output_dir, "2_citation_communities.json"))

    article_entities = extract_entities_and_concepts(articles)
    save_json(article_entities, os.path.join(output_dir, "4_entities_and_concepts.json"))

    logging.info("Synthesizing all modalities to create final concept clusters...")
    final_clusters = []
    
    for i, community_urls in enumerate(citation_communities):
        if len(community_urls) < 5: continue

        all_keywords = [kw for url in community_urls for kw in article_keywords.get(url, [])]
        all_people = [p for url in community_urls for p in article_entities.get(url, {}).get('people', [])]
        all_concepts = [c for url in community_urls for c in article_entities.get(url, {}).get('concepts', [])]

        top_keywords = [kw for kw, count in Counter(all_keywords).most_common(15)]
        top_people = [p for p, count in Counter(all_people).most_common(10)]
        top_concepts = [c for c, count in Counter(all_concepts).most_common(15)]

        bridges = find_bridge_articles(set(community_urls), article_keywords, set(top_keywords))
        
        cluster_obj = {
            "cluster_id": f"citation_cluster_{i}",
            "top_keywords_tfidf": top_keywords,
            "top_concepts_ner": top_concepts,
            "key_people": top_people,
            "core_articles": community_urls,
            "bridge_articles": bridges
        }
        final_clusters.append(cluster_obj)

    save_json(final_clusters, os.path.join(output_dir, "5_synthesized_clusters_ner.json"))
    logging.info(f"Feature engineering complete. All artifacts saved in '{output_dir}'.")

if __name__ == '__main__':
    main()