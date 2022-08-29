DISTANCE_FOR_SAME_OBJECT = 10
DISTANCE_FOR_SAME_MOB = 30
TIME_FOR_MOB_REMOVAL = 5
# speed in game coordinates per second
# (-24.98, 0, 151.01) to (-48.22, 0, 151.31) in 116/30 seconds -> 23.24/116*30 = 6.01
# probably 6 per second 
PLAYER_BASE_SPEED = 6

# camera calibration
# intrinsic parameters
FOV = 35 # degrees
# q increases camera heading, e decreases it
# extrinsic parameters
CAMERA_DISTANCE = 30
CAMERA_PITCH = 42.857142 # (30 - 15)/ (50 - 15) * 60 + (50 - 30)/ (50 - 15) * 30, degrees
CAMERA_HEADING = 45