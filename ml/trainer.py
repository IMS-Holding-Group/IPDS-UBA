from ml.behavior_analyzer import BehaviorAnalyzer


def train_behavior_model(analyzer=None):
    obj = analyzer or BehaviorAnalyzer()
    return obj.train_with_simulated_data()
