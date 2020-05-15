import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

engine = create_engine("sqlite:///hawaii.sqlite", connect_args={'check_same_thread': False})


Base = automap_base()
Base.prepare(engine, reflect=True)
Base.classes.keys()

Measurement = Base.classes.measurement
Station = Base.classes.station

session = Session(engine)

#weather app
app = Flask(__name__)


last_date = session.query(Measurement.date).order_by(Measurement.date.desc()).first()[0]
last_datetime = dt.datetime.strptime(last_date, '%Y-%m-%d')
first_datetime = last_datetime - dt.timedelta(days=365)

station_sums = (session.query(Measurement.station, func.count(Measurement.prcp))
                       .group_by(Measurement.station)
                       .order_by(func.count(Measurement.station).desc())
                       .all())


@app.route("/")
def home():
    return (f"Available Routes:<br/>"
            f"/api/v1.0/precipitaton<br/>"
            f"/api/v1.0/stations<br/>"
            f"/api/v1.0/temperature<br/>"
            f"/api/v1.0/startdate ---- #Calculates the min, avg, and max temps for dates greater than or equal to that date indicated<br/>"
            f"/api/v1.0/startdate/lastdate ---- #Calculates the min, avg, and max for days between the two dates indicated inclusive<br/>"
            )

@app.route("/api/v1.0/stations")
def stations():
    station_count = session.query(Station.station).all()
    all_stations = list(np.ravel(station_count))
    return jsonify(all_stations)

@app.route("/api/v1.0/precipitaton")
def precipitation():
    
    prcp = (session.query(Measurement.date, Measurement.prcp)
                   .filter(Measurement.date > first_datetime)
                   .order_by(Measurement.date)
                   .all())

    return jsonify(prcp)

@app.route("/api/v1.0/temperature")
def temperature():

    temps = (session.query(Measurement.date, Measurement.tobs)
                       .filter(Measurement.date > first_datetime)
                       .filter(Measurement.station == station_sums[0][0])
                       .order_by(Measurement.date)
                       .all())

    return jsonify(temps)

@app.route('/api/v1.0/<startdate>')
def start(startdate):
    results =  (session.query(Measurement.date, func.min(Measurement.tobs), 
                              func.avg(Measurement.tobs), func.max(Measurement.tobs))
                       .filter(func.strftime("%Y-%m-%d", Measurement.date) >= startdate)
                       .group_by(Measurement.date)
                       .all())

    data = []                       
    for result in results:
        result_dict = {}
        result_dict["Date"] = result[0]
        result_dict["Low Temp"] = result[1]
        result_dict["Avg Temp"] = round(result[2],2)
        result_dict["High Temp"] = result[3]
        data.append(result_dict)
    return jsonify(data)

@app.route('/api/v1.0/<startdate>/<lastdate>')
def date_range(startdate, lastdate):
    results =  (session.query(Measurement.date, func.min(Measurement.tobs), 
                              func.avg(Measurement.tobs), func.max(Measurement.tobs))
                             .filter(func.strftime("%Y-%m-%d", Measurement.date) >= startdate)
                             .filter(func.strftime("%Y-%m-%d", Measurement.date) <= lastdate)
                             .group_by(Measurement.date)
                             .all())

    data = []                       
    for result in results:
        result_dict = {}
        result_dict["Date"] = result[0]
        result_dict["Low Temp"] = result[1]
        result_dict["Avg Temp"] = round(result[2],2)
        result_dict["High Temp"] = result[3]
        data.append(result_dict)
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
