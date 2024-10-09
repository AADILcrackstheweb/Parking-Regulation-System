import cv2
import numpy as np
import requests
import imutils
from functions import find_polygon_center, save_object, load_object, is_point_in_polygon, get_label_name
from ultralytics import YOLO

# Load a pretrained YOLOv8n model
model = YOLO("Models//yolov8mmAp48//weights//best.pt")

# List to store points
polygon_data = load_object()
points = []

def draw_polygon(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONUP:
        points.append((x, y))

# Set up the IP camera URL
ip_camera_url = "http://192.168.55.55:8080/shot.jpg"

cv2.namedWindow("image")
cv2.setMouseCallback("image", draw_polygon)

while True:
    try:
        # Fetch the image from the IP camera
        img_resp = requests.get(ip_camera_url)
        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)
        frame = imutils.resize(frame, width=1280, height=720)

        mask_1 = np.zeros_like(frame)
        mask_2 = np.zeros_like(frame)

        results = model(frame, device='cpu')[0]
        polygon_data_copy = polygon_data.copy()

        for detection in results.boxes.data.tolist():
            x1, y1, x2, y2, score, class_id = detection
            label_name = get_label_name(class_id)
            if label_name in ["bicycle", "car", "van", "truck", "tricycle", "awning-tricycle", "bus", "motor"]:
                car_polygon = [(int(x1), int(y1)), (int(x1), int(y2)), (int(x2), int(y2)), (int(x2), int(y1))]

                for i in polygon_data_copy:
                    poligon_center = find_polygon_center(i)
                    is_present = is_point_in_polygon(poligon_center, car_polygon)

                    if is_present:
                        cv2.fillPoly(mask_1, [np.array(i)], (0, 0, 255))
                        polygon_data_copy.remove(i)

        cv2.putText(frame, f'Total space : {len(polygon_data)}', (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (8, 210, 255), 2, cv2.LINE_4)

        cv2.putText(frame, f'Free space : {len(polygon_data_copy)}', (50, 100),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (8, 210, 90), 3, cv2.LINE_4)

        for i in polygon_data_copy:
            cv2.fillPoly(mask_2, [np.array(i)], (0, 255, 255))

        frame = cv2.addWeighted(mask_1, 0.2, frame, 1, 0)
        frame = cv2.addWeighted(mask_2, 0.2, frame, 1, 0)

        for x, y in points:
            cv2.circle(frame, (x, y), 3, (0, 0, 255), -1)

        cv2.imshow("image", frame)

        # Capture key events
        wail_key = cv2.waitKey(1)
        if wail_key == ord("s") or wail_key == ord("S"):
            if points:
                polygon_data.append(points)
                points = []
                save_object(polygon_data)
        elif wail_key == ord("r") or wail_key == ord("R"):
            try:
                polygon_data.pop()
                save_object(polygon_data)
            except:
                pass
        elif wail_key & 0xFF == ord("q") or wail_key & 0xFF == ord("Q"):
            break

    except Exception as e:
        print(f"Error fetching IP camera feed: {e}")
        break

cv2.destroyAllWindows()
