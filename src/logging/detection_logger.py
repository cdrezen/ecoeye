# filepath: /home/user/Bureau/stage/projet/src/logging/detection_logger.py
from logging.csv import Csv

class DetectionLogger(Csv):
    """
    A class to handle detection logging operations, extending the Csv class.
    Provides methods for logging blob detections and classification results.
    """

    def __init__(self, path: str, detection_count: int = 0):
        """
        Initialize the DetectionLogger with a path and required headers.
        
        :param path: The path to the CSV file.
        """
        super().__init__(path, "detection_id", "picture_id", 
                        "blob_pixels", "blob_elongation", 
                        "blob_corner1_x", "blob_corner1_y", "blob_corner2_x", "blob_corner2_y", 
                        "blob_corner3_x", "blob_corner3_y", "blob_corner4_x", "blob_corner4_y", 
                        "blob_l_mode", "blob_l_min", "blob_l_max", 
                        "blob_a_mode", "blob_a_min", "blob_a_max", 
                        "blob_b_mode", "blob_b_min", "blob_b_max", 
                        "image_labels", "image_confidences", 
                        "image_x", "image_y", "image_width", "image_height")
        
        self.detection_count = detection_count
        
    
    def append(self, picture_id=None, blob=None, color_statistics=None,
                labels=None, confidences=None,
                rect=None,
                prepend_comma=False, end_line=True):
        """
        Append detection data to the log.
        """
        self.detection_count += 1
        data = [self.detection_count]

        if not picture_id is None:
            data.append(picture_id)
        elif not prepend_comma:
            raise ValueError("Missing parameters.")

        if blob and color_statistics:
            blob_data = self.get_blob_log_data(blob, color_statistics) 
        elif not prepend_comma:
            blob_data = ["NA"] * 19

        if blob_data:
            data += blob_data

        if labels and confidences:
            if not rect:
                raise ValueError("Missing parameter rect.")
            labels_str = ";".join(map(str, labels))
            confidences_str = ";".join(map(str, confidences))
            data += [labels_str, confidences_str, rect.x(), rect.y(), rect.w(), rect.h()]
        
        super().append(*data, prepend_comma=prepend_comma, end_line=end_line)


    def get_blob_log_data(self, blob, color_statistics):
        return [blob.pixels(), blob.elongation(),
            blob.corners()[0][0], blob.corners()[0][1], 
            blob.corners()[1][0], blob.corners()[1][1],
            blob.corners()[2][0], blob.corners()[2][1], 
            blob.corners()[3][0], blob.corners()[3][1],
            color_statistics.l_mode(), color_statistics.l_min(), color_statistics.l_max(),
            color_statistics.a_mode(), color_statistics.a_min(), color_statistics.a_max(),
            color_statistics.b_mode(), color_statistics.b_min(), color_statistics.b_max()]