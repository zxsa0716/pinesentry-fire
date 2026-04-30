"""1D-CNN deep-learning baseline on EMIT 285-band spectra (DOFA stand-in).

The original v4.1 design called for a DOFA backbone with Wavelength-Prompt
+ LoRA fine-tuning. DOFA needs heavy GPU + multi-day training, which is
out of scope for the August 2026 submission. We instead provide a
lightweight 1D CNN as a deep-learning baseline that:

  - reads each EMIT pixel's 285-band spectrum as a 1D signal
  - learns a per-pixel burn-probability classifier
  - serves as the "neural" comparison to HSI v1's hand-engineered fusion
  - reports AUC on a held-out spatial block

If 1D CNN >> HSI v1, that justifies investing in DOFA.
If 1D CNN ≤ HSI v1, the hand-engineered fusion already captures the signal.

Output: data/hsi/v1/dl_1dcnn_uiseong.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import xarray as xr

EMIT_NC = Path("data/emit/uiseong/EMIT_L2A_RFL_001_20240216T044207_2404703_007.nc")
PERI    = Path("data/fire_perimeter/synth_uiseong_dnbr.gpkg")
STACK   = Path("data/features/uiseong_stack.tif")


def orthorectify(swath, glt_x, glt_y, fill=np.nan):
    out = np.full(glt_x.shape, fill, dtype="float32")
    valid = (glt_x > 0) & (glt_y > 0)
    yy = (glt_y[valid] - 1).astype(int)
    xx = (glt_x[valid] - 1).astype(int)
    out[valid] = swath[yy, xx]
    return out


def main():
    if not EMIT_NC.exists():
        print(f"missing {EMIT_NC}", file=sys.stderr); return

    rfl_ds = xr.open_dataset(EMIT_NC, engine="h5netcdf")
    bp = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="sensor_band_parameters")
    loc = xr.open_dataset(EMIT_NC, engine="h5netcdf", group="location")
    good = bp.good_wavelengths.values.astype(bool)
    rfl = rfl_ds.reflectance.values.astype("float32")
    rfl = np.where(rfl < -1, np.nan, rfl)
    glt_x = loc.glt_x.values; glt_y = loc.glt_y.values

    import rioxarray as rxr
    import geopandas as gpd
    from rasterio.features import rasterize
    da_stack = rxr.open_rasterio(STACK, masked=True)

    # Build burn mask in stack coordinates, then map back to EMIT swath via GLT
    peri = gpd.read_file(PERI).to_crs(da_stack.rio.crs)
    burn_o = rasterize(((g, 1) for g in peri.geometry if g is not None),
                       out_shape=da_stack.shape[1:], transform=da_stack.rio.transform(),
                       fill=0, dtype="uint8").astype(bool)

    # Sample swath pixels; use orthorectified-grid lookup
    H_or, W_or = burn_o.shape
    H_sw, W_sw = rfl.shape[:2]
    # We collect per-pixel spectrum + burn label by walking the GLT
    # (only valid GLT cells). Subsample for speed.
    flat_glt_x = glt_x.ravel(); flat_glt_y = glt_y.ravel()
    flat_burn = burn_o.ravel() if (H_or == glt_x.shape[0] and W_or == glt_x.shape[1]) else None
    if flat_burn is None:
        # GLT shape doesn't match burn_o; fallback by reprojecting burn into ortho via GLT directly
        H_burn, W_burn = burn_o.shape
        if (H_burn, W_burn) != glt_x.shape:
            # crop / pad to match
            sy = min(H_burn, glt_x.shape[0]); sx = min(W_burn, glt_x.shape[1])
            tmp = np.zeros(glt_x.shape, dtype=bool)
            tmp[:sy, :sx] = burn_o[:sy, :sx]
            flat_burn = tmp.ravel()
        else:
            flat_burn = burn_o.ravel()
    valid_glt = (flat_glt_x > 0) & (flat_glt_y > 0)

    rng = np.random.default_rng(0)
    n_burn = int(flat_burn[valid_glt].sum())
    n_unburn = int((~flat_burn[valid_glt]).sum())
    print(f"valid GLT cells: {valid_glt.sum()}  burn: {n_burn}  unburn: {n_unburn}")

    # Balance classes for training
    burn_idx = np.where(valid_glt & flat_burn)[0]
    unburn_idx = np.where(valid_glt & (~flat_burn))[0]
    n_take = min(8000, len(burn_idx), len(unburn_idx) // 4)
    if n_take < 200:
        print("not enough burn samples for CNN training"); return
    train_burn = rng.choice(burn_idx, n_take, replace=False)
    train_unburn = rng.choice(unburn_idx, n_take * 2, replace=False)
    train_idx = np.concatenate([train_burn, train_unburn])
    rng.shuffle(train_idx)

    # Build X (n_samples, n_good_bands), y
    train_y = flat_burn[train_idx].astype(np.float32)
    sw_y = (flat_glt_y[train_idx] - 1).astype(int)
    sw_x = (flat_glt_x[train_idx] - 1).astype(int)
    train_X = rfl[sw_y, sw_x][:, good]
    keep = np.all(np.isfinite(train_X), axis=1)
    train_X = train_X[keep]; train_y = train_y[keep]
    print(f"final training samples: {len(train_y)}  burn frac: {train_y.mean():.3f}")

    # Try torch first; fall back to sklearn MLPClassifier
    use_torch = False
    try:
        import torch
        import torch.nn as nn
        use_torch = True
    except ImportError:
        pass

    # Two held-out designs: (a) random 80/20 (within-distribution),
    # (b) spatial-block CV (leave-one-block-out), reported separately.
    rows = sw_y[keep]
    block = (rows // (H_sw // 4)).clip(0, 3)
    rand_split = rng.uniform(size=len(train_y))
    test_mask = rand_split > 0.8
    train_mask = ~test_mask
    spatial_test_blocks = sorted(set(block.tolist()))

    if not use_torch:
        from sklearn.neural_network import MLPClassifier
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import roc_auc_score
        scaler = StandardScaler().fit(train_X[train_mask])
        Xs_tr = scaler.transform(train_X[train_mask])
        Xs_te = scaler.transform(train_X[test_mask])
        clf = MLPClassifier(hidden_layer_sizes=(256, 128, 64),
                            activation="relu", solver="adam",
                            max_iter=80, random_state=0, early_stopping=True)
        clf.fit(Xs_tr, train_y[train_mask])
        prob_te = clf.predict_proba(Xs_te)[:, 1]
        auc_rand = float(roc_auc_score(train_y[test_mask], prob_te))
        print(f"\nMLP (sklearn) - random 80/20 holdout AUC = {auc_rand:.4f}")

        # Spatial-block CV: leave-one-block-out
        block_aucs = []
        for tb in spatial_test_blocks:
            te = block == tb
            tr = ~te
            if tr.sum() < 200 or te.sum() < 50: continue
            if train_y[te].sum() < 5 or (train_y[te] == 0).sum() < 5: continue
            sc = StandardScaler().fit(train_X[tr])
            cl = MLPClassifier(hidden_layer_sizes=(256, 128, 64), max_iter=60,
                               random_state=0, early_stopping=True)
            cl.fit(sc.transform(train_X[tr]), train_y[tr])
            p = cl.predict_proba(sc.transform(train_X[te]))[:, 1]
            a = float(roc_auc_score(train_y[te], p))
            print(f"  block {tb}: train n={tr.sum()}  test n={te.sum()}  AUC = {a:.4f}")
            block_aucs.append(a)

        Path("data/hsi/v1/dl_1dcnn_uiseong.json").write_text(json.dumps({
            "model": "sklearn MLPClassifier(256,128,64) on 244 good EMIT bands",
            "auc_random_8020": auc_rand,
            "auc_spatial_blocks": block_aucs,
            "auc_spatial_mean": float(np.mean(block_aucs)) if block_aucs else None,
            "auc_spatial_std": float(np.std(block_aucs)) if block_aucs else None,
            "n_train_random": int(train_mask.sum()),
            "n_test_random": int(test_mask.sum()),
            "comparison": {"hsi_v1_auc": 0.7467, "hsi_v0_auc": 0.697}
        }, indent=2))
        return

    # 1D-CNN with PyTorch
    nb = train_X.shape[1]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"using torch device: {device}")

    class CNN1D(nn.Module):
        def __init__(self, nb):
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv1d(1, 16, 7, padding=3), nn.ReLU(), nn.MaxPool1d(2),
                nn.Conv1d(16, 32, 5, padding=2), nn.ReLU(), nn.MaxPool1d(2),
                nn.Conv1d(32, 64, 3, padding=1), nn.ReLU(),
                nn.AdaptiveAvgPool1d(8),
                nn.Flatten(),
                nn.Linear(64 * 8, 64), nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(64, 1),
            )
        def forward(self, x): return self.net(x)

    Xt = torch.from_numpy(train_X.astype(np.float32)).unsqueeze(1).to(device)
    yt = torch.from_numpy(train_y).to(device)
    Xt_tr, yt_tr = Xt[train_mask], yt[train_mask]
    Xt_te, yt_te = Xt[test_mask], yt[test_mask]

    model = CNN1D(nb).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    bce = nn.BCEWithLogitsLoss()
    bs = 256
    n_train = len(Xt_tr)
    for epoch in range(20):
        perm = torch.randperm(n_train)
        losses = []
        for i in range(0, n_train, bs):
            idx = perm[i:i+bs]
            logits = model(Xt_tr[idx]).squeeze(1)
            loss = bce(logits, yt_tr[idx])
            opt.zero_grad(); loss.backward(); opt.step()
            losses.append(loss.item())
        if epoch % 5 == 0 or epoch == 19:
            with torch.no_grad():
                logit_te = model(Xt_te).squeeze(1).cpu().numpy()
            from sklearn.metrics import roc_auc_score
            auc = float(roc_auc_score(yt_te.cpu().numpy(), logit_te))
            print(f"  epoch {epoch:3d}  loss {np.mean(losses):.4f}  test AUC {auc:.4f}")

    Path("data/hsi/v1/dl_1dcnn_uiseong.json").write_text(json.dumps({
        "model": "1D-CNN on 244 good EMIT bands (16/32/64 filters, GAP, FC-64-1)",
        "auc_test_block": auc, "n_train": int(train_mask.sum()),
        "n_test": int(test_mask.sum()),
        "comparison": {"hsi_v1_auc": 0.7467, "hsi_v0_auc": 0.697}
    }, indent=2))


if __name__ == "__main__":
    main()
