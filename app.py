from flask import Flask, request, render_template
import requests as req
import csv
from collections import defaultdict
from configparser import ConfigParser
from datetime import datetime
import os
import matplotlib.pyplot as plt
import xarray as x
import cartopy.crs as ccrs
import cartopy.feature as cf
from io import BytesIO
from PIL import Image

ini = ConfigParser()
ini.read("config.ini")
app = Flask(__name__)
apiw = ini["gfg"]["apiw"]
apin = ini["gfg"]["apin"]

countrycities = defaultdict(list)

with open("worldcities.csv", encoding="utf-8") as csvfile:
  reader = csv.DictReader(csvfile)
  for row in reader:
    countrycode = row.get("iso2")
    city = row.get("city")
    if countrycode and city:
      if city not in countrycities[countrycode]:
        countrycities[countrycode].append(city)
@app.route("/", methods=["GET", "POST"])
def index():
  weather = None
  selected_city = ""
  selected_country = ""
  selected_time = ""
  map_image = None # To store generated map
  if request.method == "POST":
    selected_city = request.form["city"]
    selected_country = request.form["iso2"]
    sselected_time = request.form["time"]
    # Weather API
    urlw = "api.openweathermap.org/data/2.5/forecast"
    paramsw = {
      "q": f"{selected_city},{selected_country}",
      "appid": apiw,
      "units": "metric"
    }
    resw = req.get(urlw, params=params)
    data = resw.json()

    if resw.status_code != 200:
      weather = {"description": f"API Error: {data.get("message", "Unknown")}"}
    elif data.get("cod") == "4-4":
      weather = {"description": f"Forecast data unavailable for {selected_city}, {selected_country}"}
    else:
      try:
        time = datetime.strptime(selected_time, "%Y-%m-%d %H:%M")
        if "list" not in data:
          weather = {"description": "No forecast data available"}
        else:
          closest = min(
            data["list"],
            key = lambda f: abs(datetime.fromtimestamp(f["dt"]) - time)
          )
        forecast_t = datetime.fromtimestamp(closest["dt"])
        temp = closest["main"]["temp"]
        desc = closest["weather"][0]["description"]
        rain = closest.get("rain", {}).get("3h", 0)
        weather = {
          "city": selected_city,
          "country": selected_country,
          "forecast_time": forecast_t.strftime("%Y-%m--%d %H:%M"),\
          "temp": temp,
          "description": desc,
          "rain": f"{rain}mm in last 3h" if rain else "No rain"
        }
      except req.exceptions.ConnectionError as rece:
        weather = {"description": "Connect to a network"}
      except Exception as e:
        weather = {"description": f"Error: {str(e)}"}

# NASA map
# Get the coordinates of city, country
urlwo = f"nominatim.openstreetmap.org/search?q={selected_city},{selected_country}&format=json"
reswo = req.get(urlwo).json()
if len(reswo) > 0:
  lat = float(reswo[0]["lat"])
  lon = float(reswo[0]["lon"])

# Get NASA map img
urln = "wvs.earthdata.nasa.gov/api/v1/snapshot"
bbox_size = 5
bbox = f"{lon - bbox_size}, {lat - bbox_size}, {lon + bbox_size}, {lat + bbox_size}"
paramsn = {
  "REQUEST": "GetSnapshot",
  "LAYERS": "MODIS_Terra_CorrectedReflectance_TrueColor",
  "BBOX": bbox,
  "CRS": "EPSG:4326",
  "FORMAT": "image/jpg",
  "WIDTH": 800,
  "HEIGHT": 600
}
resn = req.get(urln, params=paramsn)
img = Image.open(BytesIO(resn.content))

#  Mark city
plt.figure(figsize=(8,6))
plt.imshow(img, extent=[lon - bbox_size, lon + bbox_size, lat - bbox_size, lat + bbox_size])
plt.scatter(lon, lat, c="red", s=100, marker = "o")
plt.title(f"NASA map centered on {selected_city}")
plt.xlabel("Longtitude")
plt.ylabel("Latitude")

#Saving the plot to BytesIO for flask
buf = BytesIO()
plt.savefig(buf, format="jpg")
buf.seek(0)
plt.close()
map_img = buf

return render_template("index_main.html", 
                       selected_city=selected_city, 
                       selected_country=selected_country, 
                       selected_time=selected_time,
                       countrycities = countrycities,
                       map_img = map_img
                      )
@app.route("/support")
def support():
  return render_template("support.html")
@app.route("/map_img")
def map_img_r():
  map_img = request.args.get("map_img")
  if map_img:
    return send_file(map_img, mimetype = "image/jpg")
  return "No map available"

if __name__ == "__main__":
  app.run(debug=True)
