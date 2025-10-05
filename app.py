from flask import Flask, request, render_template
import requests as req
from datetime import datetime
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
import base64
from configparser import ConfigParser

# --- Load config ---
ini = ConfigParser()
ini.read("config.ini")
APIW = ini["gfg"]["apiw"]
APIN = ini["gfg"]["apin"]

app = Flask(__name__, template_folder="templates")

@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    map_img = None
    map_base64 = None
    selected_country = ""
    selected_city = ""
    selected_time = ""

    if request.method == "POST":
        selected_country = request.form.get("country", "")
        selected_city = request.form.get("city", "")
        selected_time = request.form.get("time", "")

        if selected_country and selected_city:
            # --- OpenWeatherMap API ---
            try:
                urlw = "https://api.openweathermap.org/data/2.5/forecast"
                paramsw = {"q": f"{selected_city},{selected_country}", "appid": APIW, "units": "metric"}
                resw = req.get(urlw, params=paramsw, timeout=10)
                resw.raise_for_status()
                data = resw.json()
                if "list" in data and selected_time:
                    time_obj = datetime.strptime(selected_time, "%Y-%m-%d %H:%M")
                    closest = min(
                        data["list"],
                        key=lambda f: abs(datetime.fromtimestamp(f["dt"]) - time_obj)
                    )
                    forecast_t = datetime.fromtimestamp(closest["dt"])
                    temp = closest["main"]["temp"]
                    desc = closest["weather"][0]["description"]
                    rain = closest.get("rain", {}).get("3h", 0)
                    weather = {
                        "city": selected_city,
                        "country": selected_country,
                        "forecast_time": forecast_t.strftime("%Y-%m-%d %H:%M"),
                        "temp": temp,
                        "description": desc,
                        "rain": f"{rain} mm in last 3h" if rain else "No rain"
                    }
            except Exception as e:
                weather = {"description": f"Weather API error: {e}"}

            # --- OSM coordinates ---
            try:
                urlwo = f"https://nominatim.openstreetmap.org/search?q={selected_city},{selected_country}&format=json"
                headers = {"User-Agent": "SkyCastApp/1.0 (your_email@example.com)"}
                reswo = req.get(urlwo, headers=headers, timeout=10)
                data_osm = reswo.json() if reswo.status_code == 200 else []
                if data_osm:
                    lat = float(data_osm[0]["lat"])
                    lon = float(data_osm[0]["lon"])
                else:
                    weather = {"description": "Location not found"}
                    lat, lon = None, None
            except Exception as e:
                weather = {"description": f"OpenStreetMap error: {e}"}
                lat, lon = None, None

            # --- NASA map ---
            if lat is not None and lon is not None:
              try:
                urln = "https://wvs.earthdata.nasa.gov/api/v1/snapshot"
                bbox_size = 0.5  # smaller bbox = closer to city
                bbox = f"{lon - bbox_size},{lat - bbox_size},{lon + bbox_size},{lat + bbox_size}"
                paramsn = {
                  "REQUEST": "GetSnapshot",
                  "LAYERS": "MODIS_Terra_CorrectedReflectance_TrueColor",
                  "BBOX": bbox,
                  "CRS": "EPSG:4326",
                  "FORMAT": "image/jpeg",
                  "WIDTH": 800,
                  "HEIGHT": 600,
                  "TIME": datetime.utcnow().strftime("%Y-%m-%d")  # latest image for today
                }
                resn = req.get(urln, params=paramsn, timeout=10)
                if resn.status_code == 200:
                  img = Image.open(BytesIO(resn.content))
                  plt.figure(figsize=(8, 6))
                  plt.imshow(img, extent=[lon - bbox_size, lon + bbox_size, lat - bbox_size, lat + bbox_size])
                  plt.scatter(lon, lat, c="red", s=100, marker="o")
                  plt.title(f"NASA map centered on {selected_city}")
                  plt.xlabel("Longitude")
                  plt.ylabel("Latitude")
                  buf = BytesIO()
                  plt.savefig(buf, format="jpeg")
                  buf.seek(0)
                  plt.close()
                  map_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
              except Exception as e:
                weather = {"description": f"NASA map error: {e}"}

    return render_template(
        "index_main.html",
        selected_country=selected_country,
        selected_city=selected_city,
        selected_time=selected_time,
        weather=weather,
        map_img=map_base64
    )

if __name__ == "__main__":
    app.run(debug=True)
