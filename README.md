# 🚀 LogisticalAlgorithms - Spacecraft Inventory Manager

## Overview

LogisticalAlgorithms is an advanced, intelligent inventory and storage management system designed specifically for spacecraft and space missions. This sophisticated application offers efficient management of containers and items, optimizing their placement for better space utilization, accessibility, and longevity. Leveraging a highly efficient auto-placement algorithm and continuously improving spatial optimization techniques, this system ensures that critical resources are prioritized, maintained, and easily accessible.

---

## 🧠 Key Functionalities

* **Dynamic Container Management**: Define, create, and manage containers with specific 3D dimensions.
* **Comprehensive Item Management**:

  * Upload items with detailed properties, including:

    * `ID`, `Name`
    * `Width`, `Depth`, `Height` (rotatable for better fit)
    * `Priority (0–100)`
    * `Expiry Date`, `Usage Limit`
    * `Preferred Zone` (optional for specific storage zones)
* **Adaptive Auto-Placement Algorithm**:

  * Automatically calculates the best-fit position for each item.
  * Prioritizes high-value items for easy access.
  * Optimizes space usage, minimizing gaps and unused areas.
  * Manages item expiry and usage limits, dynamically replacing expired or depleted items.

---

## 🚀 Advanced Algorithms and Optimization

* **Real-Time 3D Spatial Optimization**:

  * Uses continuously improving 3D spatial algorithms to efficiently arrange items in containers.
  * Integrates Fast Fourier Transform (FFT) for complex placement analysis.
* **Dynamic Placement Adjustment**:

  * Adjusts item placements based on changes in priority, expiry, or other parameters.
  * Minimizes reshuffling of existing items while maintaining efficient space utilization.
* **Enhanced Item Prioritization**:

  * Critical items are placed for easy access.
  * Expiring items are positioned for quick replacement.
* **Rotational Adaptation**:

  * Items can be rotated to maximize space utilization.

---

## 💡 Key Features

* **CSV-Based Bulk Upload**:

  * Supports uploading lists of items and containers in clean, structured CSV formats.
* **Customizable Item Properties**:

  * Every item can have unique parameters:

    * `ID`, `Name`
    * `Width`, `Depth`, `Height`
    * `Priority (0–100)`
    * `Expiry Date`, `Usage Limit`
    * `Preferred Zone` (optional)
* **Interactive User Interface**:

  * Intuitive React frontend for visualizing containers, managing items, and exploring placement results.
  * Real-time placement visualization and updates.

---

## ⚙️ Technical Architecture

| Layer         | Tools Used                       |
| ------------- | -------------------------------- |
| Frontend      | React, Tailwind CSS              |
| Backend       | Python (FastAPI / Flask), Pandas |
| File Input    | CSV format                       |
| Visualization | Three.js (3D), 2D Grid UI        |

---

## 📁 Example CSV Formats

### Items:

```csv
ID,Name,Width,Depth,Height,Priority,Expiry Date,Usage Limit,Preferred Zone
1,Tool Kit,10,10,5,90,2025-05-01,15,A
2,First Aid Box,15,12,10,95,2025-06-15,5,B
3,Water Can,8,8,20,70,2025-04-20,30,C
```

### Containers:

```csv
Container ID,Width,Depth,Height
C1,50,50,50
C2,30,30,30
```

---

## 🚀 Setup and Installation

### Backend Setup:

```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Setup:

```bash
cd frontend
npm install
npm start
```

* Access the app at: [http://localhost:3000](http://localhost:3000)

---

## 📈 Future Plans

* Enhanced 3D visualization with Three.js for better item arrangement insights.
* Real-time algorithm adjustments based on user preferences.
* Integration with other spacecraft systems via REST API.

---

## 👨‍🚀 About

This project was initially developed as part of a space systems software design hackathon. It combines logistics management principles with zero-gravity-specific challenges, offering a robust and scalable solution for space mission resource management.

---

## 📬 Contact

For feedback, ideas, or collaboration opportunities:

* 📧 \danishaffan678@gmail.com
* 🔗 \[[Your LinkedIn Profile]](https://www.linkedin.com/in/affan-danish-08a144353/)

---

## 📄 License

This project is licensed under the MIT License.

### Use it, improve it, share it.
