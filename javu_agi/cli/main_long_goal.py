from javu_agi.long_horizon_goal_agent import execute_long_horizon_goal
from javu_agi.utils.logger import log
import sys

if __name__ == "__main__":
    if len(sys.argv) < 2:
        log("⚠️  Please provide a long-term goal as a command-line argument.")
        sys.exit(1)

    try:
        user_id = "default_user"
        long_goal = sys.argv[1]
        log(f"🚀 Executing long-horizon goal: {long_goal}")
        execute_long_horizon_goal(user_id, long_goal)
    except Exception as e:
        log(f"❌ Error executing long-horizon goal: {e}")
