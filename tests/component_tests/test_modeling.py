import numpy as np

from modeling.PlayerModel import PlayerModel
from modeling.WorldModel import WorldModel
from modeling.constants import CAMERA_PITCH, CAMERA_DISTANCE, FOV
from utility.Clock import Clock
from utility.Point2d import Point2d

def test_transformation():
    """This tests the transformation function by using some images as reference. The basic idea was:
    - Record a video walking around two bushes on known world coordinates
    - Extract some frames from the video
    - Annotate manually in which pixels the bushes and player are
    - Transform those annotations to see if they match our known positions
    """
    clock = Clock()
    player = PlayerModel(clock)
    world = WorldModel(player, clock)
    positions = [Point2d(0,-8.6), Point2d(0,-13.8), Point2d(6.4,-6.5), Point2d(16.0,-6.5), Point2d(-8.9,-6.5)]
    bush_positions = [
        [Point2d(558, 600), Point2d(1854, 600)],
        [Point2d(107, 600), Point2d(1394, 600)],
        [Point2d(630, 428), Point2d(1783, 428)],
        [Point2d(687, 175), Point2d(1645, 175)],
        [Point2d(512, 950)]
    ]
    player_positions = [
        Point2d(1043, 600),
        Point2d(868, 600),
        Point2d(960, 671),
        Point2d(960, 671),
        Point2d(960, 550)
    ]
    answers = [
        [Point2d(0, 0), Point2d(0, -23.2)],
        [Point2d(0, 0), Point2d(0, -23.2)],
        [Point2d(0, 0), Point2d(0, -23.2)],
        [Point2d(0, 0), Point2d(0, -23.2)],
        [Point2d(0, 0)]
    ]
    results = []
    for i in range(5):
        player.position = positions[i]
        local_pos = bush_positions[i]
        answer = answers[i]
        player_pos = player_positions[i]
        world.player_detected(player_pos)
        world.update_origin_position()
        for lp, ans in zip(local_pos, answer):
            res = world.local_to_global_position(
                lp,
                0,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 1.5
        # this isn't really necessary, but I'll leave it here just to illustrate how the world model should be used
        world.finish_cycle()
    print(f"avg distance: {np.array(results).mean()}")
    results = []
    for i in range(11):
        # this simulates not detecting the player for many cycles
        world.finish_cycle()
    for i in range(5):
        player.position = positions[i]
        local_pos = bush_positions[i]
        answer = answers[i]
        player_pos = player_positions[i]
        world.update_origin_position()
        for lp, ans in zip(local_pos, answer):
            res = world.local_to_global_position(
                lp,
                0,
                CAMERA_PITCH,
                CAMERA_DISTANCE,
                FOV
            )
            results.append(res.distance(ans))
            assert res.distance(ans) < 12
    print(f"avg distance: {np.array(results).mean()}")
        


# start 32
# im1 = 119 -> 8.6 from left
# start back 294
# im2 = 388 -> 9.4 from right (13.8 from left)
# stop 461 -> 16.7 from right (6.5 from left)
# start down 461
# im3 525 -> 6.4 down
# im4 621 -> 16.0 down
# stop 621
# start up 623
# im5 872 -> 24.9 up from down -> 8.9 up
# 
# heading = 0 -> down +x  left +z
# bush1 -> 0,0
# bush2 -> 0,-23.2
# start -> 0,0
# im1 -> 0,-8.6
# im2 -> 0,-13.8
# im3 -> 6.4,-6.5
# im4 -> 16.0,-6.5
# im5 -> -8.9,-6.5
# bush_positions:
# im1 -> (558, 600), (1854, 600)
# im2 -> (107, 600), (1394, 600)
# im3 -> (630, 428), (1783, 428)
# im4 -> (687, 175), (1645, 175)
# im5 -> (512, 950)
# player_position:
# im1 -> (1043, 600)
# im2 -> (868, 600)
# im3 -> (960, 671)
# im4 -> (960, 671)
# im5 -> (960, 550)
