from modeling.Factory import factory
from modeling.Modeling import Modeling
from utility.Point2d import Point2d

def test_create_object():
    modeling = Modeling()
    for image_id in range(1, 186+1):
        factory.create_object(image_id, Point2d(0, 0), Point2d(0, 0), modeling.world_model.scheduler)