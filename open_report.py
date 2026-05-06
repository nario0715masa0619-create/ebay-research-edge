import webbrowser
from pathlib import Path

# 最新のレポートファイルを取得
report_dir = Path("data/reports")
report_files = sorted(report_dir.glob("research_report_*.html"), reverse=True)

if report_files:
    latest_report = report_files[0]
    webbrowser.open(latest_report.absolute().as_uri())
    print(f"✅ レポートを開きました: {latest_report}")
else:
    print("❌ レポートファイルが見つかりません")
