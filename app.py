import topicvisexplorer
import json

vis = topicvisexplorer.TopicVisExplorer("topicvisexplorer")
vis.load_scenarios(json.load(open("scenarios.json")))

vis.run()