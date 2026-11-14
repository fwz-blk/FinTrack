from flask import Response, render_template, request, session

from ..auth.decorators import login_required
from ..services.reports import (
    build_report,
    parse_report_date,
    report_csv,
    report_pdf,
)


def register(app):
    @app.get("/reports")
    @login_required
    def reports():
        report = build_report(
            session["user_id"],
            request.args.get("filter", "current_month"),
            parse_report_date(request.args.get("start")),
            parse_report_date(request.args.get("end")),
        )
        return render_template("reports.html", **report)

    @app.get("/reports/print")
    @login_required
    def reports_print():
        report = build_report(
            session["user_id"],
            request.args.get("filter", "current_month"),
            parse_report_date(request.args.get("start")),
            parse_report_date(request.args.get("end")),
        )
        return render_template("reports_print.html", **report)

    @app.get("/reports/export.csv")
    @login_required
    def reports_csv():
        report = build_report(
            session["user_id"],
            request.args.get("filter", "current_month"),
            parse_report_date(request.args.get("start")),
            parse_report_date(request.args.get("end")),
        )
        return Response(
            report_csv(report),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=fintrack-report.csv"},
        )

    @app.get("/reports/export.pdf")
    @login_required
    def reports_pdf():
        report = build_report(
            session["user_id"],
            request.args.get("filter", "current_month"),
            parse_report_date(request.args.get("start")),
            parse_report_date(request.args.get("end")),
        )
        return Response(
            report_pdf(report),
            mimetype="application/pdf",
            headers={"Content-Disposition": "attachment; filename=fintrack-report.pdf"},
        )
