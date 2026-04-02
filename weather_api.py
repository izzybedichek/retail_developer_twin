# Claude because was struggling to find documentation for how to apply OpenWeatherMap in Python
# Claude suggested meteostat, which I have used before, so I switched over
# meteostat cause lots of ceritifcate issues, so I used pip install openmeteo

import pandas as pd
import requests

# ref https://open-meteo.com/en/docs?latitude=37.3394&longitude=-121.895&timezone=auto&forecast_days=1&past_days=92

# Make sure all required weather variables are listed here
# The order of variables in daily is important to assign them correctly below
params = {
	"latitude": 37.3394,
	"longitude": -121.895,
	"daily": ["temperature_2m_max", "rain_sum", "snowfall_sum", "precipitation_sum"],
	"timezone": "auto",
	"start_date": "2026-01-03",
	"end_date": "2026-04-02",
}
r    = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params)
data = r.json()

df = pd.DataFrame(data["daily"])
df["time"] = pd.to_datetime(df["time"])
df = df.set_index("time")
df.columns = ["temp_max", "rain_sum", "snowfall_sum", "precipitation_sum"]

print(df.head(10))
df.to_csv("palo_alto_weather.csv")
