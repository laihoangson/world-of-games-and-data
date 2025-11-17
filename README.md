# World of Games and Data 🎮

## URL

The URL for the website is [https://laihoangson.github.io/world-of-games/](https://laihoangson.github.io/world-of-games/)

## Games Collection

### 🐍 Neon Snake
Classic snake game with modern neon aesthetics, power-ups, and dynamic obstacles.

### ✈️ Flappy Plane Adventure
Side-scrolling flight game with shooting mechanics, coin collection, and UFO enemies.

### 🎹 Interactive Piano & Cat Game
Dual application featuring a functional web piano and an endless runner cat game.

### 🧱 Neon Brick Breaker
Arcade brick breaker with power-ups, multiple levels, and neon visual effects.

## Real-time Analytics System

The Flappy Plane game includes an advanced analytics system that tracks:
- Player performance metrics
- Game session data
- Death reasons analysis
- Score distribution

### 🚀 Running Real-time Analytics

To enable the live analytics dashboard for Flappy Plane:

1. Navigate to the analytics folder:
```bash
cd analytics
```

2. Run the Python analytics server:

```bash
python analytics_plane.py
```

3. The server will start on http://localhost:5000

4. Open analytics/analysis_plane.html in your browser to view the live dashboard  

## 📊 Data Analysis Report "Game Analytics: From Bootstrapping to Predictive Modeling"

### 🔍 Key Analysis Features:

**📈 Exploratory Data Analysis (EDA)**
- Score and gameplay duration distributions
- Death reason analysis and patterns
- Correlation between game metrics
- Player performance visualization

**🤖 Predictive Modeling**
- **Survival Prediction**: Machine learning model to predict player survival beyond 10 seconds
- **Score Forecasting**: Regression models to forecast player scores based on gameplay behavior
- **Player Segmentation**: Clustering analysis to identify distinct player skill groups
- **Random Forest algorithms** for accurate predictions

