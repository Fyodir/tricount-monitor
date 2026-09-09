import subprocess
import pandas as pd
from pathlib import Path
import datetime
from zoneinfo import ZoneInfo
import sys
from rclone_python import rclone
import os
import plotly_express as px

def get_balance_now(identifier, datetime_now, user_list: list|None = None):
    
    cmd = ["/home/andysmith/.local/bin/uv","run", "/home/andysmith/tricount-extractor-pi/tricount_extractor/main.py", "-id", identifier, "-f", "/tmp"]
    
    result = subprocess.run(cmd, text=True, capture_output=True)
 
    path_xlsx = result.stdout.split(" ")[-1].strip().replace("'","")
    
    df = pd.read_excel(path_xlsx, sheet_name="balances")

    os.remove(path_xlsx)

    df_fmt = df[["member", "balance"]].copy()
    df_fmt["date"] = datetime_now
    df_fmt["balance"] = -df["balance"]
    
    if user_list is not None:
        return df_fmt.query("member in @user_list ")
    
    return df_fmt


def main():
    
    DATETIME_NOW = datetime.datetime.now(tz=ZoneInfo("Australia/Brisbane")).strftime("%y%m%d")
    
    RCLONE_BASE = "gdrive:02_Finance/pi/tricount/"
    DIR_TMP = "/tmp/tricount"
    PLOT_NAME= "tricount_plots.html"

    if len(sys.argv) != 2:
        raise ValueError("extract_balances.py TRICOUNT_ID")

    ID = sys.argv[1]
    
    # Setup Working Dirs
    tmp_dir = Path(DIR_TMP)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    local_dir_csv = tmp_dir / "csv"
    local_dir_csv.mkdir(parents=True, exist_ok=True)

    # Get TODAYS Tricount User Balances
    df_today = get_balance_now(ID, DATETIME_NOW, user_list=["Andy", "Sharelle", "2UP", "Make-up Pot"])
    print(f"Writing debts to csv --> {local_dir_csv}/{DATETIME_NOW}.csv")
    df_today.to_csv(f"{local_dir_csv}/{DATETIME_NOW}.csv", index=False)
    
    # TODO - List contents of Google Drive Tricount daily balances
    # TODO - Check local tmp/csv dir for daily Balance files
    # TODO - Download missing CSV files to tmp/csv directory
    rclone.copy(
        os.path.join(RCLONE_BASE, "csv"),
        local_dir_csv,
        ignore_existing=True
    )
    
    # TODO - Aggregate daily Balance CSV files into a master DF
    df_master = pd.concat([pd.read_csv(f) for f in local_dir_csv.iterdir() if f.name.endswith(".csv")], ignore_index=True)
    df_master["date"] = pd.to_datetime(df_master["date"], format="%y%m%d")
    df_master = df_master.sort_values(["member", "date"]).reset_index(drop=True)
    df_master = df_master.drop_duplicates(subset=["member", "date"], keep="last")

    # TODO - Plot Balance tracker line chart
    fig = px.line(
        df_master,
        x="date",
        y="balance",
        color="member",
        markers=True,
        title="Tricount Debt Balance Vs Time",
    )
    # fig.show()
    
    fig.write_html(
        os.path.join("assets", PLOT_NAME)
    )
    
    # TODO - output chart to Google Drive (Rclone)
    #rclone.copyto(
    #    os.path.join(DIR_TMP, PLOT_NAME),
    #    os.path.join(RCLONE_BASE, PLOT_NAME)
    )
    
    # TODO - Upload todays Tricount Balance CSV to gdrive
    rclone.copy(
        local_dir_csv,
        os.path.join(RCLONE_BASE, "csv"),
        ignore_existing=True
    )    
        
if __name__ == "__main__":
    
    main()
