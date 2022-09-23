
class BaseEstimator():
    """
    Estimator base class
    """


    def get_params(self, deep=True) -> dict:
        """
        Get parameters for this estimator.

        Args:
            deep: If True, will return the parameters for this estimator and
                contained subobjects that are estimators.

        Returns: Parameter names mapped to their values.

        """
        pass

    def set_params(self, **params):
        """
        Set the parameters of this estimator.
        The method works on simple estimators as well as on nested objects
        (such as :class:`~sklearn.pipeline.Pipeline`). The latter have
        parameters of the form ``<component>__<parameter>`` so that it's
        possible to update each component of a nested object.

        Args:
            **params: Estimator parameters.

        Returns: Estimator instance.

        """
        pass

    def fit_transform(self, X, y=None, **fit_params):
        """
        Fit to data, then transform it.
        Fits transformer to `X` and `y` with optional parameters `fit_params`
        and returns a transformed version of `X`.

        Args:
            X: array-like of shape (n_samples, n_features)
                Input samples.
            y: array-like of shape (n_samples,) or (n_samples, n_outputs), \
                default=None
                Target values (None for unsupervised transformations).
            **fit_params: Additional fit parameters.

        Returns: Transformed array.

        """
        pass