import argparse
import os
import azureml.core
from azureml.core import Run
from sklearn.model_selection import train_test_split

print("Split the data into train and test")
# Load dataset from context
run = Run.get_context()
input_data_train = run.input_datasets['input_dataset']
input_df_train = input_data_train.to_pandas_dataframe()

parser = argparse.ArgumentParser("split")
parser.add_argument("--output_split_train", type=str, help="output split train data")
parser.add_argument("--output_split_test", type=str, help="output split test data")

args = parser.parse_args()

print("Argument 1(output training data split path): %s" % args.output_split_train)
print("Argument 2(output test data split path): %s" % args.output_split_test)

def split_data(data_df):
    """Split a dataframe into training and test datasets"""
    train_df, test_df = \
        train_test_split(data_df, test_size=0.2, 
                         random_state=0)

    return (train_df, test_df)

train_df, test_df = split_data(input_df_train)

def write_output(df, path):
    '''
    write datasets to temporary proccessed.parquet files for reading from next pipeline
    '''
    os.makedirs(path, exist_ok=True)
    print("%s created" % path)
    df.to_parquet(path + "/processed.parquet")

if not (args.output_split_train is None and
        args.output_split_test is None):
    write_output(train_df, args.output_split_train)
    write_output(test_df, args.output_split_test)