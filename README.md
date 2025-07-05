
# 📅 SmartSched — Automated Timetable Generator

![License](https://img.shields.io/badge/License-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.x-blue.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

SmartSched is an intelligent, conflict-free timetable generator for schools, colleges, or institutions.  
It automates timetable scheduling using **Graph Coloring** and **Backtracking algorithms**, minimizing human effort and errors.

---

## 🚀 Features

- ✅ Conflict-free timetable generation
- ✅ Graph Coloring and Backtracking algorithm implementation
- ✅ Simple Python codebase — easy to understand and extend
- ✅ HTML interface for easy input and output
- ✅ Lightweight and adaptable to any institution

---

## 📸 Screenshots

![Timetable Example](images/screenshot1.png)
![Timetable Example](images/screenshot2.png)
![Timetable Example](images/screenshot3.png)

---

## 🛠️ Tech Stack

- **Python 3.x**
- **HTML**
- **CSS**
- **Javascript**
- **SQLite** 

---

## 📂 Project Structure

```
SmartSched-Automated-Timetable-Generator/
│
├── Scheduling/
│   ├── backtracking.py
│   ├── graph_coloring.py
│
├── Database/
│   ├── smartsheet.db         # Your SQLite database file
│
├── static/
│   ├── index.html            # Main input page
│   ├── timetable.html        # Timetable output page
│
├── app.py                    # Main entry point (runs the app/server)
├── initdb.py                 # Script to initialize/setup the DB
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
│
├── images/                   # Screenshots for README
│   ├── screenshot1.png
│   ├── screenshot2.png
|   ├── screenshot3.png

````

---

## ⚙️ Setup & Run

1️⃣ **Clone this repo**
```bash
git clone https://github.com/deepalichauhan16/SmartSched-Automated-Timetable-Generator.git
cd SmartSched-Automated-Timetable-Generator
````

2️⃣ **Install dependencies**

```bash
pip install -r requirements.txt
```

3️⃣ **Create a virtual environment named 'venv'**

```bash
python -m venv venv
```

4️⃣ **Activate the virtual environment**

```bash
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

5️⃣ **Run the app**

Run the Python application:

```bash
python app.py
```
By default, it will start a local server on http://127.0.0.1:5000/

6️⃣ View the timetable

Open your browser and go to:
http://127.0.0.1:5000/
Use the web interface to input data and generate your timetable!

---

## ⚡ How it Works

* **Graph Coloring:** Ensures no overlapping classes/teachers/rooms.
* **Backtracking:** Finds feasible combinations for complex constraints.

The system guarantees a practical timetable that avoids scheduling conflicts.

---

## 📌 Future Scope

* Add user authentication (teachers, admins)
* Export as PDF/Excel
* Add more input validation and customization
* Build a full web dashboard (Flask, Django)

---

## 🤝 Contributing

Contributions are welcome! Please fork this repository and submit a pull request.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## ✨ Author

**Deepali Chauhan**

🔗 [LinkedIn](https://www.linkedin.com/in/deepali-chauhan-b7881230b?utm_source=share&utm_campaign=share_via&utm_content=profile&utm_medium=android_app)

📫 \[[Email](mailto:deepalic1612@gmail.com)]

---


