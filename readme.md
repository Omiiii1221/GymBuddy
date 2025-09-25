
# Gym Buddy – Exercise Counter

A real-time gym exercise counter powered by Teachable Machine and Flask. This project uses pose detection to track body movements and count repetitions (e.g., squats, push-ups, sit-ups, bicep curls).

---

## Features

* Real-time video streaming from webcam
* Pose classification using Teachable Machine exported model
* Automatic rep counting (e.g., counts "up" and "down" movements)
* Flask backend + HTML/JS frontend for live monitoring
* Exercise stats display on the web interface

---

## Tech Stack

* Python (Flask, OpenCV, TensorFlow/keras)
* Teachable Machine (Pose classification model)
* HTML, JavaScript, CSS (Frontend UI)

---

## Project Structure

```
GymBuddy/
│── static/
│   └── my-pose-model/ # Exported Teachable Machine model (model.json, weights.bin)
│── app.py             # Flask backend
│── README.md          # Project documentation
```

---

## Installation & Setup

1. Clone the repository

   ```bash
   git clone https://github.com/omiiii1221/GymBuddy.git
   cd GymBuddy
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Export Teachable Machine model

   * Go to [Teachable Machine](https://teachablemachine.withgoogle.com/)
   * Train a Pose Classification model (e.g., Up/Down movements)
   * Export → TensorFlow → Keras format → place files inside `static/my-pose-model/`

4. Run Flask app

   ```bash
   python app.py
   ```

5. Open in browser

   ```
   http://127.0.0.1:5000
   ```

---

## How It Works

1. Open the app in your browser
2. Allow webcam access
3. Perform the exercise (e.g., squats)
4. The app will detect pose → classify movement → count reps in real time

---

## To-Do / Improvements

* Add multiple exercise support (push-ups, jumping jacks, etc.)
* Save progress to CSV/Database
* Add voice feedback (e.g., "Good Job! Rep 10!")
* Deploy on Heroku/Render for online access

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you’d like to change.

---

## License

MIT License © 2025

---