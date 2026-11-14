#!/usr/bin/env python3
"""Вырезает фрагменты РЕАЛЬНОГО марсианского рельефа из HRSC/MOLA blend DEM.

Источник: USGS Astrogeology, Mars MGS MOLA - MEX HRSC Blended DEM Global 200m v2
          https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m
          11 ГБ, читается удалённо через GDAL /vsicurl/ — скачивать целиком не нужно.

Разрешение 200 м/пиксель. На участок 25 км это 125 пикселей — ровно то, что
нужно сетке 84x84 (с запасом на передискретизацию). MOLA 463 м/px дала бы 54 px
и была бы непригодна.

Результат: JSON с полем высот, который фронтенд грузит вместо синтетики.
"""
import json
import pathlib
import subprocess
import sys

DEM = ("/vsicurl/https://planetarymaps.usgs.gov/mosaic/Mars/HRSC_MOLA_Blend/"
       "Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif")

N = 84                      # размер сетки приложения
AREA_KM = 25.0              # сторона участка
MARS_R = 3396190.0
DEG_PER_KM = 360.0 / (2 * 3.141592653589793 * MARS_R / 1000.0)

# Реальные места на Марсе с разной физикой движения.
SITES = [
    dict(id="jezero",  name="Jezero Crater",
         lat=18.44, lon=77.45,
         blurb="Perseverance landing site. Crater rim and delta: steep rim, "
               "flat floor — the return cost is strongly anisotropic."),
    dict(id="gale",    name="Gale Crater / Aeolis Mons",
         lat=-5.08, lon=137.85,
         blurb="Curiosity landing site. Central mound rising from a crater "
               "floor — a sustained climb in every direction from the base."),
    dict(id="melas",   name="Melas Chasma (Valles Marineris)",
         lat=-9.80, lon=283.80,
         blurb="Canyon floor with multi-kilometre walls. The envelope is "
               "forced along the valley; walls are impassable and shield "
               "against GCR."),
    dict(id="elysium", name="Elysium Planitia",
         lat=4.50, lon=135.90,
         blurb="InSight landing site. A flat volcanic plain — the envelope is "
               "nearly circular, which is the control case: shape comes from "
               "terrain, not from drawing."),
]


def fetch(site):
    half = AREA_KM / 2 * DEG_PER_KM
    lon = site["lon"] if site["lon"] <= 180 else site["lon"] - 360
    ulx, uly = lon - half, site["lat"] + half
    lrx, lry = lon + half, site["lat"] - half

    out = f"/tmp/dem_{site['id']}.tif"
    cmd = ["gdal_translate", "-q", "-projwin", str(ulx), str(uly), str(lrx), str(lry),
           "-outsize", str(N), str(N), "-r", "cubic", "-ot", "Float32", DEM, out]
    subprocess.run(cmd, check=True, timeout=600,
                   env={"GDAL_HTTP_TIMEOUT": "90", "GDAL_HTTP_MAX_RETRY": "4",
                        "PATH": "/usr/bin:/bin", "CPL_VSIL_CURL_CHUNK_SIZE": "1048576"})

    txt = f"/tmp/dem_{site['id']}.txt"
    subprocess.run(["gdal_translate", "-q", "-of", "AAIGrid", out, txt],
                   check=True, timeout=120)
    vals, started = [], False
    for line in pathlib.Path(txt).read_text().split("\n"):
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() or line[0] == "-":
            if not started and any(c.isalpha() for c in line):
                continue
            started = True
            vals.extend(float(v) for v in line.split())
    if len(vals) < N * N:
        raise RuntimeError(f"{site['id']}: получено {len(vals)} значений, нужно {N*N}")
    vals = vals[:N * N]
    if min(vals) < -30000:
        raise RuntimeError(f"{site['id']}: в данных есть NoData")
    return vals


def main():
    out = {"source": "USGS/NASA/DLR — MOLA + HRSC Blended DEM, 200 m/px",
           "url": "https://astrogeology.usgs.gov/search/map/"
                  "mars_mgs_mola_mex_hrsc_blended_dem_global_200m",
           "grid": N, "area_km": AREA_KM, "sites": []}
    for s in SITES:
        print(f"  {s['name']:38}", end=" ", flush=True)
        try:
            vals = fetch(s)
            rng = max(vals) - min(vals)
            out["sites"].append({**s, "elev": [round(v, 1) for v in vals]})
            print(f"ok  {min(vals):7.0f}..{max(vals):7.0f} м  (перепад {rng:5.0f} м)")
        except Exception as e:
            print(f"ОШИБКА: {e}")
            return 1
    dst = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "terrain.json")
    dst.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"\n{dst}  {dst.stat().st_size // 1024} КБ, площадок: {len(out['sites'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
