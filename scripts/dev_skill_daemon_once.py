from javu_agi.learn.skill_daemon import SkillDaemon
d = SkillDaemon(interval_s=0)
d._seen = set()
d.run_forever()
