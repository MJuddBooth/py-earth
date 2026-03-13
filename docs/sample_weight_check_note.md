# Note: sklearn `check_sample_weight_equivalence_on_dense_data`

## What the check does

`check_sample_weight_equivalence_on_dense_data` (in `sklearn.utils.estimator_checks`) verifies that **integer** sample weights are equivalent to **replicating** those samples:

- **Weighted fit:** `estimator.fit(X, y, sample_weight=sw)` with `sw` integer array
- **Repeated fit:** `estimator.fit(X_repeated, y_repeated, sample_weight=None)` where  
  `X_repeated = X.repeat(sw, axis=0)`, `y_repeated = y.repeat(sw)`

The check then compares `estimator_repeated.predict(X)` and `estimator_weighted.predict(X)` and expects them to be (numerically) the same.

So: fitting with weights `[2,0,1,3,...]` must be equivalent to fitting on data where row 0 appears twice, row 1 is dropped, row 2 once, row 3 three times, etc.

## Why Earth fails it

Earth uses `sample_weight` in three places:

1. **Forward pass** (`_forward.pyx`) – weighted RSS/GCV for term selection  
2. **Pruning pass** (`_pruning.pyx`) – weighted GCV for pruning  
3. **Linear fit** (`linear_fit` in `earth.py`) – weighted least squares for coefficients  

The **linear fit** is standard WLS and is consistent with “replicate rows and do OLS”: same normal equations. So that part is fine.

The **forward and pruning** passes use **GCV** with a **data size** term. In the code:

- `gcv_adjust(basis_size, data_size, penalty)` in `_util.pyx` uses `data_size` in the denominator:  
  `(1 - effective_parameters / data_size)^2`.
- In `_forward.pyx`, `data_size` is always `self.m` (number of rows), e.g.  
  `gcv_adjust(k + 1, self.m, self.penalty)` (and there is even a TODO: “Shouldn’t there be weights here?”).

So:

- **Repeated fit:** `m_repeated = sum(sw)` is large → GCV uses a larger `data_size` → different penalty → different term choices.
- **Weighted fit:** `m = 15` → GCV uses 15 as `data_size` → different penalty → different basis selection.

Because the **model structure** (which terms are in the basis) is chosen differently, the two estimators are not equivalent, and `predict(X)` differs.

## What would be required to pass the check

For integer weights, “replicate then fit” is equivalent to “fit with weights” only if every place that uses **sample count** uses the **effective sample count** under weighting.

- **Effective N** for weighted problems is usually taken as **sum(weights)** (or, for squared weights in some GCV formulations, a consistent choice).
- So in the forward and pruning passes, instead of using `self.m` (number of rows) in `gcv_adjust(..., data_size, ...)`, use an **effective data size** when weights are present, e.g.  
  `data_size = np.sum(self.sample_weight ** 2)` or `np.sum(self.sample_weight)` (depending on how MSE is defined with weights elsewhere in the same code).

Concretely:

1. **Forward pass (`_forward.pyx`)**  
   - When `sample_weight` is not uniform, compute something like  
     `effective_m = np.sum(self.sample_weight ** 2)` (or the same convention used for weighted MSE in that file).  
   - Pass `effective_m` into `gcv_adjust(..., data_size, ...)` instead of `self.m` (and use it anywhere else that currently uses `self.m` for “number of observations” in the GCV/RSS logic).  
   - Ensure the same convention (sum of weights vs sum of squared weights) is used for both MSE and GCV so that “replicate rows and run unweighted” matches “single row with weight w”.

2. **Pruning pass (`_pruning.pyx`)**  
   - Same idea: use an effective sample size (e.g. `sum(sample_weight)` or `sum(sample_weight**2)`) wherever the current code uses the number of rows for GCV/degrees-of-freedom, so that the pruning criterion matches the “replicated data” scenario.

3. **Documentation / tests**  
   - After the change, add a short note (e.g. in docstring or TESTING.md) that integer sample weights are designed to be equivalent to replicating samples for both structure selection (forward + pruning) and the final linear fit.  
   - Optionally add a small test that fits with weights and with repeated data and compares predictions on the original X (similar to the sklearn check).

## Summary

- **Current behavior:** Earth fails the check because GCV in the forward and pruning passes uses the raw row count `m` instead of an effective sample size, so weighted fit and “replicate then fit” choose different models.
- **Fix:** Use an effective data size (e.g. `sum(weights)` or `sum(weights**2)`) in all GCV/data-size calculations in the forward and pruning passes when sample weights are provided, and keep the linear fit as weighted least squares. Then re-run `check_sample_weight_equivalence_on_dense_data` (e.g. via `test_check_estimator`) to confirm.
