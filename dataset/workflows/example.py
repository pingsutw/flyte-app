import typing

import numpy as np
import pandas as pd
import pyarrow as pa

from flytekit import kwtypes, task, workflow
from flytekit.types.structured.structured_dataset import (
    FLYTE_DATASET_TRANSFORMER,
    DatasetDecodingHandler,
    DatasetEncodingHandler,
    DatasetFormat,
    StructuredDataset,
)

BQ_PATH = "bq://photo-313016:flyte.new_table3"

# https://github.com/flyteorg/flyte/issues/523
# We should also support map and list in schema column
my_cols = kwtypes(w=typing.Dict[str, typing.Dict[str, int]], x=typing.List[typing.List[int]], y=int, z=str)


@task
def t1(dataframe: pd.DataFrame) -> StructuredDataset[my_cols]:
    # S3 (parquet) -> Pandas -> S3 (parquet) default behaviour
    return dataframe


@task
def t1a(dataframe: pd.DataFrame) -> StructuredDataset[my_cols]:
    # S3 (parquet) -> Pandas -> S3 (parquet) default behaviour
    return StructuredDataset(dataframe=dataframe)


@task
def t2(dataframe: pd.DataFrame) -> pd.DataFrame:
    # S3 (parquet) -> Pandas -> S3 (parquet)
    return dataframe


@task
def t3(dataset: StructuredDataset[my_cols]) -> StructuredDataset[my_cols]:
    # s3 (parquet) -> pandas -> s3 (parquet)
    print("Pandas dataframe")
    print(dataset.open_as(pd.DataFrame))
    # In the example, we download dataset when we open it.
    # Here we won't upload anything, since we're returning just the input object.
    return dataset


@task
def t3a(dataset: StructuredDataset[my_cols]) -> StructuredDataset[my_cols]:
    # This task will not do anything - no uploading, no downloading
    return dataset


@task
def t4(dataset: StructuredDataset[my_cols]) -> pd.DataFrame:
    # s3 (parquet) -> pandas -> s3 (parquet)
    return dataset.open_as(pd.DataFrame)


@task
def t5(dataframe: pd.DataFrame) -> StructuredDataset[my_cols]:
    # s3 (parquet) -> pandas -> bq
    return StructuredDataset(dataframe=dataframe, remote_path=BQ_PATH, file_format=DatasetFormat.BIGQUERY)


@task
def t6(dataset: StructuredDataset[my_cols]) -> pd.DataFrame:
    # bq -> pandas -> s3 (parquet)
    df = dataset.open_as(pd.DataFrame)
    return df


@task
def t7(df1: pd.DataFrame, df2: pd.DataFrame) -> (StructuredDataset[my_cols], StructuredDataset[my_cols]):
    # df1: pandas -> bq
    # df2: pandas -> s3 (parquet)
    return StructuredDataset(dataframe=df1, remote_path=BQ_PATH, file_format=DatasetFormat.BIGQUERY), df2


@task
def t8(dataframe: pa.Table) -> StructuredDataset[my_cols]:
    # Arrow table -> s3 (parquet)
    print("Arrow table")
    print(dataframe.columns)
    return StructuredDataset(dataframe=dataframe)


@task
def t8a(dataframe: pa.Table) -> pa.Table:
    # Arrow table -> s3 (parquet)
    print(dataframe.columns)
    return dataframe


class NumpyEncodingHandlers(DatasetEncodingHandler):
    def encode(self, dataframe: np.ndarray, name: typing.Optional[typing.List[str]] = None):
        if name is None:
            name = ["col" + str(i) for i in range(len(dataframe))]
        return pa.Table.from_arrays(dataframe, name)


class NumpyDecodingHandlers(DatasetDecodingHandler):
    def decode(self, table: pa.Table):
        return table.to_pandas().to_numpy()


FLYTE_DATASET_TRANSFORMER.register_handler(np.ndarray, pa.Table, NumpyEncodingHandlers())
FLYTE_DATASET_TRANSFORMER.register_handler(pa.Table, np.ndarray, NumpyDecodingHandlers())


@task
def t9(dataframe: np.ndarray) -> StructuredDataset[my_cols]:
    # numpy -> Arrow table -> s3 (parquet)
    return StructuredDataset(dataframe=dataframe)


@task
def t10(dataset: StructuredDataset[my_cols]) -> np.ndarray:
    # s3 (parquet) -> Arrow table -> numpy
    np_array = dataset.open_as(np.ndarray)
    return np_array


# We see numpy as custom dataframe here
# we didn't implement a handler to R/W bigquery, but we still can R/W bigquery
@task
def t11(
    dataframe: np.ndarray,
) -> StructuredDataset[my_cols]:
    # numpy -> Arrow table -> bq
    return StructuredDataset(
        dataframe=dataframe, remote_path="bq://photo-313016:flyte.new_table5", file_format=DatasetFormat.BIGQUERY
    )


@task
def generate_pandas() -> pd.DataFrame:
    return pd.DataFrame({"Name": ["Tom", "Joseph"], "Age": [20, 22]})


@task
def generate_numpy() -> np.ndarray:
    return np.array([[1, 2], [4, 5]])


@task
def generate_arrow() -> pa.Table:
    df = pd.DataFrame({"Name": ["Tom", "Joseph"], "Age": [20, 22]})
    return pa.Table.from_pandas(df)


@workflow
def wf():
    df = generate_pandas()
    np_array = generate_numpy()
    table = generate_arrow()
    t1(dataframe=df)
    t1a(dataframe=df)
    t2(dataframe=df)
    t5(dataframe=df)
    t7(df1=df, df2=df)
    t8(dataframe=table)
    t8a(dataframe=table)
    t9(dataframe=np_array)
    t11(dataframe=np_array)


if __name__ == "__main__":
    wf()
