class EmbodimentInterface:
    def __init__(self, adapter=None):
        self.env = adapter  # External simulator/robot interface

    def sense(self):
        if self.env:
            return self.env.sense()
        return {
            "position": [0, 0],
            "object_nearby": True,
        }

    def act(self, action):
        if self.env:
            self.env.act(action)
        else:
            print(f"Embodied action (sim): {action}")
