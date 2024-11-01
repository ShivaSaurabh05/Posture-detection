from flask import Flask, render_template, Response, jsonify
import cv2
import math as m
import mediapipe as mp
import threading
import winsound

app = Flask(__name__)

# Global variables for posture timing and state
good_posture_time = 0
bad_posture_time = 0
current_posture = 'Good Posture'
running = True

# Calculate angle for forward/backward inclination
def findAngle(x1, y1, x2, y2):
    if y1 == 0:  # Prevent division by zero
        return 0
    try:
        theta = m.acos((y2 - y1) * (-y1) / (m.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2) * y1))
        return theta * (180 / m.pi)
    except ValueError:
        return 0

# Calculate angle for side inclination
def findSideInclination(left_shoulder, right_shoulder, head_center):
    shoulder_midpoint_x = (left_shoulder[0] + right_shoulder[0]) / 2
    shoulder_midpoint_y = (left_shoulder[1] + right_shoulder[1]) / 2
    dx = head_center[0] - shoulder_midpoint_x
    dy = head_center[1] - shoulder_midpoint_y
    angle = m.atan2(dy, dx) * (180 / m.pi)
    return angle

def sendWarning():
    print("Warning: Bad posture detected!")
    winsound.Beep(1000, 1000)

# Video streaming generator function
def generate_frames():
    global good_posture_time, bad_posture_time, current_posture

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    # Input source (IP camera URL or webcam)
    video_path = 'rtsp://admin:admin@192.168.137.250:554/unicaststream/3'
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Unable to open camera")
        return

    while running:
        success, image = cap.read()
        if not success:
            break
        
        h, w = image.shape[:2]
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        keypoints = pose.process(image_rgb)

        if keypoints.pose_landmarks:
            lm = keypoints.pose_landmarks.landmark
            l_shldr = (int(lm[mp_pose.PoseLandmark.LEFT_SHOULDER].x * w), int(lm[mp_pose.PoseLandmark.LEFT_SHOULDER].y * h))
            r_shldr = (int(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * w), int(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * h))
            l_ear = (int(lm[mp_pose.PoseLandmark.LEFT_EAR].x * w), int(lm[mp_pose.PoseLandmark.LEFT_EAR].y * h))
            r_ear = (int(lm[mp_pose.PoseLandmark.RIGHT_EAR].x * w), int(lm[mp_pose.PoseLandmark.RIGHT_EAR].y * h))
            l_hip = (int(lm[mp_pose.PoseLandmark.LEFT_HIP].x * w), int(lm[mp_pose.PoseLandmark.LEFT_HIP].y * h))

            head_center = ((l_ear[0] + r_ear[0]) // 2, (l_ear[1] + r_ear[1]) // 2)

            neck_inclination = findAngle(l_shldr[0], l_shldr[1], l_ear[0], l_ear[1])
            torso_inclination = findAngle(l_hip[0], l_hip[1], l_shldr[0], l_shldr[1])
            side_inclination = findSideInclination(l_shldr, r_shldr, head_center)

            if neck_inclination < 40 and torso_inclination < 10 and -110 < side_inclination < -80:
                current_posture = 'Good Posture'
                good_posture_time += 1
            else:
                current_posture = 'Bad Posture'
                bad_posture_time += 1

            if current_posture == 'Bad Posture':
                sendWarning()

            # Draw the current posture status on the frame
            cv2.putText(image, f'Posture: {current_posture}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if current_posture == 'Good Posture' else (0, 0, 255), 2)

        # Encode the frame in JPEG format
        _, buffer = cv2.imencode('.jpg', image)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

# New route for video streaming
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# New route for current posture status
@app.route('/posture_status')
def posture_status():
    return jsonify({
        'posture': current_posture,
        'good_posture_time': good_posture_time,
        'bad_posture_time': bad_posture_time
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    capture_thread = threading.Thread(target=generate_frames)
    capture_thread.start()
    app.run(debug=True, use_reloader=False)
    running = False
    capture_thread.join()
