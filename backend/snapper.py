import cv2
import os

# 📌 Get name input from shell
name = input("Enter name for folder: ")

# 📂 Define base directory
base_dir = "/Users/einsbern/Documents/CCTV/SnapShots"
save_path = os.path.join(base_dir, name)

# 🔧 Create directory if it doesn't exist
os.makedirs(save_path, exist_ok=True)

# 🎥 Use AVFoundation backend for Mac FaceTime camera
cam = cv2.VideoCapture(2, cv2.CAP_AVFOUNDATION)

# 🖼️ Set up window
cv2.namedWindow("press space to take a photo", cv2.WINDOW_NORMAL)
cv2.resizeWindow("press space to take a photo", 500, 300)

img_counter = 0

while True:
    ret, frame = cam.read()
    if not ret:
        print("Failed to grab frame")
        break
    cv2.imshow("press space to take a photo", frame)

    k = cv2.waitKey(1)
    if k % 256 == 27:
        # ESC pressed
        print("Escape hit, closing...")
        break
    elif k % 256 == 32:
        # SPACE pressed
        img_name = os.path.join(save_path, f"image_{img_counter}.jpg")
        cv2.imwrite(img_name, frame)
        print(f"{img_name} written!")
        img_counter += 1

# 🔚 Clean up
cam.release()
cv2.destroyAllWindows()
