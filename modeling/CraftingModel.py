class CraftingModel:
    def __init__(self) -> None:
        self.crafting_open = False
        self.current_crafting_tab = 0
        self.crafting_tabs_states = [0, 0, 0, 0, 0, 0]
        self.crafting_tree_1 = {
            0: ["Axe", "Pickaxe", "Shovel", "Hammer", "Pitchfork", "Razor", "FeatherPencil"],
            1: ["Campfire", "FirePit", "Torch"],
            2: ["Trap", "BirdTrap", "Compass", "Backpack", "HealingSalve", "StrawRoll", "PrettyParasol",
                "Umbrella", "Net", "FishingRod"],
            3: ["ScienceMachine", "AlchemyEngine", "ThermalMeasure", "Rainometer", "LightningRod"],
            4: ["Spear", "GrassSuit", "LogSuit", "SleepDart", "FireDart", "BlowDart", "BeeMine"],
            5: ["Garland", "RabbitEarmuffs", "StrawHat", "BeefaloHat", "TopHat"]
        }
        # inverse indexing for the crafting tree
        self.name_to_craft_position = {}
        for key, value in self.crafting_tree_1.items():
            for index, name in enumerate(value):
                self.name_to_craft_position[name] = (key, index)

        self.next_craft = None
