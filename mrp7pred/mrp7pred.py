"""
MRP7Pred class
"""

import pickle
import pandas as pd
from pandas import DataFrame
from numpy import ndarray
from sklearn.pipeline import Pipeline
from typing import Optional, Union, Dict, Any, List, Callable

# from mrp7pred.featurization import featurize
from mrp7pred.feats.gen_all_features import featurize
from mrp7pred.train import run
from mrp7pred.utils import (
    DATA,
    MODEL_DIR,
    get_current_time,
    DummyClassifier,
    DummyScaler,
    NoScaler,
    ensure_folder,
)

# import warnings

# warnings.filterwarnings("ignore")


class MRP7Pred(object):
    def __init__(
        self,
        clf_dir: Optional[str] = None,
        train_new: bool = False,
    ) -> None:
        """
        Parameters
        --------
        clf_dir: str
        train_new: bool
            Set train_new as True if want to train new model
        """
        self.train_new = train_new
        if not train_new:
            if clf_dir is None:
                raise ValueError("'clf_dir' cannot be None if not training new model.")
            print("Loading trained model ... ", end="", flush=True)
            with open(clf_dir, "rb") as ci:
                self.clf_best = pickle.load(ci)
            print("Done!")

    def auto_train_test(
        self,
        df: DataFrame,
        grid: Dict[str, Union[List[Any], ndarray]],
        time_limit: int,
        cv_n_splits: int = 5,
        verbose: int = 10,
        n_jobs: int = -1,
        train_test_ratio: float = 0.8,
        scoring: Union[str, callable] = "accuracy",
        featurized: bool = False,
        model_dir: Optional[str] = None,
        feats_dir: Optional[str] = None,
        random_state: Optional[str] = None,
        prefix: Optional[str] = None,
    ):
        """
        Featurize and train models

        Parameters
        --------
        df: pandas.DataFrame
            A dataframe containing all data.
            Must have columns: "name", "smiles", "label"
        train_test_ratio: float
            The ratio of training data : test data
        featurized: bool
            True if data has been featurized else False
        grid: Dict
            Grid for GridSearchCV(), defined in MRP7Pred.grid
        cv_n_splits: int
            number of splits. default cv StratifiedKFold()
        verbose: int
            verbose indicates how much information is printed
        n_jobs: int
            number of processes.
        train_test_ratio: float
            ratio of train-test data
        scoring: Union[str, callable]
            scoring function, default accuracy
        featurized: bool
            true if df is featurized
        model_dir: Optional[str]
            directory where trained model is saved
        feats_dir: Optional[str]
            directory where featurized data is saved
        random_state: Optional[int]
            random seed for repeat
        prefix: Optional[str]
            prefix of output data file

        Returns
        --------
        self.clf_best: sklearn.pipeline.Pipeline
            Best model
        """
        if not self.train_new:
            raise ValueError(
                "MRP7Pred was instantiated with train_new=False, execute training process will overwrite the previous model!"
            )

        self.clf_best = run(
            df,
            grid=grid,
            cv_n_splits=cv_n_splits,
            ratio=train_test_ratio,
            featurized=featurized,
            verbose=verbose,
            n_jobs=n_jobs,
            model_dir=model_dir,
            feats_dir=feats_dir,
            random_state=random_state,
            prefix=prefix,
            time_limit=time_limit,
        )

    def predict(
        self,
        compound_csv_dir: Optional[str] = None,
        compound_df: Optional[DataFrame] = None,
        featurized_df: Optional[DataFrame] = None,
        prefix: Optional[str] = None,
        out_dir: Optional[str] = None,
    ) -> DataFrame:
        """
        Featurize data and make predictions

        Parameters
        --------
        compound_csv_dir: Optional[str]
            The directory of unknown compound data
            with columns "name" and "smiles"
        selected_features: Optional[ndarray]
            index of selected features
        featurized_df: Optional[DataFrame]
            Featurized data in dataframe
        prefix: Optional[str]
            Prediction results output filename prefix

        Returns
        --------
        pred: ndarray
        """
        if compound_csv_dir is None and compound_df is None:
            raise ValueError(
                "Must pass either the path to csv file containing compound smiles to 'compound_csv_dir' or a dataframe with columns 'name' and 'smiles' to 'compound_df"
            )

        if featurized_df is None:
            self.featurized_df = None
            if compound_csv_dir:
                df = pd.read_csv(compound_csv_dir)
            elif compound_df is not None:
                df = compound_df

        else:
            if (
                "name" not in featurized_df.columns
                or "smiles" not in featurized_df.columns
            ):
                raise ValueError(
                    'The input csv should have these two columns: ["name", "smiles"]'
                )

            # only extract name and smiles
            df = featurized_df[["name", "smiles"]]
            df_feat = featurized_df.drop(["name", "smiles"], axis=1)

        if featurized_df is None:
            print("Generating features ... ")
            # df_feats should be purely numeric
            _, df = featurize(
                df, remove_similar=False, remove_zeros=False, prefix=prefix
            )
            self.featurized_df = df
            df_feat = df.drop(["name", "smiles"], axis=1)
            # print("Done!")
        print("Start predicting ... ", end="", flush=True)
        preds = self.clf_best.predict(df_feat)
        scores = [score[1] for score in self.clf_best.predict_proba(df_feat)]
        print("Done!")

        df_out = pd.DataFrame(columns=["name", "smiles", "pred", "score"])
        df_out["name"] = df["name"]
        df_out["smiles"] = df["smiles"]
        df_out["pred"] = preds
        df_out["score"] = scores

        if out_dir is not None:
            print("Writing output ... ", end="", flush=True)
            ensure_folder(out_dir)
            df_out.to_csv(f"{out_dir}/{prefix}predicted_{get_current_time()}.csv")
            print(
                f"Done! Results saved to: {out_dir}/{prefix}predicted_{get_current_time()}.csv"
            )
        return df_out


def main() -> None:
    m7p = MRP7Pred()
    m7p.predict(f"{DATA}/unknown.csv")


if __name__ == "__main__":
    main()
