import topicvisexplorer

vis = topicvisexplorer.TopicVisExplorer("name")

vis.load_corpus_data("models_output/single_corpus_airlines_dataset.pkl", "single_demo")
vis.load_corpus_data("models_output/single_corpus_europe_dataset_topics_6.pkl", "singlecorpus")
vis.load_corpus_data("models_output/multi_corpora_data_airlines_dataset.pkl", "multi_demo", True)
vis.load_corpus_data("models_output/multi_corpora_data_airlines_dataset_baseline_metric.pkl", "multi_demo_baseline", True)
vis.load_corpus_data("models_output/multi_corpora_data_europe_northamerica_ca_lda_mallet_gensim.pkl", "multicorpora", True)
vis.load_corpus_data("models_output/multi_corpora_data_europe_northamerica_ca_lda_mallet_gensim_topic_similarity_baseline.pkl", "multicorpora_baseline", True)

vis.run()