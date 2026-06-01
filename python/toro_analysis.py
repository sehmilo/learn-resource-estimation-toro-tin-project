"""
================================================================================
 TORO TIN PROJECT  -  Resource Estimation & Geostatistics Training Course
 Master analysis script
================================================================================
 Licence ANRML26-137 / EL-046017, Toro LGA, Bauchi State, Nigeria
 African Pits and Quarries Ltd.

 Reproduces every worked example and figure used in the 6-module course.
 Ordinary kriging is hand-coded so the module mathematics maps line-for-line
 onto runnable Python.  Run with:  python3 toro_analysis.py
================================================================================
"""
import os, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from scipy.spatial.distance import cdist
from scipy.optimize import curve_fit

# ----------------------------------------------------------------------
# 0. House style for all figures
# ----------------------------------------------------------------------
NAVY, BRONZE, TEAL = "#1f2a44", "#c8702d", "#2a7d8c"
SAND, INK, GRID    = "#e8dcc8", "#26303f", "#d8d4cb"
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": INK, "axes.labelcolor": INK, "axes.titlecolor": NAVY,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "font.size": 11, "axes.titlesize": 13, "axes.titleweight": "bold",
    "figure.dpi": 110,
})
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.dirname(BASE)
FIG  = os.path.join(BASE, "assets", "figures")
DATA = os.path.join(BASE, "data")
os.makedirs(FIG, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

def save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("   saved  " + name)

RESULTS = {}

# ======================================================================
# 1. LOAD & CLASSIFY THE TORO DATA
# ======================================================================
print("\n[1] Loading Toro datasets ...")
geo   = pd.read_csv(os.path.join(SRC, "Motimose_GeoChemData.csv"))
field = pd.read_csv(os.path.join(SRC, "Field Data Bauchi.csv"))

sep_tags = ["Nb", "Fe", "Zr", "SnO2+SiO2", "FeB", "SnO2 (2)"]
def is_separation(sid):
    s = str(sid)
    return any(t in s for t in sep_tags) and len(s.split()) > 1
geo["record_type"] = np.where(geo["Lab_Sample_ID"].apply(is_separation),
                              "lab_separation", "field_sample")
print(geo["record_type"].value_counts().to_string())

SN_FACTOR = 118.71 / 150.71
geo["Sn_pct"] = geo["SnO2"] * SN_FACTOR
fs = geo[geo["record_type"] == "field_sample"].copy()
print("   field samples (in-situ HMC grades): " + str(len(fs)))

comp = (fs.groupby("Field_Pit_ID")
          .agg(Location=("Location", "first"),
               Latitude=("Latitude", "first"), Longitude=("Longitude", "first"),
               n_splits=("SnO2", "size"), SnO2=("SnO2", "mean"),
               Nb2O5=("Nb2O5", "mean"), Ta2O5=("Ta2O5", "mean"))
          .reset_index())
comp["Sn_pct"] = comp["SnO2"] * SN_FACTOR
print("   composited pit locations: " + str(len(comp)))

lat0, lon0 = comp["Latitude"].mean(), comp["Longitude"].mean()
def to_metres(lat, lon):
    x = (lon - lon0) * 111320.0 * np.cos(np.radians(lat0))
    y = (lat - lat0) * 110540.0
    return x, y
comp["x"], comp["y"] = to_metres(comp["Latitude"].values, comp["Longitude"].values)
fs["x"],   fs["y"]   = to_metres(fs["Latitude"].values,   fs["Longitude"].values)
comp.to_csv(os.path.join(DATA, "toro_composited_pits.csv"), index=False)
fs.to_csv(os.path.join(DATA, "toro_field_samples.csv"), index=False)

S = fs["SnO2"].values
lnS = np.log(S)
print("\n   SnO2 (field, %% in HMC):  n=%d min=%.3f max=%.3f mean=%.3f "
      "median=%.3f std=%.3f CV=%.2f" % (len(S), S.min(), S.max(), S.mean(),
      np.median(S), S.std(ddof=1), S.std(ddof=1)/S.mean()))
print("   skewness=%.2f  log-skew=%.2f" % (stats.skew(S), stats.skew(lnS)))
RESULTS.update(dict(n=len(S), mn=float(S.min()), mx=float(S.max()),
    mean=float(S.mean()), median=float(np.median(S)), std=float(S.std(ddof=1)),
    cv=float(S.std(ddof=1)/S.mean()), skew=float(stats.skew(S)),
    logskew=float(stats.skew(lnS)), n_pits=int(len(comp)),
    n_sep=int((geo.record_type=="lab_separation").sum())))

# ======================================================================
# 2. EXPLORATORY DATA ANALYSIS  (Module 3)
# ======================================================================
print("\n[2] Exploratory data analysis ...")

fig, ax = plt.subplots(figsize=(7.2, 6.4))
dom_colors = {"Bishiwai village": TEAL, "Bishiwai-Yadabongo village": BRONZE,
              "Kadade-Gyadobongo": NAVY}
for loc, sub in fs.groupby("Location"):
    ax.scatter(sub["x"], sub["y"], s=70*np.sqrt(sub["SnO2"]),
               c=dom_colors.get(loc, "grey"), alpha=0.75,
               edgecolors="white", linewidths=0.8, label=loc)
ax.set_xlabel("Local easting (m)"); ax.set_ylabel("Local northing (m)")
ax.set_title("Toro field samples - symbol size scaled to SnO2 grade")
ax.legend(fontsize=8, loc="lower right", framealpha=0.95)
ax.set_aspect("equal", adjustable="datalim")
save(fig, "fig_location_map.png")

fig, ax = plt.subplots(figsize=(6.6, 4.4))
ax.hist(S, bins=12, color=TEAL, edgecolor="white", alpha=0.9)
ax.axvline(S.mean(), color=BRONZE, lw=2.2, label="mean = %.2f%%" % S.mean())
ax.axvline(np.median(S), color=NAVY, lw=2.2, ls="--",
           label="median = %.2f%%" % np.median(S))
ax.set_xlabel("SnO2 in heavy-mineral concentrate (%)"); ax.set_ylabel("Frequency")
ax.set_title("Raw SnO2 histogram - strong positive skew")
ax.legend()
save(fig, "fig_histogram.png")

fig, ax = plt.subplots(figsize=(6.6, 4.4))
ax.hist(lnS, bins=12, color=BRONZE, edgecolor="white", alpha=0.9)
ax.set_xlabel("ln(SnO2)"); ax.set_ylabel("Frequency")
ax.set_title("Log-transformed SnO2 - skew falls from %.2f to %.2f"
             % (stats.skew(S), stats.skew(lnS)))
save(fig, "fig_loghistogram.png")

fig, ax = plt.subplots(figsize=(6.0, 5.2))
(theo, ordd), (slope, icept, r) = stats.probplot(lnS, dist="norm")
ax.scatter(theo, ordd, c=TEAL, edgecolors="white", s=55, zorder=3)
ax.plot(theo, slope*np.array(theo)+icept, color=BRONZE, lw=2,
        label="R = %.3f" % r)
ax.set_xlabel("Standard normal quantile"); ax.set_ylabel("ln(SnO2) ordered values")
ax.set_title("Lognormal probability plot - points near the line")
ax.legend()
save(fig, "fig_probplot.png")

fig, ax = plt.subplots(figsize=(6.8, 4.6))
order = ["Bishiwai village", "Bishiwai-Yadabongo village", "Kadade-Gyadobongo"]
groups = [fs.loc[fs.Location == d, "SnO2"].values for d in order]
bp = ax.boxplot(groups, patch_artist=True, widths=0.55,
                tick_labels=["Bishiwai", "Yadabongo", "Kadade"])
for patch, c in zip(bp["boxes"], [TEAL, BRONZE, NAVY]):
    patch.set_facecolor(c); patch.set_alpha(0.65)
for med in bp["medians"]:
    med.set_color("white"); med.set_linewidth(2)
ax.set_ylabel("SnO2 in concentrate (%)")
ax.set_title("Grade by geographic domain - test of stationarity")
save(fig, "fig_boxplot_domain.png")

fig, ax = plt.subplots(figsize=(6.4, 4.6))
xs_sorted = np.sort(S)
p = (np.arange(1, len(xs_sorted)+1) - 0.5) / len(xs_sorted)
ax.plot(xs_sorted, p*100, "o-", color=TEAL, mfc="white", ms=6)
p975 = np.percentile(S, 97.5)
ax.axvline(p975, color=BRONZE, lw=2, ls="--",
           label="97.5th percentile = %.2f%%" % p975)
ax.set_xlabel("SnO2 (%)"); ax.set_ylabel("Cumulative probability (%)")
ax.set_title("Cumulative plot - upper tail and capping decision")
ax.legend()
save(fig, "fig_cumprob.png")

fig, ax = plt.subplots(figsize=(6.2, 4.8))
r_sn_nb = np.corrcoef(fs["SnO2"], fs["Nb2O5"])[0, 1]
ax.scatter(fs["SnO2"], fs["Nb2O5"], c=NAVY, edgecolors="white", s=55)
ax.set_xlabel("SnO2 (%)"); ax.set_ylabel("Nb2O5 (%)")
ax.set_title("Cassiterite vs columbite association  (r = %.2f)" % r_sn_nb)
save(fig, "fig_scatter_sn_nb.png")
RESULTS.update(p975=float(p975), r_sn_nb=float(r_sn_nb))
print("   corr(SnO2,Nb2O5)=%.3f   97.5pct=%.3f" % (r_sn_nb, p975))

# ======================================================================
# 3. VARIOGRAPHY  (Module 4)
# ======================================================================
print("\n[3] Variography ...")
xc, yc, zc = comp["x"].values, comp["y"].values, comp["SnO2"].values

def experimental_variogram(x, y, z, lag, nlags, tol=None, azim=None, atol=None):
    if tol is None:
        tol = lag / 2.0
    nn_ = len(z)
    dx = x[:, None] - x[None, :]
    dy = y[:, None] - y[None, :]
    h  = np.sqrt(dx**2 + dy**2)
    diff2 = (z[:, None] - z[None, :])**2
    iu = np.triu_indices(nn_, k=1)
    h, diff2, dx, dy = h[iu], diff2[iu], dx[iu], dy[iu]
    if azim is not None:
        ang = np.degrees(np.arctan2(dx, dy)) % 180.0
        da  = np.abs((ang - (azim % 180.0) + 90) % 180 - 90)
        keep = da <= atol
        h, diff2 = h[keep], diff2[keep]
    lags, gam, npair = [], [], []
    for k in range(1, nlags + 1):
        centre = k * lag
        m = np.abs(h - centre) <= tol
        if m.sum() >= 2:
            lags.append(centre); gam.append(0.5 * diff2[m].mean())
            npair.append(int(m.sum()))
    return np.array(lags), np.array(gam), np.array(npair)

def spherical(h, nugget, sill, rng):
    h = np.asarray(h, float)
    g = np.where(h <= rng,
                 nugget + (sill - nugget) * (1.5*h/rng - 0.5*(h/rng)**3),
                 sill)
    return np.where(h == 0, 0.0, g)

LAG, NLAG = 180.0, 9
hlag, ghat, npr = experimental_variogram(xc, yc, zc, LAG, NLAG)
print("   omnidirectional experimental variogram:")
for h_, g_, n_ in zip(hlag, ghat, npr):
    print("     h=%6.0f m   gamma=%6.3f   pairs=%d" % (h_, g_, n_))

var_data = float(np.var(zc, ddof=1))
reliable = npr >= 20
SILL = var_data
def spherical_fixed(h, nugget, rng):
    return spherical(h, nugget, SILL, rng)
popt, _ = curve_fit(spherical_fixed, hlag[reliable], ghat[reliable],
                    p0=[0.4*SILL, 700.0], bounds=([0, 120], [SILL, 1600]),
                    sigma=1.0/np.sqrt(npr[reliable]), maxfev=20000)
NUGGET, RANGE = float(popt[0]), float(popt[1])
print("   fit uses %d reliable lags (>=20 pairs)" % int(reliable.sum()))
print("   spherical: nugget=%.3f sill=%.3f range=%.0f m nugget/sill=%.2f"
      % (NUGGET, SILL, RANGE, NUGGET/SILL))

fig, ax = plt.subplots(figsize=(7.0, 4.8))
ax.scatter(hlag, ghat, s=90, c=TEAL, edgecolors="white", zorder=3,
           label="experimental")
for h_, g_, n_ in zip(hlag, ghat, npr):
    ax.annotate(str(n_), (h_, g_), textcoords="offset points",
                xytext=(0, 9), ha="center", fontsize=8, color=NAVY)
hh = np.linspace(0, NLAG*LAG, 200)
ax.plot(hh, spherical(hh, NUGGET, SILL, RANGE), color=BRONZE, lw=2.4,
        label="fitted spherical model")
ax.axhline(SILL, color="grey", ls="--", lw=1.2, label="sample variance = sill")
ax.axvline(RANGE, color=NAVY, ls=":", lw=1.4)
ax.text(RANGE+25, 0.4, "range\n%.0f m" % RANGE, fontsize=8, color=NAVY)
ax.text(20, NUGGET+0.25, "nugget %.2f" % NUGGET, fontsize=8, color=NAVY)
ax.set_xlabel("Lag distance h (m)"); ax.set_ylabel("Semivariance  gamma(h)")
ax.set_title("Toro SnO2 - omnidirectional experimental variogram + model")
ax.legend(loc="upper left", fontsize=8.5)
save(fig, "fig_variogram_omni.png")

fig, axs = plt.subplots(1, 2, figsize=(10.4, 4.7))
for ax, centre in zip(axs, [LAG, 4*LAG]):
    dx = xc[:, None]-xc[None, :]; dy = yc[:, None]-yc[None, :]
    h  = np.sqrt(dx**2+dy**2); iu = np.triu_indices(len(zc), k=1)
    m  = np.abs(h[iu]-centre) <= LAG/2
    zi = np.repeat(zc[:, None], len(zc), 1)[iu][m]
    zj = np.repeat(zc[None, :], len(zc), 0)[iu][m]
    rr = np.corrcoef(zi, zj)[0, 1] if len(zi) > 2 else np.nan
    ax.scatter(zi, zj, c=TEAL, edgecolors="white", s=55)
    ax.scatter(zj, zi, c=TEAL, edgecolors="white", s=55)
    lim = [0, max(zc)*1.05]
    ax.plot(lim, lim, color=NAVY, ls="--", lw=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("SnO2 at x  (%)"); ax.set_ylabel("SnO2 at x + h  (%)")
    ax.set_title("h-scatterplot, h = %.0f m  (r = %.2f)" % (centre, rr))
save(fig, "fig_hscatter.png")

fig, ax = plt.subplots(figsize=(7.0, 4.8))
for azim, col, lab in [(0, TEAL, "N-S (000)"), (90, BRONZE, "E-W (090)")]:
    hl, gh, _n = experimental_variogram(xc, yc, zc, 240, 6, azim=azim, atol=45)
    ax.plot(hl, gh, "o-", color=col, mfc="white", ms=7, lw=1.8, label=lab)
ax.axhline(var_data, color="grey", ls="--", lw=1.2, label="sample variance")
ax.set_xlabel("Lag distance h (m)"); ax.set_ylabel("Semivariance gamma(h)")
ax.set_title("Directional variograms - screening for anisotropy")
ax.legend(fontsize=9)
save(fig, "fig_variogram_directional.png")

with open(os.path.join(DATA, "variogram_fit.json"), "w") as f:
    json.dump({"nugget": NUGGET, "sill": SILL, "range": RANGE,
               "lag": LAG, "nlags": NLAG, "exp_h": hlag.tolist(),
               "exp_g": ghat.tolist(), "exp_n": npr.tolist(),
               "sample_variance": var_data}, f, indent=2)
RESULTS.update(nugget=NUGGET, sill=SILL, vrange=RANGE, nugget_ratio=NUGGET/SILL)

# ======================================================================
# 4. GRADE ESTIMATION  (Module 5)
# ======================================================================
print("\n[4] Grade estimation ...")

def gamma_model(h):
    return spherical(h, NUGGET, SILL, RANGE)

pad = 150.0
gx = np.arange(xc.min()-pad, xc.max()+pad, 60.0)
gy = np.arange(yc.min()-pad, yc.max()+pad, 60.0)
GX, GY = np.meshgrid(gx, gy)
flatx, flaty = GX.ravel(), GY.ravel()

# ordinary kriging, hand-coded
n = len(zc)
Ddd = cdist(np.c_[xc, yc], np.c_[xc, yc])
A = np.zeros((n+1, n+1))
A[:n, :n] = gamma_model(Ddd)
A[:n, n] = 1.0; A[n, :n] = 1.0; A[n, n] = 0.0
Ainv = np.linalg.inv(A)

def ok_point(x0, y0):
    d0 = np.sqrt((xc-x0)**2 + (yc-y0)**2)
    b = np.empty(n+1)
    b[:n] = gamma_model(d0); b[n] = 1.0
    w = Ainv @ b
    est = float(np.dot(w[:n], zc))
    var = float(np.dot(w[:n], b[:n]) + w[n])
    return max(est, 0.0), max(var, 0.0)

ok_est = np.empty(flatx.size); ok_var = np.empty(flatx.size)
for i in range(flatx.size):
    ok_est[i], ok_var[i] = ok_point(flatx[i], flaty[i])
ok_est = ok_est.reshape(GX.shape)
ok_var = ok_var.reshape(GX.shape)

def idw(x0, y0, power=2.0):
    d = np.sqrt((xc-x0)**2 + (yc-y0)**2)
    if d.min() < 1e-6:
        return zc[d.argmin()]
    w = 1.0 / d**power
    return float(np.dot(w, zc) / w.sum())
idw_est = np.array([idw(x, y) for x, y in zip(flatx, flaty)]).reshape(GX.shape)

def nn(x0, y0):
    d = np.sqrt((xc-x0)**2 + (yc-y0)**2)
    return float(zc[d.argmin()])
nn_est = np.array([nn(x, y) for x, y in zip(flatx, flaty)]).reshape(GX.shape)

vmax = float(np.nanpercentile(np.concatenate([ok_est.ravel(), idw_est.ravel()]), 99))
extent = [gx.min(), gx.max(), gy.min(), gy.max()]

fig, ax = plt.subplots(figsize=(6.4, 6.6))
im = ax.imshow(idw_est, origin="lower", extent=extent, cmap="YlOrBr",
               vmin=0, vmax=vmax, aspect="equal")
ax.scatter(xc, yc, c="k", s=18, edgecolors="white", linewidths=0.6)
ax.set_title("Inverse distance weighting (power 2)")
ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)")
fig.colorbar(im, ax=ax, shrink=0.8, label="SnO2 (%)")
save(fig, "fig_idw.png")

fig, axs = plt.subplots(1, 2, figsize=(12.4, 6.4))
im0 = axs[0].imshow(ok_est, origin="lower", extent=extent, cmap="YlOrBr",
                    vmin=0, vmax=vmax, aspect="equal")
axs[0].scatter(xc, yc, c="k", s=18, edgecolors="white", linewidths=0.6)
axs[0].set_title("Ordinary kriging - estimate")
axs[0].set_xlabel("Easting (m)"); axs[0].set_ylabel("Northing (m)")
fig.colorbar(im0, ax=axs[0], shrink=0.8, label="SnO2 (%)")
im1 = axs[1].imshow(np.sqrt(ok_var), origin="lower", extent=extent,
                    cmap="viridis", aspect="equal")
axs[1].scatter(xc, yc, c="red", s=18, edgecolors="white", linewidths=0.6)
axs[1].set_title("Ordinary kriging - standard error")
axs[1].set_xlabel("Easting (m)"); axs[1].set_ylabel("Northing (m)")
fig.colorbar(im1, ax=axs[1], shrink=0.8, label="kriging std. error")
save(fig, "fig_kriging.png")

xval = np.empty(n)
for i in range(n):
    keep = np.arange(n) != i
    xs, ys, zs = xc[keep], yc[keep], zc[keep]
    m = keep.sum()
    Ai = np.zeros((m+1, m+1))
    Ai[:m, :m] = gamma_model(cdist(np.c_[xs, ys], np.c_[xs, ys]))
    Ai[:m, m] = 1; Ai[m, :m] = 1
    d0 = np.sqrt((xs-xc[i])**2 + (ys-yc[i])**2)
    b = np.empty(m+1); b[:m] = gamma_model(d0); b[m] = 1
    w = np.linalg.solve(Ai, b)
    xval[i] = np.dot(w[:m], zs)
resid = xval - zc
me   = float(resid.mean())
rmse = float(np.sqrt((resid**2).mean()))
r_xv = float(np.corrcoef(xval, zc)[0, 1])
print("   cross-validation:  ME=%.3f  RMSE=%.3f  r=%.3f" % (me, rmse, r_xv))

fig, ax = plt.subplots(figsize=(5.8, 5.6))
ax.scatter(zc, xval, c=TEAL, edgecolors="white", s=60, zorder=3)
lim = [0, max(zc.max(), xval.max())*1.05]
ax.plot(lim, lim, color=NAVY, ls="--", lw=1.4, label="1:1 line")
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Actual SnO2 (%)"); ax.set_ylabel("Kriged estimate (%)")
ax.set_title("Leave-one-out cross-validation\nME=%.2f  RMSE=%.2f  r=%.2f"
             % (me, rmse, r_xv))
ax.legend()
save(fig, "fig_xval.png")

nb = 6
edges = np.linspace(yc.min(), yc.max(), nb+1)
mid = 0.5*(edges[:-1]+edges[1:])
sw_data, sw_ok, sw_idw, sw_nn = [], [], [], []
for k in range(nb):
    hi = yc <= edges[k+1] if k == nb-1 else yc < edges[k+1]
    md = (yc >= edges[k]) & hi
    hg = flaty <= edges[k+1] if k == nb-1 else flaty < edges[k+1]
    mg = (flaty >= edges[k]) & hg
    sw_data.append(zc[md].mean() if md.any() else np.nan)
    sw_ok.append(ok_est.ravel()[mg].mean() if mg.any() else np.nan)
    sw_idw.append(idw_est.ravel()[mg].mean() if mg.any() else np.nan)
    sw_nn.append(nn_est.ravel()[mg].mean() if mg.any() else np.nan)
fig, ax = plt.subplots(figsize=(7.4, 4.6))
ax.plot(mid, sw_data, "o-", color=NAVY,  lw=2,  ms=8, label="data mean")
ax.plot(mid, sw_ok,   "s-", color=BRONZE, lw=2, ms=7, label="ordinary kriging")
ax.plot(mid, sw_idw,  "^-", color=TEAL,   lw=2, ms=7, label="IDW")
ax.plot(mid, sw_nn,   "d-", color="grey", lw=1.6, ms=6, label="nearest neighbour")
ax.set_xlabel("Northing band centre (m)"); ax.set_ylabel("Mean SnO2 (%)")
ax.set_title("Swath plot - global unbiasedness check (N-S bands)")
ax.legend(fontsize=8.5)
save(fig, "fig_swath.png")
RESULTS.update(xval_me=me, xval_rmse=rmse, xval_r=r_xv,
               ok_mean=float(np.nanmean(ok_est)))

# ======================================================================
# 5. BLOCK MODEL, CUT-OFF & GRADE-TONNAGE  (Module 6)
# ======================================================================
print("\n[5] Block model and grade-tonnage ...")
CELL, THICK, DENSITY = 60.0, 3.0, 1.9
block_t = CELL*CELL*THICK*DENSITY
grades = ok_est.ravel()
tonnes = np.full(grades.shape, block_t)

cutoffs = np.linspace(0, 6, 25)
tgrade, ttonnes = [], []
for c in cutoffs:
    sel = grades >= c
    ttonnes.append(tonnes[sel].sum())
    tgrade.append(grades[sel].mean() if sel.any() else np.nan)
ttonnes = np.array(ttonnes); tgrade = np.array(tgrade)

fig, ax1 = plt.subplots(figsize=(7.6, 4.8))
ax1.plot(cutoffs, ttonnes/1e3, color=TEAL, lw=2.6)
ax1.set_xlabel("Cut-off grade, SnO2 (%)")
ax1.set_ylabel("Tonnes above cut-off (kt)", color=TEAL)
ax1.tick_params(axis="y", colors=TEAL)
ax2 = ax1.twinx()
ax2.plot(cutoffs, tgrade, color=BRONZE, lw=2.6)
ax2.set_ylabel("Mean grade above cut-off, SnO2 (%)", color=BRONZE)
ax2.tick_params(axis="y", colors=BRONZE)
ax2.grid(False)
ax1.set_title("Grade-tonnage curve - the central trade-off of cut-off grade")
save(fig, "fig_gradetonnage.png")

CUT = 2.0
fig, ax = plt.subplots(figsize=(6.4, 6.6))
disp = np.where(ok_est >= CUT, ok_est, np.nan)
im = ax.imshow(disp, origin="lower", extent=extent, cmap="YlOrBr",
               vmin=0, vmax=vmax, aspect="equal")
ax.imshow(np.where(ok_est < CUT, 1.0, np.nan), origin="lower", extent=extent,
          cmap="Greys", alpha=0.18, aspect="equal")
ax.scatter(xc, yc, c="k", s=16, edgecolors="white", linewidths=0.6)
ax.set_title("Block model - cells above %.1f%% SnO2 cut-off" % CUT)
ax.set_xlabel("Easting (m)"); ax.set_ylabel("Northing (m)")
fig.colorbar(im, ax=ax, shrink=0.8, label="SnO2 (%)")
save(fig, "fig_blockmodel.png")

n_above = int((grades >= CUT).sum())
print("   blocks total=%d above %.1f%%=%d tonnes_above=%.0f kt grade_above=%.2f%%"
      % (grades.size, CUT, n_above, tonnes[grades>=CUT].sum()/1e3,
         grades[grades>=CUT].mean()))
RESULTS.update(block_total=int(grades.size), block_above=n_above,
               kt_above=float(tonnes[grades>=CUT].sum()/1e3),
               grade_above=float(grades[grades>=CUT].mean()))

# ======================================================================
# 6. ALLUVIAL g/m3 CHAIN  &  BENCHMARK COMPARISON  (Module 6)
# ======================================================================
print("\n[6] Alluvial g/m3 chain and benchmarks ...")
recoveries_kg = {"Mining Pit\n(pt 2)": 2.0, "Kadade\n(pt 11)": 1.0,
                 "R. Bishwai\n(pt 13)": 2.0, "Kadade\n(pt 16)": 1.0,
                 "GN-005": 0.351}
bulk_kg = 200.0
sn_grade_hmc = S.mean() * SN_FACTOR / 100.0
gravel_density = 1.9
rows = []
for name, hmc in recoveries_kg.items():
    yld = hmc / bulk_kg * 100.0
    sn_kg = hmc * sn_grade_hmc
    vol_m3 = (bulk_kg/1000.0) / gravel_density
    g_per_m3 = sn_kg * 1000.0 / vol_m3
    rows.append((name.replace("\n", " "), yld, g_per_m3))
allu = pd.DataFrame(rows, columns=["pit", "hmc_yield_pct", "Sn_g_per_m3"])
print(allu.to_string(index=False))
allu.to_csv(os.path.join(DATA, "alluvial_gm3.csv"), index=False)

fig, ax = plt.subplots(figsize=(7.4, 4.4))
ax.bar(list(recoveries_kg.keys()), allu["Sn_g_per_m3"], color=BRONZE,
       edgecolor="white")
ax.axhline(allu["Sn_g_per_m3"].mean(), color=NAVY, ls="--", lw=2,
           label="mean = %.0f g/m3" % allu["Sn_g_per_m3"].mean())
ax.set_ylabel("In-situ Sn (g/m3)")
ax.set_title("Alluvial grade chain - from 200 kg bulk samples")
ax.legend()
save(fig, "fig_alluvial.png")
RESULTS.update(allu_mean_gm3=float(allu["Sn_g_per_m3"].mean()),
               allu_min_gm3=float(allu["Sn_g_per_m3"].min()),
               allu_max_gm3=float(allu["Sn_g_per_m3"].max()),
               sn_grade_hmc_pct=float(sn_grade_hmc*100))

fig, ax = plt.subplots(figsize=(7.0, 4.4))
labels = ["Alphamin Bisie\nMRE class ~2.5%+ Sn", "Achmmach\nM+I 0.70% Sn",
          "Toro\nExploration Target"]
gr = [2.50, 0.70, 0.0]
bars = ax.bar(labels, gr, color=[NAVY, TEAL, BRONZE], edgecolor="white")
ax.set_ylabel("Primary resource grade, % Sn")
ax.set_title("Benchmark grades - where a hard-rock tin project must land")
ax.text(2, 0.18, "not yet\nclassified", ha="center", fontsize=9, color=BRONZE)
save(fig, "fig_benchmark.png")

with open(os.path.join(DATA, "results.json"), "w") as f:
    json.dump(RESULTS, f, indent=2)
print("\n   key results exported to data/results.json")
print("   DONE - all figures generated.")
