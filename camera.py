import cv2

# Load the deep learning model
modelFile = "res10_300x300_ssd_iter_140000_fp16.caffemodel"
configFile = "deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(configFile, modelFile)

# Open the webcam
cap = cv2.VideoCapture(0)

# Create window for display
cv2.namedWindow('Webcam', cv2.WINDOW_NORMAL)

while True:
    # Read frame from the webcam
    ret, frame = cap.read()

    # Check if the frame was read correctly
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Prepare the frame for the model
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))

    # Perform face detection
    net.setInput(blob)
    faces = net.forward()

    # Draw rectangle around the faces
    for i in range(faces.shape[2]):
        confidence = faces[0, 0, i, 2]
        if confidence > 0.5:
            box = faces[0, 0, i, 3:7] * np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])
            (x, y, w, h) = box.astype("int")
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

    # Resize the window
    cv2.resizeWindow('Webcam', 480, 360)

    # Display the resulting frame
    cv2.imshow('Webcam', frame)

    # Break the loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and destroy all windows
cap.release()
cv2.destroyAllWindows()
