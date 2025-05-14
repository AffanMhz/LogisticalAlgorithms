# 🚀 Spacecraft Inventory Manager

An intelligent inventory and storage management system designed for spacecrafts and space missions. This application helps you manage containers and items, auto-place them efficiently based on space constraints, and prioritize critical resources — all through an intuitive interface and smart backend logic.

---

## 🧠 What It Does

- 📦 **Manages Containers**: Create and manage containers with defined 3D dimensions.
- 📋 **Manages Items**: Upload items with properties like dimensions, priority, expiry date, usage limits, and preferred zones.
- 🤖 **Auto-Placement Algorithm**: Automatically fits items into the best possible container, optimizing for space, accessibility, and long-term utility.
- 📊 **Interactive UI**: A React frontend to upload CSVs, view placement results, and explore containers and their contents.
- 🔁 **Smart Replacements**: Keeps track of item expiry and usage limits for dynamic updates.

---

## 💡 Key Features

- **CSV Uploads**: Upload a list of items and containers via clean CSV formats.
- **Custom Parameters**: Every item can have:
  - `ID`, `Name`
  - `Width`, `Depth`, `Height` (rotatable)
  - `Priority (0–100)`
  - `Expiry Date`, `Usage Limit`
  - `Preferred Zone` (optional)
- **Optimized Placement**:
  - High-priority items are more accessible.
  - Expiring items are placed where they’re easy to remove.
  - Minimal reshuffling of existing items.
- **Modular**:
  - Backend handles logic and validation.
  - Frontend stays responsive and user-friendly.

---

## 🛠️ Tech Stack

| Layer      | Tools Used                     |
|------------|--------------------------------|
| Frontend   | React, Tailwind CSS            |
| Backend    | Python (Flask / FastAPI), Pandas |
| File Input | CSV format                     |
| Optional   | Three.js or 2D grid visualization |

---

## 🧭 Dashboard Preview

![Container Interface](screenshots/Container_Management.jpeg)

![Item Management](screenshots/Items_Management.jpeg)

---

## 📁 Example CSV Format

### Items:
```csv
ID,Name,Width,Depth,Height,Priority,Expiry Date,Usage Limit,Preferred Zone
1,Tool Kit,10,10,5,90,2025-05-01,15,A
2,First Aid Box,15,12,10,95,2025-06-15,5,B
3,Water Can,8,8,20,70,2025-04-20,30,C
```



### Container:
```csv
Container ID,Width,Depth,Height
C1,50,50,50
C2,30,30,30
```

## ⚙️ Running the App

***Backend Setup:***
bash
Copy
Edit
cd backend
pip install -r requirements.txt
python app.py

##Frontend Setup:
cd frontend
npm install
npm start

Visit: http://localhost:3000 to use the UI

## 📈 Future Plans

- Real-time visualizations of container layouts

- Drag-and-drop manual override

- Sorting items based on mission phases

- REST API for integration with other spacecraft systems

## 👨‍🚀 Built By
This project was built as part of a space systems software design Hackathon to explore smarter resource management aboard spacecraft. It blends real-world logistics principles with zero-gravity-specific constraints.

## 📬 Contact
Have ideas, suggestions, or want to collaborate?

📧 danishaffan678@gmail.com
🔗 https://www.linkedin.com/in/affan-danish-08a144353/

📄 License
MIT License.

### Use it, improve it, share it.
