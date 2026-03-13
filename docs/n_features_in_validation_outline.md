# Outline: `n_features_in_` / `validate_data` for check_estimator

Sklearn’s `check_estimator` (1.6+) requires that:

1. The estimator sets `n_features_in_` in `fit()` (Earth already does this at line 641).
2. Methods that take `X` (e.g. `predict`, `transform`) validate that `X.shape[1]` matches `n_features_in_` and raise a clear error when it does not.

Earth currently fails the second part: the check in `_scrub_x()` uses `self.basis_.num_variables` and the message `'Wrong number of columns in X. Reshape your data.'`, which the checker does not treat as an `n_features_in_`-based validation.

---

## Option A (recommended): Use `validate_data` in predict/transform paths

**1. Imports**

- Add `validate_data` to the validation imports (and keep compatibility with sklearn &lt; 1.6):

```python
from sklearn.utils.validation import (
    assert_all_finite, check_is_fitted, check_X_y, check_array
)
try:
    from sklearn.utils.validation import validate_data
except ImportError:
    validate_data = None
```

**2. `predict(self, X, missing=None, skip_scrub=False)`**

- At the top of `predict()`, when `not skip_scrub`, run the standard feature-count check **before** calling `_scrub_x`:

  - **If `validate_data` is available (1.6+):**  
    Call `validate_data(self, X, reset=False)` and use the returned array(s).  
    This performs the `n_features_in_` check and gives the error message the checker expects.

  - **If `validate_data` is not available:**  
    After converting `X` to an array (e.g. with `check_array` or a minimal conversion), check  
    `getattr(self, 'n_features_in_', None) is not None and X.shape[1] != self.n_features_in_`  
    and raise `ValueError` with a message that explicitly mentions the number of features / `n_features_in_` (e.g. “X has N features; estimator expects M features from fit.”).

- Then call `_scrub_x(X, missing)` (and the rest of the method) as today.  
  So the flow is: “validate feature count (via `validate_data` or manual check) → then _scrub_x”.

**3. Other methods that take `X`**

- Apply the same pattern anywhere else that uses `X` and should enforce “same number of features as at fit”:

  - **`predict_deriv(self, X, ...)`**  
    Same as `predict`: run `validate_data(self, X, reset=False)` (or the manual `n_features_in_` check) before `_scrub_x` when you are not skipping scrub.

  - **`transform(self, X, ...)`**  
    Same idea: validate feature count first, then existing logic.

  - **`score(self, X, y, ...)`**  
    If it uses `X`, validate `X` the same way (and `y` if needed).

- For any internal path that uses `skip_scrub=True`, the caller is responsible for having already validated `X` (e.g. after a single validation in `predict`/`transform`), so no extra check is needed there if the public entry point already validated.

**4. `fit(self, X, y=None, ...)`**

- You can either:

  - **Minimal change:**  
    Leave `fit()` as is. It already sets `self.n_features_in_ = X.shape[1]` after `_scrub`.  
    No need to call `validate_data` in `fit` unless you want to centralize all validation there (see below).

  - **Optional centralization:**  
    At the very start of `fit()`, call  
    `X, y = validate_data(self, X, y, multi_output=True, reset=True, **_CHECK_FINITE_KW)`  
    (when `validate_data` is available), then pass the returned `X, y` into the rest of `fit` (including `_scrub`).  
    This sets `n_features_in_` (and optionally `feature_names_in_`) in one place. You would then keep setting `self.n_features_in_ = X.shape[1]` only when `validate_data` is not used (sklearn &lt; 1.6), so the attribute is always set.

**5. `_scrub_x`**

- Leave the existing “wrong number of columns” check in place as a fallback (it uses `self.basis_.num_variables` and will only run when already fitted).  
  Once the feature count is validated at the entry points (predict/transform/…) using `n_features_in_` (or `validate_data`), this becomes redundant but harmless and can help with non-sklearn call paths.

- Optionally, you can make the error message in `_scrub_x` mention `n_features_in_` when present, e.g.  
  “X has {} features; estimator expects {} features (n_features_in_). Reshape your data.”  
  so that any code path that only goes through `_scrub_x` still gives a message that references the attribute.

---

## Option B: Manual `n_features_in_` check only (no `validate_data`)

If you prefer not to depend on `validate_data` at all:

**1. `_scrub_x`**

- After converting `X` to a 2D array (e.g. after `check_array` and before the `basis_` check), add:

  - If `getattr(self, 'n_features_in_', None) is not None` and `X.shape[1] != self.n_features_in_`:  
    raise  
    `ValueError(  
        "X has {} features, but {} is expecting {} features as input."  
        .format(X.shape[1], self.__class__.__name__, self.n_features_in_)  
    )`  
    (or the exact message format sklearn uses; the important part is that the check is clearly based on `n_features_in_`.)

- Keep or remove the later `basis_.num_variables` check; keeping it is redundant but safe.

**2. `fit`**

- No change needed; `n_features_in_` is already set after `_scrub`.

**3. `predict` / `predict_deriv` / `transform` / `score`**

- No change needed if they all go through `_scrub_x` for `X`; the new check in `_scrub_x` will run for all of them.

**4. Backward compatibility**

- Works on any sklearn version that has `n_features_in_` convention; no need for `validate_data` (1.6+).

---

## Recommendation

- **Option A** matches the checker’s suggestion and uses the public API (`validate_data`), which may be more robust to future changes in error messages and tags.  
- **Option B** is a small, localized change (one check in `_scrub_x`) and avoids a dependency on `validate_data`; it should still satisfy the “consistency between input number of features and `n_features_in_`” requirement.

Implement either Option A (validate_data at entry points + optional fit centralization) or Option B (single check in `_scrub_x`), then re-run:

```bash
PYTHONPATH=build/lib.linux-x86_64-cpython-313 .venv-py313/bin/python -m pytest pyearth/test/test_earth.py::test_check_estimator -v
```

to confirm `check_estimator` passes.
