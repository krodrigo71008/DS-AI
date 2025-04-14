# inventory slot 0 (leftmost slot)
FIRST_INVENTORY_POSITION = (471, 1056)
# spacing between two consecutive inventory slots (there are some variations, but this works)
INVENTORY_SPACING = (48, 0)
# inventory slot for the hand (leftmost equip slot)
HAND_INVENTORY_POSITION = (1278, 1056)
# pick up duration is the time between clicking the object to be picked up and the end (time to walk to it + picking up animation + a bit more as safety)
PICK_UP_DURATION = 2.5
# pick up stop duration is the time before hovering, this makes the camera stop moving
PICK_UP_STOP_DURATION = 1
# pick up hover duration is the hover time
PICK_UP_HOVER_DURATION = .8
# run action duration (this is repeated)
RUN_DURATION = 0.1
# stop action duration (this is repeated)
STOP_DURATION = 0.1
# duration of 'explore for a bit' action (this is repeated)
EXPLORE_DURATION = 1
# duration of a single keypress duration when crafting
CRAFT_KEYPRESS_DURATION = 0.3
# keypress duration when walking
KEYPRESS_DURATION = 0.2
# duration of the eating animation
EAT_DURATION = 0.5
# duration of the equipping animation
EQUIP_DURATION = 0.1
# after pressing enter to craft, this is the time we should wait for the crafting animation to finish
FINISH_CRAFTING_DURATION = 1
# duration of any mouse click
MOUSE_CLICK_DURATION = 0.1
# distance to get close to an objective and then start hovering over it
PICK_UP_DISTANCE = 6
# distance in case we really want to get close to something
CLOSE_ENOUGH_DISTANCE = 1
# distance in case we want to get close to something for exploration
CLOSE_ENOUGH_DISTANCE_FOR_EXPLORATION = 2
# time for the collecting animation + buffer to get close enough
COLLECT_DURATION = 1.5
# if an object that we want to collect is closer than this, we decide to collect it
RESOURCE_GATHERING_DISTANCE = 15
# duration of the camera rotation action
CAMERA_ROTATION_DURATION = 2
