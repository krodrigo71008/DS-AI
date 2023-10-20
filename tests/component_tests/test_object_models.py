import pandas as pd
import numpy as np

from modeling.Modeling import Modeling
from modeling.objects.Ashes import Ashes
from modeling.objects.BerryBush import BerryBush, BERRYBUSH_READY, BERRYBUSH_HARVESTED
from modeling.objects.Evergreen import Evergreen, EVERGREEN_SMALL
from modeling.objects.Grass import Grass, GRASS_READY, GRASS_HARVESTED
from modeling.objects.Sapling import Sapling, SAPLING_READY, SAPLING_HARVESTED
from utility.Clock import ClockMock
from utility.Point2d import Point2d
from utility.GameTime import GameTime

def test_ashes():
    clock = ClockMock([0, 0, 19.9, 20])
    modeling = Modeling(clock=clock)
    ashes = Ashes(Point2d(0, 0), Point2d(0, 0), modeling.world_model.scheduler)
    modeling.world_model.add_object(ashes)
    assert len(modeling.world_model.object_lists["Ashes"]) == 1
    assert len(modeling.world_model.objects_by_chunks[(0, 0)]) == 1
    # here we simulate updating the model 19.9 seconds later without receiving any new info
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.object_lists["Ashes"]) == 1
    assert len(modeling.world_model.objects_by_chunks[(0, 0)]) == 1
    # here we simulate updating the model 20 seconds later without receiving any new info
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.object_lists["Ashes"]) == 0
    assert len(modeling.world_model.objects_by_chunks[(0, 0)]) == 0

def test_berry_bush():
    clock = ClockMock([0, 0, GameTime(non_winter_days=4.6874).seconds(), GameTime(non_winter_days=4.6875).seconds()])
    modeling = Modeling(clock=clock)
    berry_bush = BerryBush(Point2d(0, 0), Point2d(0, 0), BERRYBUSH_HARVESTED, modeling.world_model.scheduler)
    berry_bush_2 = BerryBush(Point2d(0, 0), Point2d(0, 0), BERRYBUSH_READY, modeling.world_model.scheduler)
    modeling.world_model.add_object(berry_bush)
    modeling.world_model.add_object(berry_bush_2)
    assert len(modeling.world_model.get_all_of(["BerryBush"])["BerryBush"]) == 2
    assert len(modeling.world_model.get_all_of(["BerryBush"], "only_not_harvested")["BerryBush"]) == 1
    # here we simulate updating the model 4.6874 days later without receiving any new info
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["BerryBush"])["BerryBush"]) == 2
    assert len(modeling.world_model.get_all_of(["BerryBush"], "only_not_harvested")["BerryBush"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["BerryBush"])["BerryBush"]) == 2
    assert len(modeling.world_model.get_all_of(["BerryBush"], "only_not_harvested")["BerryBush"]) == 2

def test_evergreen():
    clock = ClockMock([0, 0, 10*60-1, 10*60, (10+35)*60, (10+35+35)*60, (10+35+35+7.5)*60])
    modeling = Modeling(clock=clock)
    evergreen = Evergreen(Point2d(0, 0), Point2d(0, 0), EVERGREEN_SMALL, modeling.world_model.scheduler)
    modeling.world_model.add_object(evergreen)
    assert len(modeling.world_model.get_all_of(["Evergreen"])["Evergreen"]) == 1
    assert len(modeling.world_model.get_all_of(["Evergreen"], "evergreen_small")["Evergreen"]) == 1
    # here we simulate updating the model almost 10 minutes later without receiving any new info
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Evergreen"])["Evergreen"]) == 1
    assert len(modeling.world_model.get_all_of(["Evergreen"], "evergreen_small")["Evergreen"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Evergreen"])["Evergreen"]) == 1
    assert len(modeling.world_model.get_all_of(["Evergreen"], "evergreen_medium")["Evergreen"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Evergreen"])["Evergreen"]) == 1
    assert len(modeling.world_model.get_all_of(["Evergreen"], "evergreen_big")["Evergreen"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Evergreen"])["Evergreen"]) == 1
    assert len(modeling.world_model.get_all_of(["Evergreen"], "evergreen_dead")["Evergreen"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Evergreen"])["Evergreen"]) == 1
    assert len(modeling.world_model.get_all_of(["Evergreen"], "evergreen_small")["Evergreen"]) == 1

def test_grass():
    clock = ClockMock([0, 0, GameTime(non_winter_days=2.9).seconds(), GameTime(non_winter_days=3).seconds()])
    modeling = Modeling(clock=clock)
    grass = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_HARVESTED, modeling.world_model.scheduler)
    grass_2 = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_READY, modeling.world_model.scheduler)
    modeling.world_model.add_object(grass)
    modeling.world_model.add_object(grass_2)
    assert len(modeling.world_model.get_all_of(["Grass"])["Grass"]) == 2
    assert len(modeling.world_model.get_all_of(["Grass"], "only_not_harvested")["Grass"]) == 1
    # here we simulate updating the model 2.9 days later without receiving any new info
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Grass"])["Grass"]) == 2
    assert len(modeling.world_model.get_all_of(["Grass"], "only_not_harvested")["Grass"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Grass"])["Grass"]) == 2
    assert len(modeling.world_model.get_all_of(["Grass"], "only_not_harvested")["Grass"]) == 2

def test_sapling():
    clock = ClockMock([0, 0, GameTime(non_winter_days=3.9).seconds(), GameTime(non_winter_days=4).seconds()])
    modeling = Modeling(clock=clock)
    sapling = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_HARVESTED, modeling.world_model.scheduler)
    sapling_2 = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_READY, modeling.world_model.scheduler)
    modeling.world_model.add_object(sapling)
    modeling.world_model.add_object(sapling_2)
    assert len(modeling.world_model.get_all_of(["Sapling"])["Sapling"]) == 2
    assert len(modeling.world_model.get_all_of(["Sapling"], "only_not_harvested")["Sapling"]) == 1
    # here we simulate updating the model 3.9 days later without receiving any new info
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Sapling"])["Sapling"]) == 2
    assert len(modeling.world_model.get_all_of(["Sapling"], "only_not_harvested")["Sapling"]) == 1
    
    modeling.received_yolo_info = False
    modeling.received_segmentation_info = False
    modeling.update_model_using_info(None, None)
    assert len(modeling.world_model.get_all_of(["Sapling"])["Sapling"]) == 2
    assert len(modeling.world_model.get_all_of(["Sapling"], "only_not_harvested")["Sapling"]) == 2

def test_possible_states():
    objects_info = pd.read_csv("utility/objects_info.csv")
    clock = ClockMock([0, 0, GameTime(non_winter_days=4.6874).seconds(), GameTime(non_winter_days=4.6875).seconds()])
    modeling = Modeling(clock=clock)
    berry_bush = BerryBush(Point2d(0, 0), Point2d(0, 0), BERRYBUSH_HARVESTED, modeling.world_model.scheduler)
    possible_states = berry_bush.object_ids
    ground_truth = objects_info[objects_info["name"] == "BerryBush"]["image_id"].values
    assert np.all(possible_states == ground_truth)
    grass = Grass(Point2d(0, 0), Point2d(0, 0), GRASS_HARVESTED, modeling.world_model.scheduler)
    possible_states = grass.object_ids
    ground_truth = objects_info[objects_info["name"] == "Grass"]["image_id"].values
    assert np.all(possible_states == ground_truth)
    sapling = Sapling(Point2d(0, 0), Point2d(0, 0), SAPLING_HARVESTED, modeling.world_model.scheduler)
    possible_states = sapling.object_ids
    ground_truth = objects_info[objects_info["name"] == "Sapling"]["image_id"].values
    assert np.all(possible_states == ground_truth)
    evergreen = Evergreen(Point2d(0, 0), Point2d(0, 0), EVERGREEN_SMALL, modeling.world_model.scheduler)
    possible_states = evergreen.object_ids
    ground_truth = objects_info[objects_info["name"] == "Evergreen"]["image_id"].values
    assert np.all(possible_states == ground_truth)
