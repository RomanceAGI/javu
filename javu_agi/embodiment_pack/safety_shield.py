def safety_veto(traj, limits, geofence):
    if violates_geofence(traj, geofence):
        return False, "geofence"
    if exceeds_force_speed(traj, limits):
        return False, "force_speed"
    if time_to_collision(traj) < limits.get("ttc_min", 0.5):
        return False, "ttc"
    return True, "ok"
