# Perception
To be documented better (soon<sup>TM</sup>)

Using yolo and mss

Returns an array of detected objects (ImageObject)

Object's ID (Image ID) is its line in perception/darknet/obj.names
                          
# Modeling
To be documented better (soon<sup>TM</sup>)

There are two mostly separated models: PlayerModel and WorldModel.

### PlayerModel: 
Keeps track of player-related things: 

- Inventory
- Health/Hunger/Sanity
- Speed (just constant for now)

### WorldModel: 
Keeps track of objects and mobs in the world.

### Objects
Generally divided in pickable objects and fixed objects

Since some objects have multiple forms (e.g. sapling and harvested sapling), 
there is a separate set of IDs, called 'Object ID'

There is a factory to help with object creation

# Decision Making
To be documented better (soon<sup>TM</sup>)

# Control
To be documented better (soon<sup>TM</sup>)

# Action
To be documented better (soon<sup>TM</sup>)

# Utility
Clock: helps with clock/calendar-related things
GameTime: for conversion
Point2d: helps with 2d point operations

# Files for new objects
perception/darknet/obj.names (and retrain cnn)
modeling/Factory.py
modeling/items_info.csv
modeling/ObjectsInfo.py