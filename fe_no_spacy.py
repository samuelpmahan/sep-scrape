# feature_engineer.py (v3 - Final)

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

    # --- UPDATED: Custom Stop Words ---
    # Augment the standard English stop words list with domain-specific particles
    # like "al" (Arabic 'the') and "ibn" (Arabic 'son of') to prevent them from
    # being treated as significant keywords.
    custom_stop_words = list(ENGLISH_STOP_WORDS) + ["al", "ibn"]

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),
        stop_words=custom_stop_words,
        max_df=0.8,
        min_df=5
    )
    
    tfidf_matrix = vectorizer.fit_transform(corpus)
    feature_names = np.array(vectorizer.get_feature_names_out())
    
    article_keywords = {}
    for i, url in enumerate(urls):
        row = tfidf_matrix.getrow(i).toarray().ravel()
        top_indices = row.argsort()[-top_n:]
        top_keywords = feature_names[top_indices].tolist()
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
        source_url = article['url']
        for dest_url in article.get('related_entries', []):
            if dest_url in G:
                G.add_edge(source_url, dest_url)

    partition = community_louvain.best_partition(G.to_undirected())
    
    communities = {}
    for node, community_id in partition.items():
        communities.setdefault(community_id, []).append(node)
        
    logging.info(f"Detected {len(communities)} citation-based communities.")
    return list(communities.values())

def find_bridge_articles(community_urls: set, all_article_keywords: dict, core_concepts: set, similarity_threshold: float = 0.1) -> list:
    """Finds articles that are not in the community but are thematically similar."""
    bridge_articles = []
    for url, keywords in all_article_keywords.items():
        if url not in community_urls:
            article_keyword_set = set(keywords)
            intersection = article_keyword_set.intersection(core_concepts)
            
            # Prevent division by zero for articles with no keywords
            if not article_keyword_set:
                continue

            if len(intersection) / len(article_keyword_set) >= similarity_threshold:
                bridge_articles.append(url)
                
    return bridge_articles

def main():
    """Main function to run the feature engineering pipeline and save all artifacts."""
    parser = argparse.ArgumentParser(description="Concept Discovery Engine for the SEP corpus (v3 - Persistent).")
    parser.add_argument("--input-dir", default="processed_articles", help="Directory containing the processed JSON files.")
    parser.add_argument("--output-dir", default="engineered_features", help="Directory to save all generated feature artifacts.")
    args = parser.parse_args()

    # Create the main output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Load Data ---
    articles = load_all_articles(args.input_dir)
    if not articles:
        return

    # --- Modality 1: Lexical Fingerprints ---
    article_keywords = calculate_tfidf_fingerprints(articles)
    save_json(article_keywords, os.path.join(args.output_dir, "1_lexical_fingerprints.json"))

    # --- Modality 2: Citation Communities ---
    citation_communities = build_citation_communities(articles)
    save_json(citation_communities, os.path.join(args.output_dir, "2_citation_communities.json"))

    # --- Synthesis Phase ---
    logging.info("Synthesizing modalities to create final concept clusters...")
    final_clusters = []
    
    for i, community_urls in enumerate(citation_communities):
        if len(community_urls) < 5:
            continue

        community_keyword_counts = Counter(kw for url in community_urls for kw in article_keywords.get(url, []))
        core_concepts = [kw for kw, count in community_keyword_counts.most_common(15)]
        core_concepts_set = set(core_concepts)

        bridges = find_bridge_articles(set(community_urls), article_keywords, core_concepts_set)
        
        cluster_obj = {
            "cluster_id": f"citation_cluster_{i}",
            "core_concepts": core_concepts,
            "core_articles": community_urls,
            "bridge_articles": bridges
        }
        final_clusters.append(cluster_obj)

    # --- Save Final Synthesized Output ---
    save_json(final_clusters, os.path.join(args.output_dir, "3_synthesized_clusters.json"))
        
    logging.info(f"Feature engineering complete. All artifacts saved in '{args.output_dir}'.")

if __name__ == '__main__':
    main()
