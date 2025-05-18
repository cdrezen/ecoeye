from hardware.led import LED_YELLOW_OFF, LED_YELLOW_ON
import math, tf, image
import config.settings as cfg

### TODO: use design pattern
class Classifier:
    def __init__(self, session):
        #TODO: make sure to not use duplicated loggers
        self.detectionlog = session.detectionlog
        self.imagelog = session.imagelog
        self.model_res = cfg.MODEL_RES
        self.net_path = cfg.NET_PATH
        self.threshold_confidence = cfg.THRESHOLD_CONFIDENCE
        self.scale_mul = 0.5  # From original code's hardcoded values
        self.x_overlap = 0.5
        self.y_overlap = 0.5
        self._load_model()

    def _load_model(self):
        try:
            self.labels = [line.rstrip('\n') for line in open(cfg.LABELS_PATH)]
            print("Loaded model and labels")
            #get target label index
            self.target_indices = [i for i in range(len(self.labels)) if self.labels[i] not in cfg.NON_TARGET_LABELS]
            self.non_target_indices = [i for i in range(len(self.labels)) if self.labels[i] in cfg.NON_TARGET_LABELS]
            print("Selected target indices:",list(self.labels[i] for i in self.target_indices))
        except Exception as e:
            print(e)
            raise Exception('Failed to load "trained.tflite" or "labels.txt", make sure to add these files on the SD card (' + str(e) + ')')

    def classify(self, img, mode, roi_rect=None, use_indicators=True):
        """
        Classify an image using the specified mode.
        """
        if use_indicators: LED_YELLOW_ON()

        if mode == 'blobs':
            res = self.classify_blob(img)
        elif mode == 'image':
            res = self.classify_image(img, roi_rect)
        elif mode == 'objects':
            res = self.detect_objects(img)

        if use_indicators: LED_YELLOW_OFF()
        return res

    def _rescale_image(self, img):
        """Rescale image to model resolution"""
        img_resized = img.copy(
            x_size=self.model_res, 
            y_size=self.model_res,
            copy_to_fb=True,
            hint=image.BICUBIC
        )
        return img_resized
    
    def classify_blob(self, img):
        """Classify a single blob image"""
        img_resized = self._rescale_image(img)
        obj = tf.classify(self.net_path, img_resized)[0]
        output = obj.output()
        detected = len(output) > 0
        return detected, obj.output()

    def classify_image(self, img, roi_rect=None):
        """Classify using sliding window approach"""

        #only analyse when classification is feasible within reasonable time frame
        # ? 2 consts ? deferred analysis of images when scale is too small (not working yet)
        if (cfg.MIN_IMAGE_SCALE < cfg.THRESHOLD_IMAGE_SCALE_DEFER):
            return
            
        img = self._rescale_image(img)
        detected = False
        confidence = 0

        for obj in tf.classify(
            self.net_path,
            img,
            min_scale=cfg.MIN_IMAGE_SCALE,
            scale_mul=self.scale_mul,
            x_overlap=self.x_overlap,
            y_overlap=self.y_overlap
        ):
            output = obj.output()
            if self._check_threshold(output):
                detected = True
                print("Detected target! Logging detection...")

                self.detectionlog.append(
                    picture_id=self.imagelog.picture_count,
                    labels=self.labels,
                    confidences=output,
                    rect=roi_rect
                )
        return detected, confidence
    
    def _check_threshold(self, output):
        """Check if any non-target class exceeds confidence threshold"""
        for idx in range(len(output)):
            if idx in self.non_target_indices:
                continue
            if output[idx] >= self.threshold_confidence:
                return True
        return False

    def detect_objects(self, img, use_indicators=True):
        """Detect objects with thresholding"""

        if(cfg.USE_ROI): 
            print("Object detection skipped, as it is not compatible with using ROIs!")
            return False, 0

        threshold_value = math.ceil(self.threshold_confidence * 255)
        confidence = 0
        detected = False

        for class_id, detection_list in enumerate(tf.detect(
            self.net_path,
            img,
            thresholds=[(threshold_value, 255)]  # Original code's approach
        )):
            # Skip background class
            if (class_id == 0
            or (len(detection_list) == 0)): # no detections for this class?
                continue 

            detected = True
            print("Detected %s! Logging detection..." % self.labels[class_id])
            
            for detection in detection_list:
                if(confidence < detection[4]): 
                    confidence = detection[4]
                if use_indicators: 
                    img.draw_rectangle(detection.rect(), color=cfg.CLASS_COLORS[class_id-1], thickness=2)
                
                self.detectionlog.append(
                    picture_id=self.imagelog.picture_count,
                    labels=self.labels[class_id],
                    confidences=detection[4],
                    rect=detection.rect()
                )
                
        return detected, confidence