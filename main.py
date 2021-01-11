import shutil
import os
from io import StringIO

import boto3
import sys
from pdf_to_images import ImageConverter
import pandas as pd


def get_rows_columns_map(table_result, blocks_map):
    rows = {}
    for relationship in table_result["Relationships"]:
        if relationship["Type"] == "CHILD":
            for child_id in relationship["Ids"]:
                cell = blocks_map[child_id]
                if cell["BlockType"] == "CELL":
                    row_index = cell["RowIndex"]
                    col_index = cell["ColumnIndex"]
                    if row_index not in rows:
                        # create new row
                        rows[row_index] = {}

                    # get the text value
                    rows[row_index][col_index] = get_text(cell, blocks_map)
    return rows


def get_text(result, blocks_map):
    text = ""
    if "Relationships" in result:
        for relationship in result["Relationships"]:
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    word = blocks_map[child_id]
                    if word["BlockType"] == "WORD":
                        text += word["Text"] + " "
                    if word["BlockType"] == "SELECTION_ELEMENT":
                        if word["SelectionStatus"] == "SELECTED":
                            text += "X "
    return text


def get_table_csv_results(file_name):
    with open(file_name, "rb") as file:
        img_test = file.read()
        bytes_test = bytearray(img_test)
        print("Image loaded", file_name)

    # process using image bytes
    # get the results
    client = boto3.client("textract")

    response = client.analyze_document(
        Document={"Bytes": bytes_test}, FeatureTypes=["TABLES"]
    )

    blocks = response["Blocks"]

    blocks_map = {}
    table_blocks = []
    for block in blocks:
        blocks_map[block["Id"]] = block
        if block["BlockType"] == "TABLE":
            table_blocks.append(block)

    if len(table_blocks) <= 0:
        return "<b> NO Table FOUND </b>"

    csv = ""
    table = table_blocks[0]
    region = blocks[2]["Text"]
    csv += generate_table_csv(table, blocks_map)
    csv += "\n\n"

    return region, csv


def generate_table_csv(table_result, blocks_map):
    rows = get_rows_columns_map(table_result, blocks_map)
    csv = ""
    for row_index, cols in rows.items():
        if row_index == 1:
            header = "Provider Type, Provider Rating, Infant FT, Infant PT, Toddler FT, Toddler PT, Preschool FT, Preschool PT, School-age FT, School-age PT"
            csv += header
            csv += "\n"
        elif row_index == 17:
            pass
        else:
            for col_index, text in cols.items():
                text = text.replace("$", "").replace("-", "0").replace(" ", "")
                csv += "{}".format(text) + ","
            csv += "\n"

    csv += "\n\n\n"
    return csv


def write_csv(file_name):
    region, table_csv = get_table_csv_results(file_name)
    output_file = f"output/{region}.csv"
    df = pd.read_csv(StringIO(table_csv), index_col=False)
    df.to_csv(output_file)
    print("Output csv: ", output_file)


def recreate_dir(name):
    if os.path.exists(name):
        shutil.rmtree(name)
    os.makedirs(name)


if __name__ == "__main__":
    file_name = sys.argv[1]
    recreate_dir("tmp")
    recreate_dir("output")
    ImageConverter.pdftopil(file_name)  # Converts PDF to individual JPEGs
    for subdir, dirs, files in os.walk("tmp"):
        files = sorted([f for f in files if not f[0] == "."])
        for i, file in enumerate(files):
            file_path = os.path.join(subdir, file)
            write_csv(file_path)
