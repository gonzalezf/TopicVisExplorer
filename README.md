# TopicVisExplorer: Supporting multi-corpora comparison through visual exploration of topic modeling
Note: This is work-in-progress. Currently, we are conducting  a  user study to evaluate if the proposed functionalities of TopicVisExplorer allow better interpretation of topics.

This project is being developed by Felipe González (Msc. Computer science student at Universidad Técnica Federico Santa María) and it is being guided by Dr. Evangelos Millos (Dalhousie Univerisity), Dr. FernandoPaulovich (Dalhousie University), Dr. Claudia López (Universidad Técnica Federico Santa María), and Dr. Marcelo Mendoza(Universidad Técnica Federico Santa María)

## Scenario 1: Interpreting a topic modeling output
You can interact with a **demo** of this first scenario [**here**](http://topicvisexplorer.tk/singlecorpus "here")

![TopicVisExplorer Scenario 1](https://github.com/gonzalezf/TopicVisExplorer/blob/master/img/scenario_1.png?raw=true)

Given the topic modeling result of one corpus, our visualization has three basic pieces. First, the central panel of our visualization presents a global view of the topics and aims to answer questions “How prevalent is each topic?”, and “How do topics relate to each other?

In this view, we plot the topics as circles in a two-dimensional space whose centers are determined by computing the distance between topics using a <ins> newly proposed topic similarity metric </ins>, and then by using multidimensional scaling to project the inter-topic distances onto two dimensions using principal coordinate analysis. We encode each topic's overall prevalence using the circles' areas.

Secondly, to help users answering question 1: “What is the meaning of each topic?”, the right panel of our visualization allows the user to visualize the text and contribution percentage of the most relevant documents associated with the currently selected topic on the central panel. Documents are sorted according to the contribution to the topic. 

Finally, to help users answer the question "What is the meaning of each topic?", the left panel of our visualization depicts a horizontal bar chart whose bars represent the most useful terms to interpret the currently selected topic on the central panel. A pair of overlaid bars represent both the corpus-wide frequency of a given term as well as the topic-specific frequency of the term. This kind of linked selection allows users to examine a large number of topic-term relationships in a compact manner. Following Sievert and Shirley's approach, the most useful terms to a given topic are ranked according to the relevance metric, that allows users to flexibly rank terms in order of usefulness for topic interpretation. A slider allows users to alter the rankings of terms to aid topic interpretation. By default, the slider value is set to 0.6, as is suggested in a prior user study. 

The left, central and right panels of our visualization are linked such that selecting a topic (on the central panel) reveals the most useful terms (on the left panel) and the most useful documents (on the right panel) for interpreting the selected topic automatically.

## Scenario 2: Comparing topics from two topic modeling output
You can interact with a **demo** of this second scenario [**here**](http://topicvisexplorer.tk/multicorpora "here")

![TopicVisExplorer Scenario 2](https://github.com/gonzalezf/TopicVisExplorer/blob/master/img/scenario_2.png?raw=true)

In this second scenario, TopicVisExplorer introduces a visual representation to compare two topic modeling outputs. Here, the central panel contains a Sankey diagram to provides an overview of the relationships between the topics from different corpora. Nodes in the graph represent the topics, and the paths between nodes represent the similarity between them. The topics are represented as boxes, and their height depends on the number of connections with other topics. Topics are coloured according to the topic modeling output. The paths are represented with arcs that have a width proportional to the topic similarity score calculated by our proposed topic similarity metric. The order of the nodes is according to their frequency.

Notice that after selecting topics from two different topic modeling outputs on the central panel, the left and right panels shows the most relevant keywords and the most relevant documents to each of them, respectively. Topic labelling, topic splitting and topic merging operations are allowed as well.



