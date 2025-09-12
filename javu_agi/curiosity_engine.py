import random

class CuriosityEngine:
    def __init__(self):
        self.novelty_memory = set()

    def is_novel(self, experience):
        return experience not in self.novelty_memory

    def update(self, experience):
        self.novelty_memory.add(experience)

    def generate_curious_goal(self, memory_snapshot: list[str]) -> str:
        """
        Generate a novel exploratory question based on recent memory.

        Uses the LLM to propose a single-sentence question that has not been previously discussed.

        Parameters
        ----------
        memory_snapshot : list[str]
            A list of recent memory entries.

        Returns
        -------
        str
            A trimmed exploratory question.
        """
        from javu_agi.llm import call_llm
        # Compose context using the last 30 memory entries to provide relevant background
        context = "\n".join(memory_snapshot[-30:])
        prompt = (
            "Berdasarkan konteks berikut, buatkan satu pertanyaan eksploratif yang belum pernah dibahas:\n"
            "---\n"
            f"{context}\n"
            "---\n"
            "Format satu kalimat eksploratif."
        )
        return call_llm(prompt).strip()

