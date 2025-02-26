import tkinter as tk
from tkinter import ttk
import cv2
from threading import Thread, Lock
import time
from PIL import Image, ImageTk
from ultralytics import YOLO
import random
import serial

class RockPaperScissorsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors Game")

        # Load background image (Game interface)
        try:
            self.background_image = Image.open(r"C:\\Users\\hasan\\Desktop\\ALPEREN\\2.1arkaplan.jpg")
            self.background_image = self.background_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(self.background_image)
        except FileNotFoundError:
            self.bg_image = None

        # Place the image on the canvas
        self.canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        if self.bg_image:
            self.canvas_bg = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        self.root.geometry("800x600")  # Fixed window size
        self.running = False
        self.current_mode = "Random"  # Default mode

        # Return to home button (Top right corner)
        self.home_button = tk.Button(root, text="Return to Home", command=self.return_to_home)
        self.home_button.place(x=500, y=10, width=120, height=40)

        # Reset game button (Next to Return to Home)
        self.reset_button = tk.Button(root, text="Reset Game", command=self.reset_game)
        self.reset_button.place(x=660, y=10, width=120, height=40)

        # Toggle mode button (Top left corner)
        self.mode_button = tk.Button(root, text=f"Mode: {self.current_mode}", command=self.toggle_mode)
        self.mode_button.place(x=10, y=10, width=120, height=40)

        # Result area: To display user and robot choices
        self.result_label = tk.Label(root, text="User: Waiting... | Robot: Waiting...", font=("Arial", 14))
        self.result_label.place(x=10, y=60)

        # Scoreboard
        self.score_label = tk.Label(root, text="User: 0 - Robot: 0", font=("Arial", 12))
        self.score_label.place(x=10, y=100)

        # Placeholder for video screen
        self.video_label = tk.Label(root, bg="gray")
        self.video_label.place(x=80, y=150, width=640, height=480)

        # Scores
        self.user_score = 0
        self.robot_score = 0

        # Track if score has been updated this turn
        self.processed_this_turn = False

        # YOLO Model and Camera Initialization
        try:
            self.yolo_model = YOLO(r'C:\\Users\\hasan\\Desktop\\ALPEREN\\best3.pt')
        except FileNotFoundError:
            self.result_label.config(text="Model file not found. Please check the path.")
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.result_label.config(text="Camera initialization failed.")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 144)
        self.serial_port = 'COM3'
        try:
            self.arduino = serial.Serial(self.serial_port, 9600, timeout=0.05)
        except serial.SerialException:
            self.result_label.config(text="Serial port initialization failed.")

        # Start the game in default mode
        self.video_thread = Thread(target=self.update_video_feed, daemon=True)
        self.video_thread.start()
        self.start_random_mode()

        # Countdown işlemi için kilit
        self.countdown_lock = Lock()

    def toggle_mode(self):
        """Toggle between modes."""
        self.running = False
        time.sleep(0.5)  # Allow threads to terminate cleanly
        if self.current_mode == "Random":
            self.current_mode = "Robot Kazansın"
            self.reset_game()  # Reset game state when changing mode
            self.start_robot_wins_mode()
        else:
            self.current_mode = "Random"
            self.reset_game()  # Reset game state when changing mode
            self.start_random_mode()
        self.mode_button.config(text=f"Mode: {self.current_mode}")

    def update_video_feed(self):
        """Continuously update the video feed on the interface."""
        while hasattr(self, 'cap') and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (640, 480))
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.config(image=imgtk)
            time.sleep(0.05)  # Optimized sleep time for smoother display

    def countdown_and_detect(self):
        """Robot counts down from 3 and detects user move at the end."""
        # Countdown işlemini kilitle
        with self.countdown_lock:
            # Reset processed flag for each turn
            self.processed_this_turn = False

            for i in range(3, 0, -1):
                self.send_to_robot("rock")		
                start_time = time.time()
                while time.time() - start_time < 1:  # 1 second per countdown number
                    if hasattr(self, 'cap') and self.cap.isOpened():
                        ret, frame = self.cap.read()
                        if ret:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            # Add countdown text to the center of the frame
                            h, w, _ = frame.shape
                            font_scale = 5
                            font_thickness = 5
                            text = str(i)
                            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)[0]
                            text_x = (w - text_size[0]) // 2
                            text_y = (h + text_size[1]) // 2
                            cv2.putText(
                                frame,
                                text,
                                (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                font_scale,
                                (0, 0, 255),  # Red color for countdown
                                font_thickness
                            )
                            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                            img = Image.fromarray(frame)
                            imgtk = ImageTk.PhotoImage(image=img)
                            self.video_label.imgtk = imgtk
                            self.video_label.config(image=imgtk)
                    self.root.update()

            # Detect user's move at the end of countdown
            user_move = self.process_user_move()

            if not self.processed_this_turn:
                if self.current_mode == "Random":
                    # Random robot move
                    robot_move = random.choice(["Rock", "Paper", "Scissors"])
                elif self.current_mode == "Robot Kazansın":
                    # Robot always wins
                    robot_move = self.determine_robot_move(user_move) if user_move else random.choice(["Rock", "Paper", "Scissors"])

                # Send robot's move
                self.send_to_robot(robot_move.lower())

                # Determine result
                result = self.calculate_result(user_move, robot_move)

                # Update scores
                if result == "User Wins":
                    self.user_score += 1
                elif result == "Robot Wins":
                    self.robot_score += 1

                self.update_scores()

                # Display result
                self.result_label.config(text=f"Robot: {robot_move}, User: {user_move or 'None'}\nResult: {result}")
                self.processed_this_turn = True

            time.sleep(2)

    def start_random_mode(self):
        """Initialize Random Mode."""
        self.running = True
        self.result_label.config(text="Starting Random Mode...")
        self.random_mode_thread = Thread(target=self.random_mode_loop, daemon=True)
        self.random_mode_thread.start()

    def random_mode_loop(self):
        """Loop for Random Mode with countdown and user detection."""
        while self.running:
            self.countdown_and_detect()

    def start_robot_wins_mode(self):
        """Initialize Robot Wins Mode."""
        self.running = True
        self.result_label.config(text="Starting Robot Wins Mode...")
        self.robot_wins_thread = Thread(target=self.robot_wins_loop, daemon=True)
        self.robot_wins_thread.start()

    def robot_wins_loop(self):
        """Loop for Robot Wins Mode with countdown and user detection."""
        while self.running:
            self.countdown_and_detect()

    def update_scores(self):
        """Update the scoreboard."""
        self.score_label.config(text=f"User: {self.user_score} - Robot: {self.robot_score}")

    def process_frame(self, frame):
        """Process a single frame with YOLO model."""
        results = self.yolo_model.predict(frame, conf=0.5, verbose=False)
        if results[0].boxes:
            for box in results[0].boxes:
                label = results[0].names[int(box.cls)]
                if label in ["Rock", "Paper", "Scissors"]:
                    return label
        return None

    def process_user_move(self):
        """Simulate detecting user move using YOLO."""
        user_move = None

        if hasattr(self, 'cap') and self.cap.isOpened():
            for _ in range(50):  # Try for a few frames
                success, frame = self.cap.read()
                if success:
                    user_move = self.process_frame(frame)
                    if user_move:
                        break

        if not user_move:
            self.result_label.config(text="User: Waiting... | Robot: Waiting...")  # Display waiting message

        return user_move

    def determine_robot_move(self, user_gesture):
        """Robot selects a move to win against user's gesture."""
        moves = {"Rock": "Paper", "Paper": "Scissors", "Scissors": "Rock"}
        return moves.get(user_gesture)

    def send_to_robot(self, command):
        """Send command to the robot via serial."""
        if command:
            self.arduino.write(f"{command}\n".encode('utf-8'))

    def calculate_result(self, user_move, robot_move):
        """Calculate the result of the game."""
        if user_move == robot_move:
            return "Draw"
        elif (user_move == "Rock" and robot_move == "Scissors") or \
             (user_move == "Paper" and robot_move == "Rock") or \
             (user_move == "Scissors" and robot_move == "Paper"):
            return "User Wins"
        else:
            return "Robot Wins"

    def reset_game(self):
        """Reset the game state."""
        self.running = False
        time.sleep(0.5)  # Allow threads to stop
        self.user_score = 0
        self.robot_score = 0
        self.update_scores()
        self.result_label.config(text="Game Reset")
        if self.current_mode == "Random":
            self.start_random_mode()
        elif self.current_mode == "Robot Kazansın":
            self.start_robot_wins_mode()

    def return_to_home(self):
        """Return to the main menu."""
        self.running = False  # Stop current mode
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()  # Release camera
        self.root.destroy()  # Close the current window
        root_main = tk.Tk()
        MainMenuApp(root_main)  # Start main menu interface
        root_main.mainloop()

class MainMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors")
        self.root.geometry("800x600")
        self.root.resizable(False, False)

        # Load background image (Main menu)
        try:
            self.background_image = Image.open(r"C:\\Users\\hasan\\Desktop\\ALPEREN\\Background.jpg")
            self.background_image = self.background_image.resize((800, 600), Image.Resampling.LANCZOS)
            self.bg_image = ImageTk.PhotoImage(self.background_image)
        except FileNotFoundError:
            self.bg_image = None

        # Place the image on the canvas
        self.canvas = tk.Canvas(self.root, width=800, height=600, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        if self.bg_image:
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

        # Load Play button image
        try:
            self.button_image = Image.open(r"C:\\Users\\hasan\\Desktop\\ALPEREN\\button.jpg")
            self.button_image = self.button_image.resize((257, 100), Image.Resampling.LANCZOS)
            self.button_photo = ImageTk.PhotoImage(self.button_image)
        except FileNotFoundError:
            self.button_photo = None

        # Play button with image
        if self.button_photo:
            self.play_button = tk.Button(self.root, image=self.button_photo, command=self.start_game, borderwidth=0)
        else:
            self.play_button = tk.Button(self.root, text="Play", command=self.start_game)
        self.canvas.create_window(396, 430, anchor="center", window=self.play_button)

        # Load Exit button image
        try:
            self.exit_button_image = Image.open(r"C:\\Users\\hasan\\Desktop\\ALPEREN\\exit.jpg")
            self.exit_button_image = self.exit_button_image.resize((257, 100), Image.Resampling.LANCZOS)
            self.exit_button_photo = ImageTk.PhotoImage(self.exit_button_image)
        except FileNotFoundError:
            self.exit_button_photo = None

        # Exit button with image
        if self.exit_button_photo:
            self.exit_button = tk.Button(self.root, image=self.exit_button_photo, command=self.exit_game, borderwidth=0)
        else:
            self.exit_button = tk.Button(self.root, text="Exit", command=self.exit_game)
        self.canvas.create_window(396, 530, anchor="center", window=self.exit_button)

    def start_game(self):
        """Start the game interface."""
        self.root.destroy()
        root_game = tk.Tk()
        RockPaperScissorsApp(root_game)
        root_game.mainloop()

    def exit_game(self):
        """Exit the application."""
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainMenuApp(root)
    root.mainloop()