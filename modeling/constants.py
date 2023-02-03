# distance for two objects to be considered the same one
DISTANCE_FOR_SAME_OBJECT = 2.5
# distance for two mods to be considered the same one
DISTANCE_FOR_SAME_MOB = 15
# if a mob is not seen for this time, it will be removed
TIME_FOR_MOB_REMOVAL = 5
# if an object is not detected for this many cycles, it will be removed 
CYCLES_FOR_OBJECT_REMOVAL = 5
# an object needs to be detected for this many cycles to be added to the world model
CYCLES_TO_ADMIT_OBJECT = 3
# speed in game coordinates per second
# (-24.98, 0, 151.01) to (-48.22, 0, 151.31) in 116/30 seconds -> 23.24/116*30 = 6.01
# probably 6 per second 
PLAYER_BASE_SPEED = 6
# distance from screen center to discard possible player positions
DISTANCE_FOR_VALID_PLAYER_POSITION = 300

# camera calibration
# intrinsic parameters
FOV = 35 # degrees
# q increases camera heading, e decreases it
# extrinsic parameters
CAMERA_DISTANCE = 30
CAMERA_PITCH = 42.857142 # (30 - 15)/ (50 - 15) * 60 + (50 - 30)/ (50 - 15) * 30, degrees
CAMERA_HEADING = 45

CHUNK_SIZE = 64