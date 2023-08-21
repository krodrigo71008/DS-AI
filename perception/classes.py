def get_class_names():
    # this converts yolo_id to yolo_name
    with open("perception/darknet/obj.names", "r") as f:
        class_names = [cname.strip() for cname in f.readlines()]
    return class_names
