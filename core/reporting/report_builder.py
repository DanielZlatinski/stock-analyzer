import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from core.visualization.report_charts import (
    fundamentals_chart,
    peers_chart,
    price_chart,
    relative_chart,
    sentiment_chart,
)


def build_report(snapshot, analysis, benchmark_prices, output_dir, export_format="html"):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"{snapshot.context.ticker}_{timestamp}.{export_format}"
    filepath = os.path.join(output_dir, filename)

    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "templates"))
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")

    context = {
        "snapshot": snapshot,
        "analysis": analysis,
        "generated_at": datetime.utcnow().isoformat(),
        "charts": {
            "price": price_chart(snapshot.price_history),
            "relative": relative_chart(snapshot.price_history, benchmark_prices),
            "fundamentals": fundamentals_chart(analysis.fundamentals.time_series),
            "peers": peers_chart(analysis.peers.peer_metrics),
            "sentiment": sentiment_chart(snapshot.news),
        },
    }

    html = template.render(**context)
    if export_format == "html":
        with open(filepath, "w", encoding="utf-8") as handle:
            handle.write(html)
        return filepath

    if export_format == "pdf":
        try:
            from weasyprint import HTML
        except ImportError as exc:
            raise RuntimeError("WeasyPrint not installed; cannot export PDF.") from exc
        HTML(string=html, base_url=template_dir).write_pdf(filepath)
        return filepath

    raise ValueError(f"Unsupported export format: {export_format}")
