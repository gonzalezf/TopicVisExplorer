import topicvisexplorer
import json
vis = topicvisexplorer.TopicVisExplorer("topicvisexplorer")
vis.load_scenarios(json.load(open("scenarios.json")))
app = vis.app

if __name__ == '__main__':
        vis.run()