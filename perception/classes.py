def get_class_names():
    with open("darknet/obj.names", "r") as f:
        class_names = [cname.strip() for cname in f.readlines()]
    return class_names
