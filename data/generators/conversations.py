import random
from datetime import datetime
from .base import BaseGenerator

class ConversationGenerator(BaseGenerator):
    QUERIES = [
        "Which outlets should I visit first today?",
        "Why is Sari-sari ni Aling Maria high priority?",
        "Give me a brief for outlet X",
        "How many outlets in my area are at risk?",
        "What happened with my dormant outlets last week?"
    ]
    RESPONSES = [
        "Here are the top 3 priority outlets to visit today: ...",
        "Sari-sari ni Aling Maria is high priority because of declining transaction volume over the last 14 days.",
        "Outlet X has 3 active products, last visited 20 days ago.",
        "You have 15 outlets currently flagged as at risk.",
        "Last week, 5 dormant outlets were re-engaged."
    ]

    def generate_conversations(self, dsps, count=500):
        conversations = []
        for _ in range(count):
            dsp = random.choice(dsps)
            idx = random.randint(0, len(self.QUERIES) - 1)
            conversations.append({
                "id": self.generate_uuid(),
                "dsp_id": dsp["id"],
                "query": self.QUERIES[idx],
                "response": self.RESPONSES[idx],
                "timestamp": datetime.now()
            })
        return conversations
