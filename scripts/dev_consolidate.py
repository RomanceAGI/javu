from javu_agi.memory.consolidation_scheduler import ConsolidationScheduler
if __name__ == "__main__":
    s = ConsolidationScheduler(interval_s=0)
    s.tick()
    print("consolidation: OK")
