class AgentCommunicator:
    def __init__(self):
        self.inbox = []

    def receive(self, message):
        self.inbox.append(message)

    def send(self, target_agent, message):
        target_agent.communicator.receive(message)

    def process_messages(self, identity):
        for msg in self.inbox:
            identity.experience.append({"message_from_other": msg})
        self.inbox.clear()
