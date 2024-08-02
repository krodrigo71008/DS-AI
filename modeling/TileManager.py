import numpy as np
from scipy.stats import mode

class TileManager:
    def __init__(self):
        # tiles is a XxYxN array, with N being number of detections recorded (e.g. N=10 means that 
        # we record the latest 10 detections of that tile)
        self.tiles : np.ndarray = None
        self._x1_shift : int = 0
        self._x2_shift : int = 0
        self._MAX_QUEUE_SIZE : int = 5

    def _map_index_to_actual_index(self, xy : tuple[int, int]) -> tuple[int, int]:
        x, y = xy
        return (x - self._x1_shift, y - self._x2_shift)

    def get_tiles(self, p1 : tuple[int, int], p2 : tuple[int, int]) -> np.ndarray:
        """Get tiles ids from a certain area

        :param p1: leftupper corner
        :type p1: tuple[int, int]
        :param p2: rightlower corner
        :type p2: tuple[int, int]
        :return: array with tile ids
        :rtype: np.ndarray
        """
        assert p1[0] <= p2[0]
        assert p1[1] <= p2[1]
        if self.tiles is None:
            return None
        p11, p12 = p1
        p21, p22 = p2
        conv_p11, conv_p12 = self._map_index_to_actual_index((p11, p12))
        if conv_p11 < 0 or conv_p11 >= self.tiles.shape[0] or conv_p12 < 0 or conv_p12 >= self.tiles.shape[1]:
            return None
        conv_p21, conv_p22 = self._map_index_to_actual_index((p21, p22))
        if conv_p21 < 0 or conv_p21 >= self.tiles.shape[0] or conv_p22 < 0 or conv_p22 >= self.tiles.shape[1]:
            return None
        
        # [0] gets values, [1] gets counts
        results = mode(self.tiles[conv_p11:conv_p21+1, conv_p12:conv_p22+1, :], axis=2, keepdims=False)[0]
        return results

    def get_tile(self, p : tuple[int, int]) -> np.ndarray:
        """Get tile id for one tile

        :param p: chunk index
        :type p: tuple[int, int]
        :return: array with tile id
        :rtype: np.ndarray
        """
        if self.tiles is None:
            return None
        p1, p2 = p
        conv_p1, conv_p2 = self._map_index_to_actual_index((p1, p2))
        if conv_p1 < 0 or conv_p1 >= self.tiles.shape[0] or conv_p2 < 0 or conv_p2 >= self.tiles.shape[1]:
            return None
        
        results = mode(self.tiles[conv_p1, conv_p2, :], keepdims=False)[0]
        return results
    
    def add_detections(self, x_lines : list[int], y_lines : list[int], warped_image : np.ndarray, coords : tuple[int, int]) -> None:
        new_info_size = (len(y_lines)-1, len(x_lines)-1)
        if self.tiles is None:
            self._x1_shift = coords[0]
            self._x2_shift = coords[1]
            self.tiles = np.zeros((new_info_size[0], new_info_size[1], self._MAX_QUEUE_SIZE))

        c1 = coords[0]
        c2 = coords[1]
        c3 = coords[0]+new_info_size[0]
        c4 = coords[1]+new_info_size[1]
        diff1 = max(0, self._x1_shift - c1)
        diff2 = max(0, self._x2_shift - c2)
        diff3 = max(0, c3 - self._x1_shift - self.tiles.shape[0])
        diff4 = max(0, c4 - self._x2_shift - self.tiles.shape[1])
        # update x1_shift and x1_shift
        self._x1_shift -= diff1
        self._x2_shift -= diff2

        # expand tile grid if needed
        self.tiles = np.vstack((
            np.hstack((np.zeros((diff1, diff2, self._MAX_QUEUE_SIZE)), 
                      np.zeros((diff1, self.tiles.shape[1], self._MAX_QUEUE_SIZE)), 
                      np.zeros((diff1, diff4, self._MAX_QUEUE_SIZE)))),

            np.hstack((np.zeros((self.tiles.shape[0], diff2, self._MAX_QUEUE_SIZE)), 
                      self.tiles, 
                      np.zeros((self.tiles.shape[0], diff4, self._MAX_QUEUE_SIZE)))),

            np.hstack((np.zeros((diff3, diff2, self._MAX_QUEUE_SIZE)), 
                      np.zeros((diff3, self.tiles.shape[1], self._MAX_QUEUE_SIZE)), 
                      np.zeros((diff3, diff4, self._MAX_QUEUE_SIZE)))),
        ))

        for i in range(len(x_lines)-1):
            x1 = x_lines[i]
            x2 = x_lines[i+1]
            for j in range(len(y_lines)-1):
                y1 = y_lines[j]
                y2 = y_lines[j+1]
                # again, opencv x = x2, opencv y = x1
                cur_chunk = warped_image[x1:x2, y1:y2]
                values, counts = np.unique(cur_chunk, return_counts=True)
                tile_id = values[np.argmax(counts)]
                if tile_id != 0:
                    conv_j, conv_i = self._map_index_to_actual_index((coords[0]+j, coords[1]+i))
                    self.tiles[conv_j, conv_i, 1:] = self.tiles[conv_j, conv_i, :-1]
                    self.tiles[conv_j, conv_i, 0] = tile_id
