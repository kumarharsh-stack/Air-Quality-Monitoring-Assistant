
Air Quality Assistant

An AI-powered, beginner-friendly web application that helps users monitor air quality for any city, understand pollution levels, receive health recommendations, view historical AQI data, and predict future PM2.5 levels using Machine Learning.

The project combines Flask, Open-Meteo APIs, SQLite, Chart.js, and Scikit-learn into a single web application.

 Features
 City-based Air Quality Search
Enter any city and retrieve its current air-quality information.
The application converts the city name into geographical coordinates using geocoding.
 Live Air Quality Data
Retrieves current AQI and pollutant information using the Open-Meteo Air Quality API.
Displays parameters such as:
US AQI
PM2.5
PM10
Ozone
Nitrogen Dioxide
Health Recommendations
Provides easy-to-understand health advice based on the current AQI level.
Historical AQI Chart
Search results are stored in a local SQLite database.
Previous readings can be visualized using a Chart.js line chart. PM2.5 Prediction
Uses a RandomForestRegressor model from Scikit-learn.
Predicts the next PM2.5 value using recent historical readings.
 Air Quality Assistant
Includes a rule-based question-answering assistant.
Can optionally be upgraded with Claude for more natural responses.
The application continues to work without an API key.
 Local Database
SQLite database is automatically initialized when the application starts.
 Technologies Used
Technology	Purpose
Python	Core programming language
Flask	Backend web framework
Open-Meteo API	Geocoding and air-quality data
SQLite	Local data storage
Scikit-learn	Machine Learning
Random Forest	PM2.5 prediction
NumPy	Numerical operations
Matplotlib	ML evaluation visualization
HTML/CSS/JavaScript	Frontend
Chart.js	Historical data visualization
Claude API	Optional AI assistant

The core dependencies are defined in requirements.txt
